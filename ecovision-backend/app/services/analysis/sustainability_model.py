# ============================================================
# optimizer.py
# Material Optimization Engine
# User selection BEFORE vs AI recommendation AFTER
# ============================================================

import json
import itertools
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

SURFACES = {
    "wall": 0.50,
    "floor": 0.35,
    "ceiling": 0.15
}

SURFACE_CATEGORY_RULES = {
    "wall": ["brick", "concrete_block", "stone"],
    "floor": ["concrete", "stone"],
    "ceiling": ["insulation", "concrete"]
}

TOP_K_PER_SURFACE = 15

# Recommendations must have carbon at or below user's baseline with some tolerance.
CARBON_CEILING_RATIO = 1.15

# Maximum allowed comfort drop relative to the user's baseline.
COMFORT_FLOOR_RATIO = 0.95

# Prefer a realistic improvement band so the optimizer does not always jump
MIN_CARBON_REDUCTION_RATIO = 0.05
TARGET_CARBON_REDUCTION_RATIO = 0.15
MAX_CARBON_REDUCTION_RATIO = 0.30


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize(series):
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series(0.5, index=series.index)

    return (series - min_val) / (max_val - min_val)


def prepare_materials(materials_df):
    materials_df = materials_df.copy()

    materials_df["thermal_mass_norm"] = normalize(
        materials_df["pred_thermal_mass"]
    )

    materials_df["insulation_norm"] = normalize(
        materials_df["pred_insulation_score"]
    )

    materials_df["thermal_comfort_score"] = (
        0.45 * materials_df["thermal_mass_norm"]
        + 0.55 * materials_df["insulation_norm"]
    )

    return materials_df


def get_material_by_id(materials_df, material_id):
    match = materials_df[materials_df["material_id"] == material_id]

    if match.empty:
        raise ValueError(f"Material ID not found: {material_id}")

    return match.iloc[0]


def embodied_carbon(material_row):
    return (
        material_row["density_kg_m3"]
        * material_row["thickness_m"]
        * material_row["pred_carbon_kgCO2_per_kg"]
    )


def thermal_comfort(material_row):
    return material_row["thermal_comfort_score"]


# ============================================================
# BASE MATERIAL + OPTIONAL INSULATION
# ============================================================

def combine_base_with_insulation(base_material, insulation_material=None):
    if insulation_material is None:
        return {
            "name": base_material["name"],
            "material_id": base_material["material_id"],
            "density_kg_m3": base_material["density_kg_m3"],
            "thickness_m": base_material["thickness_m"],
            "pred_carbon_kgCO2_per_kg": base_material["pred_carbon_kgCO2_per_kg"],
            "thermal_comfort_score": base_material["thermal_comfort_score"]
        }

    return {
        "name": f"{base_material['name']} + {insulation_material['name']}",
        "material_id": f"{base_material['material_id']}+{insulation_material['material_id']}",
        "thickness_m": (base_material["thickness_m"] + insulation_material["thickness_m"]),
        "density_kg_m3": (
            (base_material["density_kg_m3"] * base_material["thickness_m"]
             + insulation_material["density_kg_m3"] * insulation_material["thickness_m"])
            / (base_material["thickness_m"] + insulation_material["thickness_m"])
        ),
        "pred_carbon_kgCO2_per_kg": (
            (base_material["pred_carbon_kgCO2_per_kg"] * base_material["thickness_m"]
             + insulation_material["pred_carbon_kgCO2_per_kg"] * insulation_material["thickness_m"])
            / (base_material["thickness_m"] + insulation_material["thickness_m"])
        ),
        "thermal_comfort_score": (
            0.60 * base_material["thermal_comfort_score"]
            + 0.40 * insulation_material["thermal_comfort_score"]
        )
    }


# ============================================================
# USER SELECTION EVALUATION — BEFORE
# ============================================================

