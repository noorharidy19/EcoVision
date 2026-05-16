from copy import deepcopy
from typing import Dict, List

from thermal_comfort_engine import analyze_thermal_comfort


MIN_IMPROVEMENT_TO_SHOW = 0.3


def run_scenario(
    name: str,
    description: str,
    design_action: str,
    why_it_helps: str,
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> Dict:
    result = analyze_thermal_comfort(
        floorplan_features=floorplan_features,
        climate_features=climate_features,
        material_uvalues=material_uvalues,
    )

    return {
        "name": name,
        "description": description,
        "design_action": design_action,
        "why_it_helps": why_it_helps,
        "result": result,
    }


# =========================================================
# Helper Functions for Window Feature Updates
# =========================================================

def update_window_ratios_and_wwr(floorplan_features: Dict) -> Dict:
    """
    Recalculates WWR and directional window ratios after changing window areas.
    This keeps the modified scenario consistent.
    """
    updated = deepcopy(floorplan_features)

    total_window_area = max(float(updated.get("total_window_area", 0.0)), 0.0)
    total_room_area = max(float(updated.get("total_room_area", 1.0)), 1.0)

    updated["wwr"] = round(total_window_area / total_room_area, 4)

    denominator = max(total_window_area, 1.0)

    for direction in ["north", "south", "east", "west"]:
        area_key = f"{direction}_window_area"
        ratio_key = f"{direction}_window_ratio"
        updated[ratio_key] = round(float(updated.get(area_key, 0.0)) / denominator, 4)

    return updated


def reduce_window_area(floorplan_features: Dict, reduction_ratio: float) -> Dict:
    """
    Reduces all window areas by the same percentage.
    """
    updated = deepcopy(floorplan_features)
    factor = 1.0 - reduction_ratio

    window_keys = [
        "total_window_area",
        "north_window_area",
        "south_window_area",
        "east_window_area",
        "west_window_area",
    ]

    for key in window_keys:
        updated[key] = round(float(updated.get(key, 0.0)) * factor, 4)

    return update_window_ratios_and_wwr(updated)


def increase_window_area(floorplan_features: Dict, increase_ratio: float) -> Dict:
    """
    Increases all window areas by the same percentage.
    Useful when the current design is slightly cool.
    """
    updated = deepcopy(floorplan_features)
    factor = 1.0 + increase_ratio

    window_keys = [
        "total_window_area",
        "north_window_area",
        "south_window_area",
        "east_window_area",
        "west_window_area",
    ]

    for key in window_keys:
        updated[key] = round(float(updated.get(key, 0.0)) * factor, 4)

    return update_window_ratios_and_wwr(updated)


def reduce_directional_window_area(
    floorplan_features: Dict,
    directions: List[str],
    reduction_ratio: float,
) -> Dict:
    """
    Reduces window area only in selected directions, such as south/west.
    """
    updated = deepcopy(floorplan_features)
    total_reduction = 0.0

    for direction in directions:
        key = f"{direction}_window_area"
        old_area = float(updated.get(key, 0.0))
        reduction = old_area * reduction_ratio

        updated[key] = round(max(old_area - reduction, 0.0), 4)
        total_reduction += reduction

    updated["total_window_area"] = round(
        max(float(updated.get("total_window_area", 0.0)) - total_reduction, 0.0),
        4,
    )

    return update_window_ratios_and_wwr(updated)


def reduce_south_west_window_area(floorplan_features: Dict, reduction_ratio: float) -> Dict:
    """
    Reduces/shades the most sun-exposed glazing.
    Mainly affects south and west windows.
    """
    return reduce_directional_window_area(
        floorplan_features=floorplan_features,
        directions=["south", "west"],
        reduction_ratio=reduction_ratio,
    )


def increase_directional_window_area(
    floorplan_features: Dict,
    direction: str,
    increase_ratio: float,
) -> Dict:
    """
    Increases window area in one selected direction.
    """
    updated = deepcopy(floorplan_features)

    key = f"{direction}_window_area"
    old_area = float(updated.get(key, 0.0))
    added_area = old_area * increase_ratio

    updated[key] = round(old_area + added_area, 4)
    updated["total_window_area"] = round(
        float(updated.get("total_window_area", 0.0)) + added_area,
        4,
    )

    return update_window_ratios_and_wwr(updated)


def increase_south_window_area(floorplan_features: Dict, increase_ratio: float) -> Dict:
    """
    Increases useful south-facing solar exposure.
    Useful when the design is slightly cool.
    """
    return increase_directional_window_area(
        floorplan_features=floorplan_features,
        direction="south",
        increase_ratio=increase_ratio,
    )


def redistribute_west_windows_to_north_east(
    floorplan_features: Dict,
    shift_ratio: float,
) -> Dict:
    """
    Moves part of west-facing window area toward north/east orientations.
    Total window area stays the same, but orientation distribution changes.
    """
    updated = deepcopy(floorplan_features)

    west_area = float(updated.get("west_window_area", 0.0))
    shifted_area = west_area * shift_ratio

    updated["west_window_area"] = round(max(west_area - shifted_area, 0.0), 4)

    updated["north_window_area"] = round(
        float(updated.get("north_window_area", 0.0)) + shifted_area / 2,
        4,
    )

    updated["east_window_area"] = round(
        float(updated.get("east_window_area", 0.0)) + shifted_area / 2,
        4,
    )

    return update_window_ratios_and_wwr(updated)


# =========================================================
# Text / Explanation Helpers
# =========================================================

def get_impact_level(improvement: float) -> str:
    if improvement >= 10:
        return "High impact"
    elif improvement >= 4:
        return "Medium impact"
    elif improvement > 0:
        return "Low impact"
    return "Not recommended"


def get_current_design_summary(current_result: Dict) -> str:
    pmv = float(current_result["pmv"])
    score = float(current_result["comfort_score"])

    if current_result["comfort_class"] == "Neutral" and score >= 85:
        if pmv < -0.3:
            return "The current design is comfortable but slightly cool."
        if pmv > 0.3:
            return "The current design is comfortable but slightly warm."
        return "The current design is performing well under the selected conditions."

    if pmv > 0.5:
        return "The current design tends to feel warm, mainly due to heat gain and climate conditions."

    if pmv < -0.5:
        return "The current design tends to feel cool, so heat retention or useful solar gain may need improvement."

    return "The current design is close to neutral comfort but can still be optimized."


def detect_main_issue(
    current_result: Dict,
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> Dict:
    pmv = float(current_result["pmv"])
    avg_temp = float(climate_features.get("avg_temp", 0.0))
    avg_solar = float(climate_features.get("avg_solar", 0.0))
    shgc = float(material_uvalues.get("shgc", 0.0))
    u_window = float(material_uvalues.get("u_window", 0.0))
    wwr = float(floorplan_features.get("wwr", 0.0))

    south_ratio = float(floorplan_features.get("south_window_ratio", 0.0))
    west_ratio = float(floorplan_features.get("west_window_ratio", 0.0))

    if pmv > 0.5:
        if avg_temp > 25 or avg_solar > 250 or shgc > 0.6:
            return {
                "issue": "Overheating",
                "direction": "cooling",
                "explanation": (
                    "The design feels warm because climate heat and solar radiation are increasing indoor temperature. "
                    "Cooling-oriented strategies such as reducing solar gain, improving glazing, or shading windows should be tested."
                ),
            }

        if u_window > 3.0 or wwr > 0.25 or south_ratio > 0.35 or west_ratio > 0.25:
            return {
                "issue": "Overheating due to window performance, size, or orientation",
                "direction": "cooling",
                "explanation": (
                    "The design feels warm because window properties, window size, or window orientation may be increasing heat gain. "
                    "The system should test glazing upgrades and window design changes."
                ),
            }

        return {
            "issue": "General overheating",
            "direction": "cooling",
            "explanation": (
                "The design is warmer than the comfort range, so cooling-oriented design changes are needed."
            ),
        }

    if pmv < -0.5:
        return {
            "issue": "Cool indoor conditions",
            "direction": "warming",
            "explanation": (
                "The design feels cool, so strategies that increase useful solar gain or reduce excessive heat blocking should be tested."
            ),
        }

    if -0.5 <= pmv < -0.3:
        return {
            "issue": "Slightly cool but still comfortable",
            "direction": "gentle_warming",
            "explanation": (
                "The design is already comfortable but leans slightly cool. "
                "Only small warming-oriented adjustments should be tested to avoid overcorrecting the design."
            ),
        }

    if 0.3 < pmv <= 0.5:
        return {
            "issue": "Slightly warm but still comfortable",
            "direction": "gentle_cooling",
            "explanation": (
                "The design is already comfortable but leans slightly warm. "
                "Only small cooling-oriented adjustments should be tested."
            ),
        }

    return {
        "issue": "Near neutral comfort",
        "direction": "neutral",
        "explanation": (
            "The design is already close to thermal neutrality. Strong design changes are not necessary."
        ),
    }


def generate_comparison_insight(
    current_result: Dict,
    best_scenario: Dict,
    main_issue: Dict,
) -> str:
    if not best_scenario:
        return (
            f"{main_issue['explanation']} "
            "The tested scenarios did not produce a noticeable improvement. "
            "This means the current design may already be suitable under the selected conditions."
        )

    improvement = float(best_scenario["improvement_points"])
    before_class = best_scenario["comfort_class_before"]
    after_class = best_scenario["comfort_class_after"]

    return (
        f"{main_issue['explanation']} "
        f"The best scenario is '{best_scenario['name']}'. "
        f"It improves the comfort score by {improvement:.2f} points "
        f"and changes the comfort class from {before_class} to {after_class}."
    )


# =========================================================
# Scenario Groups
# =========================================================

def add_cooling_scenarios(
    scenarios: List[Dict],
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> None:
    current_u_window = float(material_uvalues.get("u_window", 0.0))
    current_shgc = float(material_uvalues.get("shgc", 0.0))

    if current_u_window > 2.8 or current_shgc > 0.65:
        double_glazing_materials = deepcopy(material_uvalues)
        double_glazing_materials["u_window"] = 2.8
        double_glazing_materials["shgc"] = 0.65

        scenarios.append(
            run_scenario(
                name="Upgrade to Double Glazing",
                description="Replace current glazing with double glazing.",
                design_action="Use double-glazed windows instead of weaker glazing.",
                why_it_helps="Double glazing reduces heat transfer through windows.",
                floorplan_features=floorplan_features,
                climate_features=climate_features,
                material_uvalues=double_glazing_materials,
            )
        )

    if current_u_window > 1.6 or current_shgc > 0.45:
        low_e_materials = deepcopy(material_uvalues)
        low_e_materials["u_window"] = 1.6
        low_e_materials["shgc"] = 0.45

        scenarios.append(
            run_scenario(
                name="Upgrade to Low-E Double Glazing",
                description="Use low-E glazing to reduce solar heat gain and improve window thermal performance.",
                design_action="Replace current windows with Low-E double glazing.",
                why_it_helps="Low-E glazing lowers SHGC, reducing solar heat entering the building.",
                floorplan_features=floorplan_features,
                climate_features=climate_features,
                material_uvalues=low_e_materials,
            )
        )

    shading_materials = deepcopy(material_uvalues)
    shading_materials["shgc"] = round(max(float(shading_materials["shgc"]) * 0.65, 0.30), 4)

    scenarios.append(
        run_scenario(
            name="Add External Shading / Solar Control",
            description="Reduce effective solar heat gain through shading devices or solar-control glazing.",
            design_action="Add shading devices or use stronger solar-control glazing.",
            why_it_helps="This reduces direct solar gain, which can lower overheating risk.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=shading_materials,
        )
    )

    scenarios.append(
        run_scenario(
            name="Reduce South/West Window Size",
            description="Reduce the size of south and west-facing windows.",
            design_action="Decrease south/west window dimensions or use smaller openings.",
            why_it_helps=(
                "South and west-facing windows can receive stronger solar exposure. "
                "Reducing their size lowers solar heat gain."
            ),
            floorplan_features=reduce_directional_window_area(
                floorplan_features,
                directions=["south", "west"],
                reduction_ratio=0.25,
            ),
            climate_features=climate_features,
            material_uvalues=material_uvalues,
        )
    )

    scenarios.append(
        run_scenario(
            name="Redistribute West Windows Toward North/East",
            description="Move part of the west-facing window area toward north/east orientations.",
            design_action="Redesign some west-facing windows toward north/east sides.",
            why_it_helps=(
                "This keeps daylight potential while reducing stronger west-side heat gain."
            ),
            floorplan_features=redistribute_west_windows_to_north_east(
                floorplan_features,
                shift_ratio=0.50,
            ),
            climate_features=climate_features,
            material_uvalues=material_uvalues,
        )
    )

    roof_materials = deepcopy(material_uvalues)
    roof_materials["u_roof"] = round(float(roof_materials["u_roof"]) * 0.5, 4)

    scenarios.append(
        run_scenario(
            name="Improve Roof Insulation",
            description="Reduce roof U-value to limit heat transfer through the roof.",
            design_action="Use stronger roof insulation.",
            why_it_helps="The roof is exposed to solar heat, so better roof insulation can reduce overheating.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=roof_materials,
        )
    )

    scenarios.append(
        run_scenario(
            name="Reduce Overall Window Area by 25%",
            description="Reduce total glazing area to lower solar heat gain and overheating risk.",
            design_action="Reduce excessive window area or use smaller window openings.",
            why_it_helps="Less glazing reduces solar gain and heat transfer through windows.",
            floorplan_features=reduce_window_area(floorplan_features, 0.25),
            climate_features=climate_features,
            material_uvalues=material_uvalues,
        )
    )

    combined_floorplan = reduce_south_west_window_area(floorplan_features, 0.25)

    combined_materials = deepcopy(material_uvalues)
    combined_materials["u_roof"] = round(float(combined_materials["u_roof"]) * 0.5, 4)
    combined_materials["u_window"] = 1.6
    combined_materials["shgc"] = 0.35

    scenarios.append(
        run_scenario(
            name="Combined Solar-Control Strategy",
            description="Combine Low-E glazing, roof insulation, and reduced south/west window exposure.",
            design_action="Use Low-E glazing, improve roof insulation, and reduce or shade south/west-facing windows.",
            why_it_helps="This targets solar heat through windows and heat transfer through the roof together.",
            floorplan_features=combined_floorplan,
            climate_features=climate_features,
            material_uvalues=combined_materials,
        )
    )


def add_warming_scenarios(
    scenarios: List[Dict],
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> None:
    warmer_glazing = deepcopy(material_uvalues)
    warmer_glazing["shgc"] = round(min(float(warmer_glazing.get("shgc", 0.0)) * 1.15, 0.85), 4)

    scenarios.append(
        run_scenario(
            name="Use Higher-SHGC Glazing",
            description="Use glazing that allows more useful solar heat gain.",
            design_action="Select glazing with a slightly higher SHGC.",
            why_it_helps="Higher SHGC allows more solar heat into the space, which can help when the design is cool.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=warmer_glazing,
        )
    )

    scenarios.append(
        run_scenario(
            name="Increase Overall Window Area Slightly",
            description="Increase total glazing area to admit more useful solar gain.",
            design_action="Increase total window area or WWR slightly.",
            why_it_helps="More glazing can increase useful solar gain when the building is cooler than desired.",
            floorplan_features=increase_window_area(floorplan_features, 0.15),
            climate_features=climate_features,
            material_uvalues=material_uvalues,
        )
    )

    scenarios.append(
        run_scenario(
            name="Increase South-Facing Window Size",
            description="Increase useful south-facing window area slightly.",
            design_action="Increase south-facing window dimensions or add a small south-facing opening.",
            why_it_helps="Controlled south-facing solar gain can move PMV closer to neutral comfort.",
            floorplan_features=increase_south_window_area(floorplan_features, 0.20),
            climate_features=climate_features,
            material_uvalues=material_uvalues,
        )
    )

    reduced_shading = deepcopy(material_uvalues)
    reduced_shading["shgc"] = round(min(float(reduced_shading.get("shgc", 0.0)) * 1.10, 0.85), 4)

    scenarios.append(
        run_scenario(
            name="Reduce Excessive Solar Control",
            description="Avoid overly strong solar-control glazing or shading in a cool design.",
            design_action="Use less aggressive solar-control treatment.",
            why_it_helps="Reducing excessive solar control can prevent the design from becoming too cool.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=reduced_shading,
        )
    )


def add_neutral_optimization_scenarios(
    scenarios: List[Dict],
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> None:
    mild_roof = deepcopy(material_uvalues)
    mild_roof["u_roof"] = round(float(mild_roof["u_roof"]) * 0.85, 4)

    scenarios.append(
        run_scenario(
            name="Mild Roof Insulation Improvement",
            description="Slightly improve roof insulation without strongly changing the design.",
            design_action="Use a slightly better roof assembly.",
            why_it_helps="A mild change can improve stability without overcorrecting an already comfortable design.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=mild_roof,
        )
    )

    mild_window = deepcopy(material_uvalues)
    mild_window["u_window"] = round(max(float(mild_window["u_window"]) * 0.85, 1.6), 4)

    scenarios.append(
        run_scenario(
            name="Mild Window Thermal Upgrade",
            description="Slightly improve window thermal performance.",
            design_action="Use moderately improved glazing.",
            why_it_helps="A small glazing improvement may improve comfort without strongly changing the design.",
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=mild_window,
        )
    )


# =========================================================
# Main Recommendation Function
# =========================================================

def recommend_thermal_scenarios(
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> Dict:
    current_result = analyze_thermal_comfort(
        floorplan_features=floorplan_features,
        climate_features=climate_features,
        material_uvalues=material_uvalues,
    )

    main_issue = detect_main_issue(
        current_result=current_result,
        floorplan_features=floorplan_features,
        climate_features=climate_features,
        material_uvalues=material_uvalues,
    )

    scenarios: List[Dict] = []
    direction = main_issue["direction"]

    if direction == "cooling":
        add_cooling_scenarios(
            scenarios,
            floorplan_features,
            climate_features,
            material_uvalues,
        )

    elif direction in ["warming", "gentle_warming"]:
        add_warming_scenarios(
            scenarios,
            floorplan_features,
            climate_features,
            material_uvalues,
        )

    elif direction == "gentle_cooling":
        add_cooling_scenarios(
            scenarios,
            floorplan_features,
            climate_features,
            material_uvalues,
        )

    else:
        add_neutral_optimization_scenarios(
            scenarios,
            floorplan_features,
            climate_features,
            material_uvalues,
        )

    current_score = float(current_result["comfort_score"])
    compared_scenarios = []
    all_tested_scenarios = []

    for scenario in scenarios:
        after_result = scenario["result"]
        after_score = float(after_result["comfort_score"])
        improvement = round(after_score - current_score, 2)

        before_after_summary = (
            f"This change improves comfort from {current_score}% to {after_score}% "
            f"({improvement:+.2f} points). "
            f"PMV changes from {current_result['pmv']} to {after_result['pmv']}, "
            f"and PPD changes from {current_result['ppd']}% to {after_result['ppd']}%. "
            f"The comfort class changes from {current_result['comfort_class']} "
            f"to {after_result['comfort_class']}."
        )

        scenario_comparison = {
            "name": scenario["name"],
            "description": scenario["description"],
            "design_action": scenario["design_action"],
            "why_it_helps": scenario["why_it_helps"],
            "before_after_summary": before_after_summary,
            "comfort_score_before": current_score,
            "comfort_score_after": after_result["comfort_score"],
            "improvement_points": improvement,
            "comfort_class_before": current_result["comfort_class"],
            "comfort_class_after": after_result["comfort_class"],
            "pmv_before": current_result["pmv"],
            "pmv_after": after_result["pmv"],
            "ppd_before": current_result["ppd"],
            "ppd_after": after_result["ppd"],
            "tdb_before": current_result["tdb_est"],
            "tdb_after": after_result["tdb_est"],
            "tr_before": current_result["tr_est"],
            "tr_after": after_result["tr_est"],
        }

        all_tested_scenarios.append(scenario_comparison)

        if improvement <= MIN_IMPROVEMENT_TO_SHOW:
            continue

        compared_scenarios.append(
            {
                **scenario_comparison,
                "impact_level": get_impact_level(improvement),
            }
        )

    compared_scenarios = sorted(
        compared_scenarios,
        key=lambda x: x["improvement_points"],
        reverse=True,
    )

    all_tested_scenarios = sorted(
        all_tested_scenarios,
        key=lambda x: x["improvement_points"],
        reverse=True,
    )

    best_scenario = compared_scenarios[0] if compared_scenarios else None

    comparison_insight = generate_comparison_insight(
        current_result=current_result,
        best_scenario=best_scenario,
        main_issue=main_issue,
    )

    if best_scenario:
        architect_summary = (
            f"Current design: {current_result['comfort_score']}% "
            f"({current_result['comfort_class']}). "
            f"Detected issue: {main_issue['issue']}. "
            f"Best improvement: {best_scenario['name']} can raise comfort to "
            f"{best_scenario['comfort_score_after']}% "
            f"({best_scenario['improvement_points']:+.2f} points)."
        )
    else:
        architect_summary = (
            f"Current design: {current_result['comfort_score']}% "
            f"({current_result['comfort_class']}). "
            f"Detected issue: {main_issue['issue']}. "
            "No tested scenario produced a noticeable improvement, so the current design may already be suitable "
            "or only needs very small design adjustments."
        )

    return {
        "current_design": {
            "comfort_score": current_result["comfort_score"],
            "comfort_class": current_result["comfort_class"],
            "pmv": current_result["pmv"],
            "ppd": current_result["ppd"],
            "tdb_est": current_result["tdb_est"],
            "tr_est": current_result["tr_est"],
            "summary": get_current_design_summary(current_result),
        },
        "current_result": current_result,
        "main_issue": main_issue,
        "architect_summary": architect_summary,
        "comparison_insight": comparison_insight,
        "recommended_scenarios": compared_scenarios,
        "all_tested_scenarios": all_tested_scenarios,
        "best_scenario": best_scenario,
    }