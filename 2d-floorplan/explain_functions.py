# #Step 2: Normalizing names in dxf file
# def normalize_furniture_name(raw_name):
#     raw_name = raw_name.lower()

#     # Define your "Translation Dictionary" here
#     mapping = {

#     "master br toilet": "toilet_master",
#     "master bedroom": "master_bed",
#     "dressing": "dressing_room",
#     "terrace": "terrace_area",
#     "toilet": "toilet_guest",
#     # --- Seating & Living ---
#     "cay03_mb": "chair_modern",
#     "sofa-46": "sofa_small",
#     "sofa-50": "sofa_large",
#     "s2": "sofa_loveseat",
#     "st": "side_table",
#     "arm-ch": "armchair",

#     # --- Kitchen & Dining ---
#     "12pplt12": "dining_plate",
#     "ps sin 12": "sink_kitchen",
#     "k-sink": "sink_kitchen",
#     "ref-1": "refrigerator",
#     "ovn-01": "oven_range",
#     "dsadas": "dining_table_set", # Based on your previous JSON coordinates

#     # --- Bathroom & Plumbing ---
#     "toilet": "toilet",
#     "lav-01": "sink_bathroom",
#     "shw-sq": "shower_stall",
#     "btub": "bathtub",
#     "f": "fixture_plumbing",

#     # --- Structural & Architectural ---
#     "s-cols": "structural_column",
#     "a-furn": "furniture_layer_generic",
#     "dr-s": "door_single",
#     "dr-d": "door_double",
#     "win-std": "window_standard",

#     # --- Decorative & Utility ---
#     "a$c2cc23d6e": "decor_item",
#     "*u": "utility_block",
#     "fsfsf": "miscellaneous_item",
#     "p-pot": "indoor_plant",
#     "tv-unit": "media_console"
# }

#     # 1. Check for exact match in our dictionary
#     if raw_name in mapping:
#         return mapping[raw_name]

#     # 2. Check for partial matches (e.g., any name containing 'sofa')
#     if "sofa" in raw_name: return "sofa"
#     if "toilet" in raw_name: return "toilet"
#     if "bed" in raw_name: return "bed"
#     if "dressing" in raw_name: return "dressing"
#     if "terrace" in raw_name: return "terrace"
#     if "bath" in raw_name or "shw" in raw_name: return "shower"

#     return raw_name # Fallback to original if no rule found

# def auto_label_room(room, all_furniture):
#     # Find all furniture whose centroid is near this room
#     # (Simple version: check if the furniture is linked to the room_id)
    
#     items_in_room = [f['type'] for f in all_furniture if f.get('room_id') == room['id']]

#     if any("door 100 x 25" in x for x in items_in_room):
#         return "terrace"

#     # التعرف على الـ Dressing
#     if any("a$ce7959106" in x for x in items_in_room):
#         return "dressing_room"

#     # التعرف على الـ Master (لو فيها سرير وحمام في نفس الكلوستر)
#     has_bed = "bed" in items_in_room
#     has_bath = any("shower" in x or "mixer" in x for x in items_in_room)
#     if has_bed and has_bath:
#         return "master_bedroom"

#     if "master_bed" in items_in_room or ("bed" in items_in_room and "toilet_master" in items_in_room):
#         return "master_bedroom"
    
#     if "dressing_room" in items_in_room or "dressing" in items_in_room:
#         return "dressing_room"
        
#     if "terrace_area" in items_in_room or "terrace" in items_in_room:
#         return "terrace"
        
#     if any(x in items_in_room for x in ["toilet", "sink_bathroom", "bathtub","shower_stall"]):
#         return "bathroom"
#     if any(x in items_in_room for x in ["sink_kitchen", "refrigerator", "oven_range"]):
#         return "kitchen"
#     if any(x in items_in_room for x in ["sofa_small", "sofa_large", "sofa_loveseat","side_table","armchair","chair_modern"]):
#         return "living_room"
#     if any(x in items_in_room for x in ["dining_plate", "dining_table_set"]):
#         return "dining_room"
#     if "bed" in items_in_room:
#         return "bedroom"