def evaluate_user_selection(room, materials_df, user_selection):
    total_carbon = 0.0
    total_comfort = 0.0
    surface_results = {}

    for surface, ratio in SURFACES.items():
        base_id = user_selection[surface]["base_material_id"]
        insulation_id = user_selection[surface].get("insulation_material_id")

        base_material = get_material_by_id(materials_df, base_id)

        insulation_material = None
        if insulation_id is not None and str(insulation_id).upper() not in ("NONE", "NULL", ""):
            insulation_material = get_material_by_id(materials_df, insulation_id)

        combined_material = combine_base_with_insulation(
            base_material,
            insulation_material
        )

        # حساب الكاربون مضروباً في مساحة الغرفة الفصيلية للحصول على أرقام منطقية بالـ kg
        room_area = room.get("area_m2", 1.0)
        surface_carbon = (
            combined_material["density_kg_m3"]
            * combined_material["thickness_m"]
            * combined_material["pred_carbon_kgCO2_per_kg"]
        ) * room_area

        surface_comfort = combined_material["thermal_comfort_score"]

        total_carbon += surface_carbon
        total_comfort += surface_comfort * ratio

        surface_results[surface] = {
            "name": combined_material["name"],
            "material_id": combined_material["material_id"],
            "carbon_kg": round(surface_carbon, 2),
            "comfort": round(surface_comfort, 3)
        }

    return {
        "materials": surface_results,
        "total_carbon": round(total_carbon, 2),
        "avg_comfort": round(total_comfort, 3)
    }


# ============================================================
# CANDIDATE SELECTION
# ============================================================

def get_surface_candidates(materials_df, surface_name, debug=False):
    allowed_categories = SURFACE_CATEGORY_RULES[surface_name]

    subset = materials_df[
        materials_df["category"].isin(allowed_categories)
    ].copy()

    if subset.empty:
        raise ValueError(f"No materials found for surface: {surface_name}")

    subset["material_carbon_score"] = (
        1 - normalize(subset["pred_carbon_kgCO2_per_kg"])
    )

    if surface_name == "wall":
        subset["pre_score"] = (
            0.30 * (subset["material_carbon_score"] ** 2)
            + 0.55 * (subset["thermal_comfort_score"] ** 2)
            + 0.15 * (subset["insulation_norm"] ** 2)
        )
    elif surface_name == "floor":
        subset["pre_score"] = (
            0.40 * (subset["material_carbon_score"] ** 2)
            + 0.50 * (subset["thermal_comfort_score"] ** 2)
            + 0.10 * (subset["insulation_norm"] ** 2)
        )
    elif surface_name == "ceiling":
        subset["pre_score"] = (
            0.20 * (subset["material_carbon_score"] ** 2)
            + 0.40 * (subset["thermal_comfort_score"] ** 2)
            + 0.40 * (subset["insulation_norm"] ** 2)
        )

    subset["category_bonus"] = 0.0
    subset.loc[subset["category"] == "brick", "category_bonus"] = 0.03
    subset.loc[subset["category"] == "insulation", "category_bonus"] = 0.05
    subset["pre_score"] += subset["category_bonus"]

    subset["surface_bonus"] = 0.0
    if surface_name == "wall":
        subset.loc[subset["category"] == "brick", "surface_bonus"] += 0.06
        subset.loc[subset["category"] == "concrete_block", "surface_bonus"] += 0.05
        subset.loc[subset["category"] == "stone", "surface_bonus"] -= 0.03
    elif surface_name == "floor":
        subset.loc[subset["category"] == "concrete", "surface_bonus"] += 0.05
        subset.loc[subset["category"] == "stone", "surface_bonus"] += 0.02
    elif surface_name == "ceiling":
        subset.loc[subset["category"] == "insulation", "surface_bonus"] += 0.08
        subset.loc[subset["category"] == "concrete", "surface_bonus"] += 0.02

    subset["pre_score"] += subset["surface_bonus"]
    subset = subset.sort_values(by="pre_score", ascending=False).head(TOP_K_PER_SURFACE)

    return subset


