import ezdxf
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Polygon
from typing import Dict, Any

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
