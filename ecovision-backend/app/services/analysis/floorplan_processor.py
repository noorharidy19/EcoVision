import ezdxf
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Polygon
from typing import Dict, Any
def normalize_furniture_name(raw_name):
    raw_name = raw_name.lower()

    # Define your "Translation Dictionary" here
    mapping = {
    # --- Seating & Living ---
    "cay03_mb": "chair_modern",
    "sofa-46": "sofa_small",
    "sofa-50": "sofa_large",
    "s2": "sofa_loveseat",
    "st": "side_table",
    "arm-ch": "armchair",

    # --- Kitchen & Dining ---
    "12pplt12": "dining_plate",
    "ps sin 12": "sink_kitchen",
    "k-sink": "sink_kitchen",
    "ref-1": "refrigerator",
    "ovn-01": "oven_range",
    "dsadas": "dining_table_set", # Based on your previous JSON coordinates

    # --- Bathroom & Plumbing ---
    "toilet": "toilet",
    "lav-01": "sink_bathroom",
    "shw-sq": "shower_stall",
    "btub": "bathtub",
    "f": "fixture_plumbing",

    # --- Structural & Architectural ---
    "s-cols": "structural_column",
    "a-furn": "furniture_layer_generic",
    "dr-s": "door_single",
    "dr-d": "door_double",
    "win-std": "window_standard",

    # --- Decorative & Utility ---
    "a$c2cc23d6e": "decor_item",
    "*u": "utility_block",
    "fsfsf": "miscellaneous_item",
    "p-pot": "indoor_plant",
    "tv-unit": "media_console"
}

    # 1. Check for exact match in our dictionary
    if raw_name in mapping:
        return mapping[raw_name]

    # 2. Check for partial matches (e.g., any name containing 'sofa')
    if "sofa" in raw_name: return "sofa"
    if "toilet" in raw_name: return "toilet"
    if "bed" in raw_name: return "bed"

    return raw_name # Fallback to original if no rule found

def auto_label_room(room, all_furniture):
    # Find all furniture whose centroid is near this room
    # (Simple version: check if the furniture is linked to the room_id)
    items_in_room = [f['type'] for f in all_furniture if f.get('room_id') == room['id']]

    if any(x in items_in_room for x in ["toilet", "sink_bathroom", "bathtub","shower_stall"]):
        return "bathroom"
    if any(x in items_in_room for x in ["sink_kitchen", "refrigerator", "oven_range"]):
        return "kitchen"
    if any(x in items_in_room for x in ["sofa_small", "sofa_large", "sofa_loveseat","side_table","armchair","chair_modern"]):
        return "living_room"
    if any(x in items_in_room for x in ["dining_plate", "dining_table_set"]):
        return "dining_room"
    if "bed" in items_in_room:
        return "bedroom"

    return room['type'] # Keep original if no furniture match
DEFAULT_FURN_SIZES = {
    "toilet": (0.7, 0.7),
    "sink_kitchen": (0.6, 0.6),
    "fixture_plumbing": (0.4, 0.4),

    "chair_modern": (0.5, 0.5),
    "side_table": (0.6, 0.6),

    "dining_plate": (0.4, 0.4),
    "dining_table_set": (1.6, 1.2),

    "sofa_small": (1.6, 0.9),
    "sofa_loveseat": (1.8, 0.9),
    "sofa_large": (2.4, 1.0),
    "sofa": (2.0, 0.9),

    "decor_item": (0.5, 0.5),
    "miscellaneous_item": (1.0, 1.0)
}
def normalize_furn_for_semantics(t: str) -> str:
    t = (t or "").lower().strip()
    if "sink" in t:
        return "sink"
    if "refrigerator" in t or "fridge" in t or "ref" in t:
        return "refrigerator"
    if "oven" in t or "stove" in t:
        return "stove"
    if "toilet" in t or "wc" in t:
        return "toilet"
    if "sofa" in t:
        return "sofa"
    if "chair" in t:
        return "chair"
    if "plate" in t:
        return "plate"
    return t