def get_room_weights(room):
    carbon_weight = 0.50
    comfort_weight = 0.50

    if room.get("is_high_use", False):
        carbon_weight -= 0.10
        comfort_weight += 0.10

    if room.get("solar_rating") == "poor":
        carbon_weight -= 0.05
        comfort_weight += 0.05

    return carbon_weight, comfort_weight


# ============================================================
# AI COMBINATION GENERATION — AFTER
# ============================================================

def generate_room_combinations(room, materials_df, debug=False):
    wall_candidates = get_surface_candidates(materials_df, "wall", debug=debug)
    floor_candidates = get_surface_candidates(materials_df, "floor", debug=debug)
    ceiling_candidates = get_surface_candidates(materials_df, "ceiling", debug=debug)

    wall_records = wall_candidates.to_dict("records")
    floor_records = floor_candidates.to_dict("records")
    ceiling_records = ceiling_candidates.to_dict("records")

    combinations = []
    room_area = room.get("area_m2", 1.0)

    for wall, floor, ceiling in itertools.product(wall_records, floor_records, ceiling_records):
        wall_carbon = embodied_carbon(wall) * room_area
        floor_carbon = embodied_carbon(floor) * room_area
        ceiling_carbon = embodied_carbon(ceiling) * room_area

        total_carbon = wall_carbon + floor_carbon + ceiling_carbon

        wall_comfort = thermal_comfort(wall)
        floor_comfort = thermal_comfort(floor)
        ceiling_comfort = thermal_comfort(ceiling)

        avg_comfort = (
            wall_comfort * SURFACES["wall"]
            + floor_comfort * SURFACES["floor"]
            + ceiling_comfort * SURFACES["ceiling"]
        )

        combinations.append({
            "wall_material": wall["name"],
            "floor_material": floor["name"],
            "ceiling_material": ceiling["name"],
            "wall_id": wall["material_id"],
            "floor_id": floor["material_id"],
            "ceiling_id": ceiling["material_id"],
            "total_carbon": total_carbon,
            "avg_comfort": avg_comfort,
            "wall_carbon": wall_carbon,
            "floor_carbon": floor_carbon,
            "ceiling_carbon": ceiling_carbon,
            "wall_comfort": wall_comfort,
            "floor_comfort": floor_comfort,
            "ceiling_comfort": ceiling_comfort,
        })

    return pd.DataFrame(combinations)


def pareto_filter(combos_df):
    df = combos_df.sort_values(
        by=["total_carbon", "avg_comfort"],
        ascending=[True, False]
    ).copy()

    pareto_rows = []
    best_comfort_so_far = -float("inf")

    for _, row in df.iterrows():
        if row["avg_comfort"] > best_comfort_so_far:
            pareto_rows.append(row)
            best_comfort_so_far = row["avg_comfort"]

    return pd.DataFrame(pareto_rows)


def rank_combinations(combos_df, room):
    combos_df = combos_df.copy()

    combos_df["carbon_score"] = (1 - normalize(combos_df["total_carbon"]))
    combos_df["comfort_score"] = normalize(combos_df["avg_comfort"])

    carbon_weight, comfort_weight = get_room_weights(room)

    combos_df["final_score"] = (
        carbon_weight * combos_df["carbon_score"]
        + comfort_weight * combos_df["comfort_score"]
    )

    combos_df["same_wall_floor"] = (combos_df["wall_material"] == combos_df["floor_material"]).astype(int)
    combos_df["same_wall_ceiling"] = (combos_df["wall_material"] == combos_df["ceiling_material"]).astype(int)
    combos_df["same_floor_ceiling"] = (combos_df["floor_material"] == combos_df["ceiling_material"]).astype(int)

    combos_df["repetition_penalty"] = (
        0.10 * combos_df["same_wall_floor"]
        + 0.03 * combos_df["same_wall_ceiling"]
        + 0.03 * combos_df["same_floor_ceiling"]
    )

    combos_df["final_score"] = combos_df["final_score"] - combos_df["repetition_penalty"]
    return combos_df.sort_values(by="final_score", ascending=False)