#     return room['type'] # Keep original if no furniture match 

# from shapely.geometry import Polygon
# from shapely.validation import make_valid

# DEFAULT_FURN_SIZES = {
#     "toilet": (0.7, 0.7),
#     "sink_kitchen": (0.6, 0.6),
#     "fixture_plumbing": (0.4, 0.4),

#     "chair_modern": (0.5, 0.5),
#     "side_table": (0.6, 0.6),

#     "dining_plate": (0.4, 0.4),
#     "dining_table_set": (1.6, 1.2),

#     "sofa_small": (1.6, 0.9),
#     "sofa_loveseat": (1.8, 0.9),
#     "sofa_large": (2.4, 1.0),
#     "sofa": (2.0, 0.9),

#     "decor_item": (0.5, 0.5),
#     "miscellaneous_item": (1.0, 1.0)
# }


# def room_metrics_from_polygon(poly: Polygon):
#     """
#     Returns bounds, width, height, area, perimeter from a shapely polygon.
#     Works for non-rectangular rooms too.
#     """
#     # Fix invalid polygons if needed
#     try:
#         if not poly.is_valid:
#             poly = make_valid(poly)
#     except Exception:
#         pass

#     minx, miny, maxx, maxy = poly.bounds
#     width = maxx - minx
#     height = maxy - miny

#     return {
#         "bounds": {
#             "min_x": round(minx, 2),
#             "min_y": round(miny, 2),
#             "max_x": round(maxx, 2),
#             "max_y": round(maxy, 2),
#         },
#         "width": round(width, 2),
#         "height": round(height, 2),
#         "area": round(poly.area, 2),
#         "perimeter": round(poly.length, 2),
#     }

# import ezdxf
# import numpy as np
# from sklearn.cluster import DBSCAN
# import json

# # ----------------------------
# # Helpers
# # ----------------------------

# def detect_scale_and_eps(furniture_data):
#     """eps based on 10% of total furniture spread."""
#     if not furniture_data:
#         return 25.0
#     coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
#     width  = np.ptp(coords[:, 0])
#     height = np.ptp(coords[:, 1])
#     span = max(width, height)
#     return max(span * 0.10, 1.0)  # avoid eps = 0

# def normalize_furn_for_semantics(t: str) -> str:
#     """Unify names so your cluster labeling works."""
#     t = (t or "").lower().strip()

#     # map your real types to generic keywords for labeling
#     if "sink" in t:
#         return "sink"
#     if "refrigerator" in t or "fridge" in t or "ref" in t:
#         return "refrigerator"
#     if "oven" in t or "stove" in t:
#         return "stove"
#     if "toilet" in t or "wc" in t:
#         return "toilet"
#     if "sofa" in t:
#         return "sofa"
#     if "chair" in t:
#         return "chair"
#     if "plate" in t:
#         return "plate"
#     return t

# def compute_room_metrics_from_bounds(min_x, min_y, max_x, max_y):
#     # الفرق بالوحدات الأصلية
#     w_raw = max_x - min_x
#     h_raw = max_y - min_y
    
#     # احسبي المساحة الأصلية أولاً
#     raw_area = w_raw * h_raw
#     raw_perimeter = 2 * (w_raw + h_raw)

#     # معامل تصحيح (Scale Factor)
#     # هنقسم المساحة على 100 عشان الـ 400 تبقى 4 متر
#     area = raw_area / 100
#     perimeter = raw_perimeter / 10 # المحيط بيتقسم على 10 بس مش 100
    
#     # العرض والطول للتوضيح
#     w_meters = w_raw / 10
#     h_meters = h_raw / 10
    
#     return round(w_meters, 2), round(h_meters, 2), round(area, 2), round(perimeter, 2)

