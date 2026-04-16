import math
from typing import Dict


def comfort_class_from_pmv(pmv_value: float) -> str:
    if pmv_value < -0.5:
        return "Cool"
    elif pmv_value > 0.5:
        return "Warm"
    return "Neutral"


def compute_ppd_from_pmv(pmv_value: float) -> float:
    return 100 - 95 * math.exp(-0.03353 * (pmv_value ** 4) - 0.2179 * (pmv_value ** 2))


def estimate_indoor_conditions(
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> Dict:
    avg_temp = float(climate_features["avg_temp"])
    avg_humidity = float(climate_features["avg_humidity"])
    avg_solar = float(climate_features["avg_solar"])

    total_room_area = max(float(floorplan_features["total_room_area"]), 1.0)
    effective_area = max(
        float(floorplan_features.get("weighted_conditioned_area", total_room_area)),
        1.0
    )

    total_window_area = float(floorplan_features.get("total_window_area", 0.0))

    north_window_area = float(floorplan_features.get("north_window_area", 0.0))
    south_window_area = float(floorplan_features.get("south_window_area", 0.0))
    east_window_area = float(floorplan_features.get("east_window_area", 0.0))
    west_window_area = float(floorplan_features.get("west_window_area", 0.0))

    north_exposed_area = float(floorplan_features.get("north_exposed_area", 0.0))
    south_exposed_area = float(floorplan_features.get("south_exposed_area", 0.0))
    east_exposed_area = float(floorplan_features.get("east_exposed_area", 0.0))
    west_exposed_area = float(floorplan_features.get("west_exposed_area", 0.0))

    u_wall = float(material_uvalues["u_wall"])
    u_roof = float(material_uvalues["u_roof"])
    u_floor = float(material_uvalues["u_floor"])
    u_window = float(material_uvalues["u_window"])
    shgc = float(material_uvalues["shgc"])

    # Gross wall area from exposed directional areas
    wall_area = north_exposed_area + south_exposed_area + east_exposed_area + west_exposed_area

    # Net opaque wall area after removing windows to avoid double-counting
    net_wall_area = max(wall_area - total_window_area, 0.0)

    roof_area = total_room_area
    floor_area = total_room_area

    opaque_heat_transfer = (
        u_wall * net_wall_area +
        u_roof * roof_area +
        u_floor * floor_area
    ) / max((net_wall_area + roof_area + floor_area), 1.0)

    window_heat_transfer = (u_window * total_window_area) / max(effective_area, 1.0)

    envelope_factor = opaque_heat_transfer + window_heat_transfer

    # Solar gain by window direction, using SHGC
    orientation_solar_factor = (
        0.03 * north_window_area +
        0.65 * south_window_area +
        0.22 * east_window_area +
        0.50 * west_window_area
    ) / max(total_window_area, 1.0)

    room_size_factor = min(70000.0 / effective_area, 1.8)
    climate_heat_factor = max(avg_temp - 20.0, 0.0) / 10.0

    solar_gain = (
        (avg_solar / 230.0)
        * shgc
        * (total_window_area / max(effective_area, 1.0))
        * (1.0 + 2.4 * orientation_solar_factor)
        * room_size_factor
    )

    tdb = avg_temp + 0.70 * solar_gain + 0.35 * envelope_factor * climate_heat_factor
    tr = avg_temp + 1.25 * solar_gain + 0.20 * envelope_factor * climate_heat_factor

    return {
        "tdb": tdb,
        "tr": tr,
        "rh": avg_humidity,
    }


def estimate_pmv_simple(
    tdb: float,
    tr: float,
    rh: float,
    vr: float = 0.15,
    met: float = 1.1,
    clo: float = 0.5,
) -> float:
    operative = (tdb + tr) / 2.0

    pmv = (
        0.22 * (operative - 24.0)
        - 0.02 * (rh - 50.0)
        - 0.35 * (vr - 0.15)
        + 0.10 * (met - 1.1)
        + 0.08 * (clo - 0.5)
    )

    return max(-3.0, min(3.0, pmv))


def analyze_thermal_comfort(
    floorplan_features: Dict,
    climate_features: Dict,
    material_uvalues: Dict,
) -> Dict:
    indoor = estimate_indoor_conditions(
        floorplan_features=floorplan_features,
        climate_features=climate_features,
        material_uvalues=material_uvalues,
    )

    pmv = estimate_pmv_simple(
        tdb=indoor["tdb"],
        tr=indoor["tr"],
        rh=indoor["rh"],
        vr=0.15,
        met=1.1,
        clo=0.5,
    )

    ppd = compute_ppd_from_pmv(pmv)
    comfort_score = max(0.0, min(100.0, 100.0 - ppd))
    comfort_class = comfort_class_from_pmv(pmv)

    return {
        "comfort_score": round(comfort_score, 2),
        "comfort_class": comfort_class,
        "pmv": round(pmv, 3),
        "ppd": round(ppd, 2),
        "tdb_est": round(indoor["tdb"], 2),
        "tr_est": round(indoor["tr"], 2),
    }