def compare_before_after(before, after):
    carbon_saved = before["total_carbon"] - after["total_carbon"]
    carbon_reduction_pct = (carbon_saved / before["total_carbon"] * 100) if before["total_carbon"] > 0 else 0
    comfort_change = after["avg_comfort"] - before["avg_comfort"]

    return {
        "carbon_saved_kg": round(carbon_saved, 2),
        "carbon_reduction_pct": round(carbon_reduction_pct, 2),
        "comfort_change": round(comfort_change, 3),
        "comfort_status": "improved" if comfort_change > 0 else "same" if comfort_change == 0 else "reduced"
    }


# ============================================================
# ROOM-LEVEL OPTIMIZATION WITH USER SELECTION
# ============================================================

def optimize_room_with_user_selection(room, materials_df, user_selection, top_n=3, debug=False):
    before = evaluate_user_selection(room, materials_df, user_selection)
    combos_df = generate_room_combinations(room, materials_df, debug=debug)

    if combos_df.empty:
        return _fallback_room_result(room, before)

    ranked_df = rank_combinations(combos_df, room)

    # تطبيق الفلاتر الذكية (Carbon Ceiling & Comfort Floor)
    carbon_ceiling = before["total_carbon"] * CARBON_CEILING_RATIO
    comfort_floor = before["avg_comfort"] * COMFORT_FLOOR_RATIO

    filtered_df = ranked_df[
        (ranked_df["total_carbon"] <= carbon_ceiling) & 
        (ranked_df["avg_comfort"] >= comfort_floor)
    ].copy()

    # محاولة فلترة النتائج داخل الـ Realistic Improvement Band
    if not filtered_df.empty and before["total_carbon"] > 0:
        filtered_df["carbon_reduction_pct"] = (before["total_carbon"] - filtered_df["total_carbon"]) / before["total_carbon"]
        band_df = filtered_df[
            (filtered_df["carbon_reduction_pct"] >= MIN_CARBON_REDUCTION_RATIO) & 
            (filtered_df["carbon_reduction_pct"] <= MAX_CARBON_REDUCTION_RATIO)
        ].copy()
        
        if not band_df.empty:
            band_df["reduction_distance"] = (band_df["carbon_reduction_pct"] - TARGET_CARBON_REDUCTION_RATIO).abs()
            filtered_df = band_df.sort_values(by=["reduction_distance", "final_score"], ascending=[True, False])

    filtered_df = filtered_df.drop_duplicates(subset=["wall_id", "floor_id", "ceiling_id"], keep="first")
    top_recommendations = filtered_df.head(top_n)

    if top_recommendations.empty:
        return _fallback_room_result(room, before)

    recommendations = []
    for _, row in top_recommendations.iterrows():
        after = {
            "materials": {
                "wall": {"name": row["wall_material"], "material_id": row["wall_id"], "carbon_kg": round(row["wall_carbon"], 2), "comfort": round(row["wall_comfort"], 3)},
                "floor": {"name": row["floor_material"], "material_id": row["floor_id"], "carbon_kg": round(row["floor_carbon"], 2), "comfort": round(row["floor_comfort"], 3)},
                "ceiling": {"name": row["ceiling_material"], "material_id": row["ceiling_id"], "carbon_kg": round(row["ceiling_carbon"], 2), "comfort": round(row["ceiling_comfort"], 3)}
            },
            "total_carbon": round(row["total_carbon"], 2),
            "avg_comfort": round(row["avg_comfort"], 3),
            "final_score": round(row["final_score"], 3)
        }
        recommendations.append({"after": after, "comparison": compare_before_after(before, after)})

    best_rec = recommendations[0]["after"]
    
    return {
        "room": room["name"],
        "area_m2": room["area_m2"],
        "your_selection": {
            "materials": before["materials"],
            "total_carbon_kg": before["total_carbon"],
            "avg_comfort": before["avg_comfort"]
        },
        "recommended_solution": {
            "materials": best_rec["materials"],
            "total_carbon_kg": best_rec["total_carbon"],
            "avg_comfort": best_rec["avg_comfort"]
        },
        "carbon_savings": {
            "saved_kg": round(before["total_carbon"] - best_rec["total_carbon"], 2),
            "reduction_percent": round(((before["total_carbon"] - best_rec["total_carbon"]) / before["total_carbon"] * 100), 2) if before["total_carbon"] > 0 else 0
        },
        "recommendations": recommendations
    }

