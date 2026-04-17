# =====================================================================
# PHASE 3 — MULTI-MATERIAL ARCHITECTURAL OPTIMIZER (FINAL VERSION)
# =====================================================================
# =====================================================================
# MATERIAL SUSTAINABILITY — FULL PIPELINE
# Phase 1: Train & save best model
# Phase 2: Load model, score all materials, recommend alternatives
# =====================================================================

# =====================================
# 1. IMPORTS
# =====================================
# import pandas as pd
# import numpy as np
# import joblib
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_absolute_error
# from sklearn.preprocessing import StandardScaler
# from sklearn.linear_model import LinearRegression, Ridge, Lasso
# from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
# from sklearn.tree import DecisionTreeRegressor
# from sklearn.svm import SVR
# from sklearn.neighbors import KNeighborsRegressor

# # =====================================
# # 2. LOAD DATA
# # =====================================
# df = pd.read_excel("/content/drive/MyDrive/Grad Prj/Data.xlsx")
# print("Dataset shape:", df.shape)
# print("Columns:", df.columns.tolist())
# print()

# # =====================================
# # 3. FEATURE ENGINEERING
# # =====================================
# df['conductivity_W_mK'] = df['conductivity_W_mK'].replace(0, 1e-6)
# df['thermal_mass']      = df['density_kg_m3'] * df['specific_heat_J_kgK']
# df['insulation_score']  = df['thickness_m'] / df['conductivity_W_mK']

# # ── FIX 1: Stabilized target ─────────────────────────────────────────
# # Old: 1 / carbon  → explodes when carbon is tiny (e.g. stone ≈ 0.006 → score ≈ 167)
# # New: 1 / (1 + carbon) → always in (0, 1], no outlier scores
# df['sustainability_score'] = 1 / (1 + df['carbon_kgCO2_per_kg'])

# # =====================================
# # 4. ENCODE & BUILD FEATURE MATRIX
# # =====================================
# df_encoded = pd.get_dummies(df, columns=['category', 'roughness'])

# DROP_COLS = ['material_id', 'name', 'carbon_kgCO2_per_kg', 'sustainability_score']
# X = df_encoded.drop(columns=DROP_COLS)
# y = df_encoded['sustainability_score']

# print("Feature matrix shape:", X.shape)
# print("Features:", X.columns.tolist())
# print()

# # =====================================
# # 5. TRAIN / VALIDATION SPLIT
# # =====================================
# X_train, X_val, y_train, y_val = train_test_split(
#     X, y, test_size=0.2, random_state=42
# )

# # ── FIX 3: Scaling for distance/margin-based models ──────────────────
# # Tree models (RF, GB, ET, DT) are scale-invariant → use raw X_train
# # SVR and KNN rely on distances → must be scaled
# scaler = StandardScaler()
# X_train_scaled = scaler.fit_transform(X_train)   # fit only on train
# X_val_scaled   = scaler.transform(X_val)          # transform val with same params

# # =====================================
# # 6. DEFINE MODELS
# # (SVR and KNN flagged so we know to use scaled data)
# # =====================================
# tree_models = {
#     "LinearRegression" : LinearRegression(),
#     "Ridge"            : Ridge(),
#     "Lasso"            : Lasso(),
#     "DecisionTree"     : DecisionTreeRegressor(max_depth=5),
#     "RandomForest"     : RandomForestRegressor(n_estimators=100, random_state=42),
#     "ExtraTrees"       : ExtraTreesRegressor(n_estimators=100, random_state=42),
#     "GradientBoosting" : GradientBoostingRegressor(random_state=42),
# }

# scaled_models = {
#     "SVR" : SVR(),
#     "KNN" : KNeighborsRegressor(n_neighbors=3),
# }

# # =====================================
# # 7. TRAIN + EVALUATE ALL MODELS
# # =====================================
# results        = {}
# trained_models = {}

# print("=" * 50)
# print("Model Performance (MAE — lower is better)")
# print("=" * 50)

# # Tree / linear models — unscaled data
# for name, model in tree_models.items():
#     try:
#         model.fit(X_train, y_train)
#         preds = model.predict(X_val)
#         mae   = mean_absolute_error(y_val, preds)
#         results[name]        = mae
#         trained_models[name] = (model, False)   # False = no scaling needed
#         print(f"  {name:<22} MAE = {mae:.6f}")
#     except Exception as e:
#         print(f"  {name:<22} FAILED: {e}")

