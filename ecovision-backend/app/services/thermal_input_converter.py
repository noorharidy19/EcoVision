from typing import Dict


def mm2_to_m2(width_mm: float, height_mm: float) -> float:
    return (width_mm / 1000.0) * (height_mm / 1000.0)


def normalize_direction(value: str) -> str:
    if not value:
        return "unknown"
    value = value.strip().upper()
    if value in {"N", "S", "E", "W"}:
        return value
    return "unknown"


def classify_space(name: str, is_circulation: bool = False) -> str:
    name = (name or "").strip().lower()

    if "terrace" in name or "balcony" in name:
        return "outdoor"

    if is_circulation or "lobby" in name or "corridor" in name or "hall" in name:
        return "circulation"

    if "bathroom" in name or "toilet" in name or "wc" in name:
        return "service"

    return "main"


def convert_test_json_to_engine_features(data: Dict) -> Dict:
    rooms = data.get("rooms", [])

    # We will compute conditioned indoor area only
    conditioned_area_m2 = 0.0
    weighted_area_m2 = 0.0

    num_rooms = 0
    num_windows = 0
    num_doors = int(data.get("total_doors", 0))

    num_bedrooms = 0
    num_bathrooms = 0
    num_kitchens = 0

    total_window_area = 0.0

    north_window_area = 0.0
    south_window_area = 0.0
    east_window_area = 0.0
    west_window_area = 0.0

    north_exposed_area = 0.0
    south_exposed_area = 0.0
    east_exposed_area = 0.0
    west_exposed_area = 0.0

    rooms_north = 0
    rooms_south = 0
    rooms_east = 0
    rooms_west = 0

    high_use_area = 0.0

    kept_room_areas = []

    for room in rooms:
        name = str(room.get("name", ""))
        is_circulation = bool(room.get("is_circulation", False))
        is_high_use = bool(room.get("is_high_use", False))

        space_type = classify_space(name, is_circulation)
        area = float(room.get("area_m2", 0.0))
        orientation = normalize_direction(room.get("orientation", "unknown"))
        all_window_directions = room.get("all_window_directions", []) or []
        window_dimensions = room.get("window_dimensions", []) or []

        # -------- EXCLUDE outdoor spaces completely --------
        if space_type == "outdoor":
            continue

        # -------- Apply weighting --------
        # main spaces count fully
        # circulation/service count partially
        if space_type == "main":
            area_weight = 1.0
        elif space_type == "circulation":
            area_weight = 0.35
        else:  # service
            area_weight = 0.50

        weighted_area = area * area_weight

        conditioned_area_m2 += area
        weighted_area_m2 += weighted_area
        kept_room_areas.append(area)
        num_rooms += 1

        lower_name = name.lower()
        if "bedroom" in lower_name:
            num_bedrooms += 1
        elif "bathroom" in lower_name:
            num_bathrooms += 1
        elif "kitchen" in lower_name:
            num_kitchens += 1

        if is_high_use:
            high_use_area += area

        # -------- Directional exposed area --------
        if orientation == "N":
            rooms_north += 1
            north_exposed_area += weighted_area
        elif orientation == "S":
            rooms_south += 1
            south_exposed_area += weighted_area
        elif orientation == "E":
            rooms_east += 1
            east_exposed_area += weighted_area
        elif orientation == "W":
            rooms_west += 1
            west_exposed_area += weighted_area

        # -------- Windows --------
        room_window_count = int(room.get("window_count", 0))
        num_windows += room_window_count

        for i, wd in enumerate(all_window_directions):
            direction = normalize_direction(wd)

            if i < len(window_dimensions):
                width_mm = float(window_dimensions[i].get("width_mm", 0.0))
                height_mm = float(window_dimensions[i].get("height_mm", 0.0))
                win_area = mm2_to_m2(width_mm, height_mm)
            else:
                win_area = 0.0

            # Windows of circulation/service spaces contribute less
            weighted_window_area = win_area * area_weight

            total_window_area += weighted_window_area

            if direction == "N":
                north_window_area += weighted_window_area
            elif direction == "S":
                south_window_area += weighted_window_area
            elif direction == "E":
                east_window_area += weighted_window_area
            elif direction == "W":
                west_window_area += weighted_window_area

    total_room_area = conditioned_area_m2
    avg_room_area = total_room_area / num_rooms if num_rooms > 0 else 0.0
    largest_room_area = max(kept_room_areas) if kept_room_areas else 0.0

    # Use conditioned indoor area for WWR proxy
    wwr = total_window_area / total_room_area if total_room_area > 0 else 0.0

    north_window_ratio = north_window_area / total_window_area if total_window_area > 0 else 0.0
    south_window_ratio = south_window_area / total_window_area if total_window_area > 0 else 0.0
    east_window_ratio = east_window_area / total_window_area if total_window_area > 0 else 0.0
    west_window_ratio = west_window_area / total_window_area if total_window_area > 0 else 0.0

    return {
        "total_room_area": round(total_room_area, 3),
        "weighted_conditioned_area": round(weighted_area_m2, 3),
        "avg_room_area": round(avg_room_area, 3),
        "largest_room_area": round(largest_room_area, 3),

        "num_rooms": num_rooms,
        "num_windows": num_windows,
        "num_doors": num_doors,
        "num_bedrooms": num_bedrooms,
        "num_bathrooms": num_bathrooms,
        "num_kitchens": num_kitchens,

        "total_window_area": round(total_window_area, 3),
        "wwr": round(wwr, 4),

        "north_window_area": round(north_window_area, 3),
        "south_window_area": round(south_window_area, 3),
        "east_window_area": round(east_window_area, 3),
        "west_window_area": round(west_window_area, 3),

        "north_window_ratio": round(north_window_ratio, 4),
        "south_window_ratio": round(south_window_ratio, 4),
        "east_window_ratio": round(east_window_ratio, 4),
        "west_window_ratio": round(west_window_ratio, 4),

        "north_exposed_area": round(north_exposed_area, 3),
        "south_exposed_area": round(south_exposed_area, 3),
        "east_exposed_area": round(east_exposed_area, 3),
        "west_exposed_area": round(west_exposed_area, 3),

        "rooms_north": rooms_north,
        "rooms_south": rooms_south,
        "rooms_east": rooms_east,
        "rooms_west": rooms_west,

        "high_use_area": round(high_use_area, 3),
    }