def _fallback_room_result(room, before):
    return {
        "room": room["name"],
        "area_m2": room["area_m2"],
        "your_selection": {"materials": before["materials"], "total_carbon_kg": before["total_carbon"], "avg_comfort": before["avg_comfort"]},
        "recommended_solution": {"materials": before["materials"], "total_carbon_kg": before["total_carbon"], "avg_comfort": before["avg_comfort"]},
        "carbon_savings": {"saved_kg": 0.0, "reduction_percent": 0.0},
        "recommendations": []
    }


# ============================================================
# BUILDING-LEVEL OPTIMIZATION FUNCTIONS
# ============================================================

def optimize_building_with_user_selections(materials_path, json_path, user_selections_by_room, top_n=3, debug=False):
    materials_df = pd.read_csv(materials_path)
    materials_df = prepare_materials(materials_df)

    with open(json_path, "r") as f:
        building_data = json.load(f)

    room_results = []
    for room in building_data["rooms"]:
        room_name = room["name"]
        if room_name not in user_selections_by_room:
            raise ValueError(f"Missing user material selection for room: {room_name}")

        result = optimize_room_with_user_selection(
            room=room,
            materials_df=materials_df,
            user_selection=user_selections_by_room[room_name],
            top_n=top_n,
            debug=debug
        )
        room_results.append(result)

    return {
        "building_city": building_data.get("city"),
        "climate": building_data.get("climate"),
        "total_floor_area_m2": building_data.get("total_floor_area_m2"),
        "rooms": room_results
    }


def optimize_building_from_ids(material_ids, rooms, top_n=3, debug=False):
    materials_df = load_materials_from_csv()
    if materials_df is None:
        return {"status": "error", "error": "Materials file not found."}

    valid_ids = [m for m in material_ids if m and str(m).upper() not in ("NONE", "NULL", "")]
    if not valid_ids:
        return {"status": "error", "error": "No valid material IDs provided."}

    # FIX 6: التوزيع الصحيح على الأسطح بالترتيب البوزيشنال من الموبايل/الموقع
    wall_base = valid_ids[0]
    floor_base = valid_ids[1] if len(valid_ids) > 1 else valid_ids[0]
    ceiling_base = valid_ids[2] if len(valid_ids) > 2 else valid_ids[0]

    materials_dict = {
        "wall_base": wall_base, "wall_insulation": None,
        "floor_base": floor_base, "floor_insulation": None,
        "roof_base": ceiling_base, "roof_insulation": None
    }
    
    return optimize_building_with_user_materials(materials_dict, rooms, top_n, debug)


def optimize_building_with_user_materials(materials_dict, rooms, top_n=3, debug=False):
    materials_df = load_materials_from_csv()
    if materials_df is None:
        return {"status": "error", "error": "Materials file not found."}

    user_selection = {
        "wall": {"base_material_id": materials_dict.get("wall_base"), "insulation_material_id": materials_dict.get("wall_insulation")},
        "floor": {"base_material_id": materials_dict.get("floor_base"), "insulation_material_id": materials_dict.get("floor_insulation")},
        "ceiling": {"base_material_id": materials_dict.get("roof_base"), "insulation_material_id": materials_dict.get("roof_insulation")}
    }

    room_results = []
    total_carbon_before = 0.0
    total_carbon_after = 0.0

    for room in rooms:
        try:
            result = optimize_room_with_user_selection(room, materials_df, user_selection, top_n, debug)
            room_results.append(result)
            total_carbon_before += result["your_selection"]["total_carbon_kg"]
            total_carbon_after += result["recommended_solution"]["total_carbon_kg"]
        except Exception as e:
            continue

    if not room_results:
        return {"status": "error", "error": "No rooms could be analyzed"}

    total_savings = total_carbon_before - total_carbon_after
    reduction_percent = (total_savings / total_carbon_before * 100) if total_carbon_before > 0 else 0

    return {
        "status": "success",
        "summary": {
            "your_total_carbon": round(total_carbon_before, 2),
            "optimized_total_carbon": round(total_carbon_after, 2),
            "total_savings": round(total_savings, 2),
            "reduction_percent": round(reduction_percent, 2)
        },
        "rooms": room_results
    }