# def filter_outliers_by_main_bbox(furniture_data, margin=200.0):
#     """
#     More robust than abs(x)>5000.
#     Keeps only items near the main cluster.
#     """
#     coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
#     minx, miny = np.min(coords, axis=0)
#     maxx, maxy = np.max(coords, axis=0)

#     # If bbox is enormous (outliers exist), we keep only points near the dense region using percentiles
#     x1, x2 = np.percentile(coords[:, 0], [5, 95])
#     y1, y2 = np.percentile(coords[:, 1], [5, 95])

#     filtered = []
#     for f in furniture_data:
#         x, y = f["centroid"]
#         if (x1 - margin) <= x <= (x2 + margin) and (y1 - margin) <= y <= (y2 + margin):
#             filtered.append(f)
#     return filtered

# # ----------------------------
# # Main
# # ----------------------------

# def dxf_to_json_clustered(dxf_path, padding=10.0, min_samples=1):
#     doc = ezdxf.readfile(dxf_path)
#     msp = doc.modelspace()

#     furniture_data = []

#     # 1) Extract furniture blocks (INSERT)
#     for f_ent in msp.query("INSERT"):
#         x, y = float(f_ent.dxf.insert.x), float(f_ent.dxf.insert.y)

#         # keep raw type + translated type if you want
#         raw_name = f_ent.dxf.name
#         clean_type = normalize_furniture_name(raw_name)  # your existing function
#         sem_type = normalize_furn_for_semantics(clean_type)

#         furniture_data.append({
#             "id": f"furn_{f_ent.dxf.handle}",
#             "type": clean_type,           # keep your normalized type (sink_kitchen, sofa_small...)
#             "semantic_type": sem_type,    # extra field for clustering logic (sink, sofa, toilet...)
#             "centroid": [x, y]
#         })

#     if not furniture_data:
#         return {"rooms": [], "furniture": []}

#     # 2) Filter outliers robustly (fix 64341 / 10334 junk)
#     furniture_data = filter_outliers_by_main_bbox(furniture_data, margin=200.0)
#     if not furniture_data:
#         return {"rooms": [], "furniture": []}

#     # 3) Cluster furniture by proximity
#     coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
#     auto_eps = detect_scale_and_eps(furniture_data) * 1.5
#     print(f"📏 Detected scale. Using eps: {auto_eps:.2f}")

#     clustering = DBSCAN(eps=auto_eps, min_samples=min_samples).fit(coords)
#     labels = clustering.labels_

#     # 4) Semantic merge for kitchen (optional)
#     # 4) Smart Semantic Merge (Merging multiple clusters of the same room type)
#     # تجميع الـ clusters اللي ليهم نفس النوع عشان ما يطلعش 2 Living Room
#     type_to_clusters = {
#         'bathroom': set(),
#         'living_room': set(),
#         'kitchen': set()
#     }

#     # تصنيف الـ clusters الحالية بناءً على العفش اللي جواها
#     for i, furn in enumerate(furniture_data):
#         label = labels[i]
#         if label == -1: continue # تجاهل النويز
        
#         sem_t = furn['semantic_type']
#         if sem_t == 'toilet':
#             type_to_clusters['bathroom'].add(label)
#         elif sem_t in ['sink', 'stove', 'refrigerator']:
#             type_to_clusters['kitchen'].add(label)
#         elif sem_t in ['sofa', 'chair']:
#             type_to_clusters['living_room'].add(label)

#     # تنفيذ الدمج الفعلي
#     new_labels = labels.copy()
#     for r_type, cluster_set in type_to_clusters.items():
#         if len(cluster_set) > 1:
#             main_label = list(cluster_set)[0]
#             for other_label in cluster_set:
#                 new_labels[new_labels == other_label] = main_label
#             print(f"🔗 Merged {len(cluster_set)} clusters into one {r_type}.")
    
#     labels = new_labels

#     # 5) Build room clusters + explanation metrics
#     rooms_data = []
#     for cluster_id in sorted(set(labels)):
#         indices = np.where(labels == cluster_id)[0].tolist()
#         room_items = [furniture_data[i] for i in indices]