# # SVR & KNN — scaled data
# for name, model in scaled_models.items():
#     try:
#         model.fit(X_train_scaled, y_train)
#         preds = model.predict(X_val_scaled)
#         mae   = mean_absolute_error(y_val, preds)
#         results[name]        = mae
#         trained_models[name] = (model, True)    # True = scaling was applied
#         print(f"  {name:<22} MAE = {mae:.6f}  (scaled)")
#     except Exception as e:
#         print(f"  {name:<22} FAILED: {e}")

# if not results:
#     raise RuntimeError("All models failed. Check your feature matrix.")

# # =====================================
# # 8. SELECT BEST MODEL
# # =====================================
# best_model_name         = min(results, key=results.get)
# best_model, needs_scale = trained_models[best_model_name]

# print()
# print(f"Best model  : {best_model_name}  (MAE = {results[best_model_name]:.6f})")
# print(f"Uses scaling: {needs_scale}")

# # =====================================
# # 9. RETRAIN BEST MODEL ON FULL DATA
# # =====================================
# if needs_scale:
#     X_full_scaled = scaler.fit_transform(X)   # refit scaler on all data
#     best_model.fit(X_full_scaled, y)
#     joblib.dump(scaler, "scaler.pkl")
#     print("Saved: scaler.pkl")
# else:
#     best_model.fit(X, y)

# # =====================================
# # 10. SAVE MODEL + COLUMN SCHEMA
# # =====================================
# joblib.dump(best_model, "best_model.pkl")
# joblib.dump(X.columns.tolist(), "model_columns.pkl")
# joblib.dump(needs_scale, "model_needs_scale.pkl")
# print("Saved: best_model.pkl")
# print("Saved: model_columns.pkl")
# print("Saved: model_needs_scale.pkl")

import joblib

import json
from itertools import product

# =========================================================
# LOAD TRAINED ARTIFACTS
# =========================================================
model = joblib.load("best_model.pkl")
model_columns = joblib.load("model_columns.pkl")
needs_scale = joblib.load("model_needs_scale.pkl")

scaler = None
if needs_scale:
    scaler = joblib.load("scaler.pkl")