def filter_outliers_by_main_bbox(furniture_data, margin=200.0):
    if not furniture_data:
        return furniture_data
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    x1, x2 = np.percentile(coords[:, 0], [5, 95])
    y1, y2 = np.percentile(coords[:, 1], [5, 95])
    filtered = []
    for f in furniture_data:
        x, y = f['centroid']
        if (x1 - margin) <= x <= (x2 + margin) and (y1 - margin) <= y <= (y2 + margin):
            filtered.append(f)
    return filtered


def detect_scale_and_eps(furniture_data):
    if not furniture_data:
        return 25.0
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    width = np.ptp(coords[:, 0])
    height = np.ptp(coords[:, 1])
    span = max(width, height)
    return max(span * 0.10, 1.0)


def compute_room_metrics_from_bounds(min_x, min_y, max_x, max_y):
    w = max_x - min_x
    h = max_y - min_y
    area = w * h
    perimeter = 2 * (w + h)
    return round(w, 2), round(h, 2), round(area, 2), round(perimeter, 2)


def dxf_to_json_clustered(dxf_path: str, padding: float = 10.0, min_samples: int = 1) -> Dict[str, Any]:
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    furniture_data = []
    for f_ent in msp.query("INSERT"):
        try:
            x, y = float(f_ent.dxf.insert.x), float(f_ent.dxf.insert.y)
        except Exception:
            continue
        raw_name = getattr(f_ent.dxf, "name", "")
        clean_type = raw_name.lower() if raw_name else "unknown"
        sem_type = normalize_furn_for_semantics(clean_type)
        furniture_data.append({
            "id": f"furn_{f_ent.dxf.handle}",
            "type": clean_type,
            "semantic_type": sem_type,
            "centroid": [x, y]
        })

    if not furniture_data:
        return {"rooms": [], "furniture": []}

    furniture_data = filter_outliers_by_main_bbox(furniture_data, margin=200.0)
    if not furniture_data:
        return {"rooms": [], "furniture": []}

    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    auto_eps = detect_scale_and_eps(furniture_data) * 1.5

    clustering = DBSCAN(eps=auto_eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    rooms_data = []
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
        indices = np.where(labels == cluster_id)[0].tolist()
        room_items = [furniture_data[i] for i in indices]
        room_id = f"room_cluster_{cluster_id}"
        for item in room_items:
            item['room_id'] = room_id

        sem_types = " ".join([item['semantic_type'] for item in room_items])
        if "toilet" in sem_types:
            r_type = "bathroom"
        elif "sink" in sem_types and ("sofa" in sem_types or "chair" in sem_types):
            r_type = "open_kitchen_living"
        elif "sink" in sem_types:
            r_type = "kitchen"
        elif "sofa" in sem_types:
            r_type = "living_room"
        elif "chair" in sem_types or "plate" in sem_types:
            r_type = "dining_room"
        else:
            r_type = "general_area"

        mean_pos = np.mean([f['centroid'] for f in room_items], axis=0)
        room_coords = np.array([f['centroid'] for f in room_items], dtype=float)
        min_x, min_y = np.min(room_coords, axis=0)
        max_x, max_y = np.max(room_coords, axis=0)

        min_x_p = float(min_x - padding)
        min_y_p = float(min_y - padding)
        max_x_p = float(max_x + padding)
        max_y_p = float(max_y + padding)

        width, height, area, perimeter = compute_room_metrics_from_bounds(min_x_p, min_y_p, max_x_p, max_y_p)

        rooms_data.append({
            "id": room_id,
            "type": r_type,
            "centroid": [round(float(mean_pos[0]), 2), round(float(mean_pos[1]), 2)],
            "bounds": {
                "min_x": round(min_x_p, 2),
                "min_y": round(min_y_p, 2),
                "max_x": round(max_x_p, 2),
                "max_y": round(max_y_p, 2),
            },
            "width": width,
            "height": height,
            "area": area,
            "perimeter": perimeter,
        })

    return {"rooms": rooms_data, "furniture": furniture_data}


def dxf_to_json_clustered_from_normalized(dxf_path: str, normalized_furniture: list, padding: float = 10.0, min_samples: int = 1) -> Dict[str, Any]:
    """Cluster normalized furniture data into rooms with enumerated room IDs.
    
    Args:
        dxf_path: Path to DXF file (used for reference)
        normalized_furniture: Pre-normalized list of furniture dictionaries
        padding: Padding around room bounds
        min_samples: Minimum samples for DBSCAN clustering
        
    Returns:
        Dictionary with rooms and furniture data
    """
    furniture_data = normalized_furniture.copy()
    
    if not furniture_data:
        return {"rooms": [], "furniture": []}

    # Filter outliers
    furniture_data = filter_outliers_by_main_bbox(furniture_data, margin=200.0)
    if not furniture_data:
        return {"rooms": [], "furniture": []}

    # Prepare coordinates for clustering
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    auto_eps = detect_scale_and_eps(furniture_data) * 1.5

    # Perform DBSCAN clustering
    clustering = DBSCAN(eps=auto_eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    # First pass: collect rooms and determine types
    temp_rooms = []
    room_type_counts = {}  # Track count of each room type for enumeration
    
    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue
            
        indices = np.where(labels == cluster_id)[0].tolist()
        room_items = [furniture_data[i] for i in indices]
        
        # Determine room type based on semantic furniture types
        sem_types = " ".join([item['semantic_type'] for item in room_items])
        
        if "toilet" in sem_types:
            r_type = "bathroom"
        elif "sink" in sem_types and ("sofa" in sem_types or "chair" in sem_types):
            r_type = "open_kitchen_living"
        elif "sink" in sem_types:
            r_type = "kitchen"
        elif "sofa" in sem_types:
            r_type = "living_room"
        elif "chair" in sem_types or "plate" in sem_types:
            r_type = "dining_room"
        elif "bed" in sem_types:
            r_type = "bedroom"
        else:
            r_type = "general_area"
        
        # Count room types for enumeration
        if r_type not in room_type_counts:
            room_type_counts[r_type] = 0
        room_type_counts[r_type] += 1
        room_number = room_type_counts[r_type]
        
        temp_rooms.append({
            "cluster_id": cluster_id,
            "type": r_type,
            "number": room_number,
            "items": room_items
        })
    
    # Second pass: create final rooms with enumerated IDs
    rooms_data = []
    for temp_room in temp_rooms:
        r_type = temp_room["type"]
        room_number = temp_room["number"]
        room_items = temp_room["items"]
        
        # Create enumerated room ID (bathroom1, bathroom2, living_room1, etc.)
        enumerated_room_id = f"{r_type}{room_number}"
        
        # Assign room_id to furniture
        for item in room_items:
            item['room_id'] = enumerated_room_id

        # Calculate room metrics
        mean_pos = np.mean([f['centroid'] for f in room_items], axis=0)
        room_coords = np.array([f['centroid'] for f in room_items], dtype=float)
        min_x, min_y = np.min(room_coords, axis=0)
        max_x, max_y = np.max(room_coords, axis=0)

        min_x_p = float(min_x - padding)
        min_y_p = float(min_y - padding)
        max_x_p = float(max_x + padding)
        max_y_p = float(max_y + padding)

        width, height, area, perimeter = compute_room_metrics_from_bounds(min_x_p, min_y_p, max_x_p, max_y_p)

        rooms_data.append({
            "id": enumerated_room_id,
            "type": r_type,
            "number": room_number,
            "centroid": [round(float(mean_pos[0]), 2), round(float(mean_pos[1]), 2)],
            "bounds": {
                "min_x": round(min_x_p, 2),
                "min_y": round(min_y_p, 2),
                "max_x": round(max_x_p, 2),
                "max_y": round(max_y_p, 2),
            },
            "width": width,
            "height": height,
            "area": area,
            "perimeter": perimeter,
        })

    return {"rooms": rooms_data, "furniture": furniture_data}