#         room_id = f"room_cluster_{cluster_id}"
#         for item in room_items:
#             item['room_id'] = room_id

#         # Label room based on semantic types (more reliable)
#         sem_types = " ".join([item['semantic_type'] for item in room_items])

#         # توسيع نطاق التصنيف بناءً على العفش المكتشف
#         if any(kw in sem_types for kw in ["toilet", "shower", "sink_bathroom", "bathtub", "water_closet"]):
#             r_type = "bathroom"

#         elif any(kw in sem_types for kw in ["bed", "wardrobe", "nightstand", "dresser"]):
#             r_type = "bedroom"

#         elif any(kw in sem_types for kw in ["stove", "oven", "refrigerator", "fridge", "kitchen_cabinet", "dishwasher"]):
#             r_type = "kitchen"

#         elif any(kw in sem_types for kw in ["sofa", "couch", "tv", "media_unit", "armchair", "coffee_table"]):
#             r_type = "living_room"

#         elif any(kw in sem_types for kw in ["dining_table", "plate", "dining_chair"]):
#             r_type = "dining_room"

#         elif any(kw in sem_types for kw in ["desk", "office_chair", "bookshelf", "workstation"]):
#             r_type = "home_office"

#         elif any(kw in sem_types for kw in ["washing_machine", "dryer", "laundry_basket"]):
#             r_type = "laundry_room"

#         elif any(kw in sem_types for kw in ["outdoor_chair", "umbrella", "planter", "balcony_set"]):
#             r_type = "balcony"
#         elif any(kw in sem_types for kw in ["master_bed", "double_bed"]):
#             r_type = "master_bedroom"
#         elif "dressing" in sem_types or ("wardrobe" in sem_types and "bed" not in sem_types):
#             r_type = "dressing_room"

# # Terrace / Balcony
#         elif any(kw in sem_types for kw in ["terrace", "balcony", "railing", "outdoor_chair"]):
#             r_type = "terrace"

# # Entrance / Foyer
#         elif "entrance" in sem_types or "foyer" in sem_types:
#             r_type = "entrance_foyer"

# # Corridor
#         elif "corridor" in sem_types or "passage" in sem_types:
#             r_type = "corridor"

#         elif "sink" in sem_types:
#     # لو فيه حوض بس، ممكن يبقى مطبخ صغير أو حمام ضيوف
#             r_type = "kitchenette" if "fridge" in sem_types else "service_area"

#         else:
#             r_type = "general_area"

#         mean_pos = np.mean([f['centroid'] for f in room_items], axis=0)

#         room_coords = np.array([f['centroid'] for f in room_items], dtype=float)
#         min_x, min_y = np.min(room_coords, axis=0)
#         max_x, max_y = np.max(room_coords, axis=0)

#         # apply padding
#         min_x_p = float(min_x - padding)
#         min_y_p = float(min_y - padding)
#         max_x_p = float(max_x + padding)
#         max_y_p = float(max_y + padding)

#         width, height, area, perimeter = compute_room_metrics_from_bounds(min_x_p, min_y_p, max_x_p, max_y_p)

#         rooms_data.append({
#             "id": room_id,
#             "type": r_type,
#             "centroid": [round(float(mean_pos[0]), 2), round(float(mean_pos[1]), 2)],
#             "bounds": {
#                 "min_x": round(min_x_p, 2),
#                 "min_y": round(min_y_p, 2),
#                 "max_x": round(max_x_p, 2),
#                 "max_y": round(max_y_p, 2),
#             },
#             # Explanation fields (what you wanted)
#             "width": width,
#             "height": height,
#             "area": area,
#             "perimeter": perimeter,
#         })

#     # optional: remove semantic_type if you don’t want it in final output
#     # for f in furniture_data:
#     #     del f["semantic_type"]

#     return {"rooms": rooms_data, "furniture": furniture_data}