# =========================================================
# LOAD ROOMS
# =========================================================
def load_rooms(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return data["rooms"]

rooms = load_rooms("/content/drive/MyDrive/Grad Prj/extracted_features.json")


# =========================================================
# SURFACE DEFINITIONS
# =========================================================
SURFACES = {
    "wall": 0.6,
    "floor": 0.25,
    "ceiling": 0.15
}

SURFACE_CATEGORY_RULES = {
    "wall": ["brick", "concrete_block", "stone"],
    "floor": ["concrete", "stone"],
    "ceiling": ["insulation", "concrete"]
}


# =========================================================
# PREPARE DATA FOR MODEL
# =========================================================
def prepare_features(df):
    df_encoded = pd.get_dummies(df, columns=['category', 'roughness'])

    for col in model_columns:
        if col not in df_encoded:
            df_encoded[col] = 0

    return df_encoded[model_columns]


# =========================================================
# PREDICT ML SCORE
# =========================================================
def predict_scores(df):
    X = prepare_features(df)

    if needs_scale:
        X = scaler.transform(X)

    df["predicted_score"] = model.predict(X)
    return df


# =========================================================
# FILTER USER MATERIALS
# =========================================================
def filter_user_materials(df, selected_ids):
    return df[df["material_id"].isin(selected_ids)].copy()


# =========================================================
# VALIDATION
# =========================================================
def validate_selection(df):
    categories = set(df["category"])
    missing = []

    for surface, cats in SURFACE_CATEGORY_RULES.items():
        if not any(cat in categories for cat in cats):
            missing.append(surface)

    return missing


# =========================================================
# CARBON CALCULATION
# =========================================================
def embodied_carbon(area, mat):
    return (
        area *
        mat['density_kg_m3'] *
        mat['thickness_m'] *
        mat['carbon_kgCO2_per_kg']
    )


# =========================================================
# USER BASELINE COMBO (NO OPTIMIZATION)
# =========================================================
def compute_user_combo(room, df, selected_ids):
    combo = {}
    total_carbon = 0

    user_df = df[df["material_id"].isin(selected_ids)]

    for surface, ratio in SURFACES.items():
        cats = SURFACE_CATEGORY_RULES[surface]
        subset = user_df[user_df["category"].isin(cats)]

        if subset.empty:
            return None, None

        mat = subset.iloc[0]  # simulate user choice

        surface_area = room["area_m2"] * ratio
        carbon = embodied_carbon(surface_area, mat)

        combo[surface] = {
            "name": mat["name"],
            "carbon_kg": round(carbon, 2)
        }

        total_carbon += carbon

    return combo, total_carbon


# =========================================================
# GET TOP MATERIALS PER SURFACE
# =========================================================
def get_surface_candidates(df, top_k=3):
    surface_candidates = {}

    for surface, categories in SURFACE_CATEGORY_RULES.items():
        subset = df[df["category"].isin(categories)]

        if subset.empty:
            continue

        subset = subset.sort_values("predicted_score", ascending=False).head(top_k)
        surface_candidates[surface] = subset.to_dict("records")

    return surface_candidates


# =========================================================
# OPTIMIZE ONE ROOM
# =========================================================
def optimize_room(room, surface_candidates):
    if len(surface_candidates) < len(SURFACES):
        return None, None

    best_combo = None
    best_score = float("inf")

    for combo in product(*surface_candidates.values()):
        total_carbon = 0
        combo_details = {}

        for (surface, ratio), mat in zip(SURFACES.items(), combo):
            surface_area = room["area_m2"] * ratio
            carbon = embodied_carbon(surface_area, mat)

            total_carbon += carbon

            combo_details[surface] = {
                "name": mat["name"],
                "carbon_kg": round(carbon, 2)
            }

        if total_carbon < best_score:
            best_score = total_carbon
            best_combo = combo_details

    return best_combo, best_score


# =========================================================
# OPTIMIZE BUILDING (FINAL OUTPUT)
# =========================================================
def optimize_building(df, rooms, selected_ids):
    user_df = filter_user_materials(df, selected_ids)

    if user_df.empty:
        return {"error": "No valid materials selected"}

    missing = validate_selection(user_df)
    if missing:
        return {"error": f"Missing materials for surfaces: {missing}"}

    user_df = predict_scores(user_df)

    results = []
    total_user = 0
    total_opt = 0

    for room in rooms:

        # USER BASELINE
        user_combo, user_carbon = compute_user_combo(room, df, selected_ids)

        # OPTIMIZED
        surface_candidates = get_surface_candidates(user_df)
        opt_combo, opt_carbon = optimize_room(room, surface_candidates)

        if user_combo is None or opt_combo is None:
            results.append({
                "room": room["name"],
                "error": "Invalid material selection"
            })
            continue

        saving = user_carbon - opt_carbon
        saving_pct = (saving / user_carbon * 100) if user_carbon > 0 else 0

        total_user += user_carbon
        total_opt += opt_carbon

        results.append({
            "room": room["name"],
            "area_m2": room["area_m2"],

            "your_selection": {
                "materials": user_combo,
                "total_carbon_kg": round(user_carbon, 2)
            },

            "recommended_solution": {
                "materials": opt_combo,
                "total_carbon_kg": round(opt_carbon, 2)
            },

            "carbon_savings": {
                "saved_kg": round(saving, 2),
                "reduction_percent": round(saving_pct, 1)
            }
        })

    return {
        "summary": {
            "your_total_carbon": round(total_user, 2),
            "optimized_total_carbon": round(total_opt, 2),
            "total_savings": round(total_user - total_opt, 2),
            "reduction_percent": round(
                (total_user - total_opt) / total_user * 100, 1
            ) if total_user > 0 else 0
        },
        "rooms": results
    }


# =========================================================
# RUN DEMO
# =========================================================
if __name__ == "__main__":

    selected_materials = [
        "MAT001", "MAT011", "MAT015",
        "MAT020", "MAT031", "MAT038"
    ]

    result = optimize_building(df, rooms, selected_materials)

    print("\nFINAL RESULT:\n")
    print(json.dumps(result, indent=2))