def load_materials_from_csv(csv_path=None):
    if csv_path is None:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "../../../../materials_with_predictions.csv"),
            os.path.join(os.path.dirname(__file__), "../../../materials_with_predictions.csv"),
            "materials_with_predictions.csv",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = os.path.abspath(path)
                break
    try:
        return prepare_materials(pd.read_csv(csv_path)) if csv_path else None
    except:
        return None


# ============================================================
# RUN BUILDING OPTIMIZATION TEST (HARNESS)
# ============================================================

def run_building_optimization_test(materials_path="materials_with_predictions.csv", json_path="rooms1 final (added windows).json", top_n=3, debug=False):
    user_selection_example = {
        "wall": {"base_material_id": "MAT011", "insulation_material_id": None},
        "floor": {"base_material_id": "MAT015", "insulation_material_id": None},
        "ceiling": {"base_material_id": "MAT024", "insulation_material_id": None}
    }

    if not os.path.exists(json_path):
        test_building = {"city": "Cairo", "rooms": [{"name": "Sample Room", "area_m2": 17.9}]}
        user_selections_by_room = {"Sample Room": user_selection_example}
        materials_df = load_materials_from_csv()
        if materials_df is None: return {"status": "error", "error": "CSV missing"}
        
        result = optimize_room_with_user_selection(test_building["rooms"][0], materials_df, user_selection_example, top_n, debug)
        return {"rooms": [result]}
    
    return optimize_building_with_user_selections(materials_path, json_path, {r["name"]: user_selection_example for r in json.load(open(json_path))["rooms"]}, top_n, debug)


if __name__ == "__main__":
    results = run_building_optimization_test()
    if "rooms" in results:
        print("\n" + "=" * 70)
        print("BEFORE VS AFTER OPTIMIZATION RESULTS")
        print("=" * 70)

        for room in results.get("rooms", []):
            print(f"\nROOM: {room['room']}")
            print(f"Area: {room['area_m2']} m²")
            print(f"\nBEFORE — User Selection")
            print(f"Carbon : {room['your_selection']['total_carbon_kg']} kg CO2")
            print(f"Comfort: {room['your_selection']['avg_comfort']} / 1")

            print(f"\nAFTER — AI Recommendations")
            # FIX: قمنا بتدبيس الـ Indentation هنا لكي تظهر كافة تفاصيل الـ Recommendations بشكل منسق
            for i, rec in enumerate(room.get("recommendations", []), start=1):
                after = rec["after"]
                comp = rec["comparison"]
                print(f"\n  Recommendation #{i}")
                print(f"  ---------------------------------------------")
                print(f"    Wall    : {after['materials']['wall']['name']}")
                print(f"    Floor   : {after['materials']['floor']['name']}")
                print(f"    Ceiling : {after['materials']['ceiling']['name']}")
                print(f"    Carbon  : {after['total_carbon']} kg CO2")
                print(f"    Comfort : {after['avg_comfort']} / 1")
                print(f"    Score   : {after['final_score']}")
                print(f"    Comparison:")
                print(f"      Carbon Saved     : {comp['carbon_saved_kg']} kg CO2")
                print(f"      Carbon Reduction : {comp['carbon_reduction_pct']}%")
                print(f"      Comfort Change   : {comp['comfort_change']}")
                print(f"      Comfort Status   : {comp['comfort_status']}")