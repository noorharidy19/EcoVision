import os

#Step 2: Normalizing names in dxf file
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
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint, Polygon

def generate_furniture_clusters(msp, eps=0.5, min_samples=3):
    """
    eps: المسافة بين الخطوط عشان نعتبرهم قطعة واحدة (مثلاً 50 سم)
    """
    points = []
    line_entities = []

    # 1. تجميع كل النقط من الخطوط الموجودة في الرسمة
    for entity in msp.query('LINE LWPOLYLINE'):
        if entity.dxftype() == 'LINE':
            p1, p2 = entity.dxf.start, entity.dxf.end
            points.append([p1.x, p1.y])
            points.append([p2.x, p2.y])
            line_entities.append(entity)
        elif entity.dxftype() == 'LWPOLYLINE':
            for p in entity.get_points():
                points.append([p[0], p[1]])
            line_entities.append(entity)

    if not points:
        return []

    X = np.array(points)
    
    # 2. تشغيل الـ DBSCAN لتجميع النقط القريبة
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = clustering.labels_

    clusters_output = []
    unique_labels = set(labels)

    for label in unique_labels:
        if label == -1: continue  # Noise (خطوط لوحدها)

        cluster_points = X[labels == label]
        
        # حساب السنتر (Centroid) للـ Cluster ده
        centroid_x = np.mean(cluster_points[:, 0])
        centroid_y = np.mean(cluster_points[:, 1])

        # حساب الحدود (Bounding Box)
        min_x, min_y = np.min(cluster_points, axis=0)
        max_x, max_y = np.max(cluster_points, axis=0)
        width = max_x - min_x
        height = max_y - min_y

        clusters_output.append({
            "id": f"furn_cluster_{label}",
            "type": "unknown_furniture", # الـ AI هو اللي هيحدد النوع بعدين
            "centroid": [round(centroid_x, 2), round(centroid_y, 2)],
            "width": round(width, 2),
            "height": round(height, 2),
            "points_count": len(cluster_points)
        })

    print(f"✅ Found {len(clusters_output)} furniture clusters!")
    return clusters_output

from shapely.geometry import Polygon
from shapely.validation import make_valid

def room_metrics_from_polygon(poly: Polygon):
    """
    Returns bounds, width, height, area, perimeter from a shapely polygon.
    Works for non-rectangular rooms too.
    """
    # Fix invalid polygons if needed
    try:
        if not poly.is_valid:
            poly = make_valid(poly)
    except Exception:
        pass

    minx, miny, maxx, maxy = poly.bounds
    width = maxx - minx
    height = maxy - miny

    return {
        "bounds": {
            "min_x": round(minx, 2),
            "min_y": round(miny, 2),
            "max_x": round(maxx, 2),
            "max_y": round(maxy, 2),
        },
        "width": round(width, 2),
        "height": round(height, 2),
        "area": round(poly.area, 2),
        "perimeter": round(poly.length, 2),
    }

from shapely.geometry import Polygon
from shapely.validation import make_valid

def room_metrics_from_polygon(poly: Polygon):
    """
    Returns bounds, width, height, area, perimeter from a shapely polygon.
    Works for non-rectangular rooms too.
    """
    # Fix invalid polygons if needed
    try:
        if not poly.is_valid:
            poly = make_valid(poly)
    except Exception:
        pass

    minx, miny, maxx, maxy = poly.bounds
    width = maxx - minx
    height = maxy - miny

    return {
        "bounds": {
            "min_x": round(minx, 2),
            "min_y": round(miny, 2),
            "max_x": round(maxx, 2),
            "max_y": round(maxy, 2),
        },
        "width": round(width, 2),
        "height": round(height, 2),
        "area": round(poly.area, 2),
        "perimeter": round(poly.length, 2),
    }

import ezdxf
import numpy as np
from sklearn.cluster import DBSCAN
import json

# ----------------------------
# Helpers
# ----------------------------

def detect_scale_and_eps(furniture_data):
    """eps based on 10% of total furniture spread."""
    if not furniture_data:
        return 25.0
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    width  = np.ptp(coords[:, 0])
    height = np.ptp(coords[:, 1])
    span = max(width, height)
    return max(span * 0.10, 1.0)  # avoid eps = 0

def normalize_furn_for_semantics(t: str) -> str:
    """Unify names so your cluster labeling works."""
    t = (t or "").lower().strip()

    # map your real types to generic keywords for labeling
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

def compute_room_metrics_from_bounds(min_x, min_y, max_x, max_y):
    """Metrics for explanation (rectangle approximation)."""
    w = max_x - min_x
    h = max_y - min_y
    area = w * h
    perimeter = 2 * (w + h)
    return round(w, 2), round(h, 2), round(area, 2), round(perimeter, 2)

def filter_outliers_by_main_bbox(furniture_data, margin=200.0):
    """
    More robust than abs(x)>5000.
    Keeps only items near the main cluster.
    """
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    minx, miny = np.min(coords, axis=0)
    maxx, maxy = np.max(coords, axis=0)

    # If bbox is enormous (outliers exist), we keep only points near the dense region using percentiles
    x1, x2 = np.percentile(coords[:, 0], [5, 95])
    y1, y2 = np.percentile(coords[:, 1], [5, 95])

    filtered = []
    for f in furniture_data:
        x, y = f["centroid"]
        if (x1 - margin) <= x <= (x2 + margin) and (y1 - margin) <= y <= (y2 + margin):
            filtered.append(f)
    return filtered

# ----------------------------
# Main
# ----------------------------

def dxf_to_json_clustered(dxf_path, padding=10.0, min_samples=1):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    furniture_data = []

    # 1) Extract furniture blocks (INSERT)
    for f_ent in msp.query("INSERT"):
        x, y = float(f_ent.dxf.insert.x), float(f_ent.dxf.insert.y)

        # keep raw type + translated type if you want
        raw_name = f_ent.dxf.name
        clean_type = normalize_furniture_name(raw_name)  # your existing function
        sem_type = normalize_furn_for_semantics(clean_type)

        furniture_data.append({
            "id": f"furn_{f_ent.dxf.handle}",
            "type": clean_type,           # keep your normalized type (sink_kitchen, sofa_small...)
            "semantic_type": sem_type,    # extra field for clustering logic (sink, sofa, toilet...)
            "centroid": [x, y]
        })

    if not furniture_data:
        return {"rooms": [], "furniture": []}

    # 2) Filter outliers robustly (fix 64341 / 10334 junk)
    furniture_data = filter_outliers_by_main_bbox(furniture_data, margin=200.0)
    if not furniture_data:
        return {"rooms": [], "furniture": []}

    # 3) Cluster furniture by proximity
    coords = np.array([f['centroid'] for f in furniture_data], dtype=float)
    auto_eps = detect_scale_and_eps(furniture_data) * 1.5
    print(f"📏 Detected scale. Using eps: {auto_eps:.2f}")

    clustering = DBSCAN(eps=auto_eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    # 4) Semantic merge for kitchen (optional)
    # 4) Smart Semantic Merge (Merging multiple clusters of the same room type)
    # تجميع الـ clusters اللي ليهم نفس النوع عشان ما يطلعش 2 Living Room
    type_to_clusters = {
        'bathroom': set(),
        'living_room': set(),
        'kitchen': set()
    }

    # تصنيف الـ clusters الحالية بناءً على العفش اللي جواها
    for i, furn in enumerate(furniture_data):
        label = labels[i]
        if label == -1: continue # تجاهل النويز
        
        sem_t = furn['semantic_type']
        if sem_t == 'toilet':
            type_to_clusters['bathroom'].add(label)
        elif sem_t in ['sink', 'stove', 'refrigerator']:
            type_to_clusters['kitchen'].add(label)
        elif sem_t in ['sofa', 'chair']:
            type_to_clusters['living_room'].add(label)

    # تنفيذ الدمج الفعلي
    new_labels = labels.copy()
    for r_type, cluster_set in type_to_clusters.items():
        if len(cluster_set) > 1:
            main_label = list(cluster_set)[0]
            for other_label in cluster_set:
                new_labels[new_labels == other_label] = main_label
            print(f"🔗 Merged {len(cluster_set)} clusters into one {r_type}.")
    
    labels = new_labels

    # 5) Build room clusters + explanation metrics
    rooms_data = []
    for cluster_id in sorted(set(labels)):
        indices = np.where(labels == cluster_id)[0].tolist()
        room_items = [furniture_data[i] for i in indices]

        room_id = f"room_cluster_{cluster_id}"
        for item in room_items:
            item['room_id'] = room_id

        # Label room based on semantic types (more reliable)
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

        # apply padding
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
            # Explanation fields (what you wanted)
            "width": width,
            "height": height,
            "area": area,
            "perimeter": perimeter,
        })

    # optional: remove semantic_type if you don’t want it in final output
    # for f in furniture_data:
    #     del f["semantic_type"]

    return {"rooms": rooms_data, "furniture": furniture_data}

def apply_with_clamping(delta, original_context, msp, doc):
    for add_item in delta.get("added_ids", []):
        room_id = add_item.get("room_id")
        # البحث عن الأوضة المختارة في الـ context
        room = next((r for r in original_context['rooms'] if r['id'] == room_id), None)
        
        if room:
            b = room['bounds']
            padding = 10 # مسافة أمان من الحوائط
            
            # الإحداثيات اللي الـ AI اقترحها
            suggested_x = float(add_item.get("x", room['centroid'][0]))
            suggested_y = float(add_item.get("y", room['centroid'][1]))

            # 🔥 الـ Clamping: إجبار الإحداثيات تكون جوه حدود الأوضة
            final_x = max(b['min_x'] + padding, min(suggested_x, b['max_x'] - padding))
            final_y = max(b['min_y'] + padding, min(suggested_y, b['max_y'] - padding))

            # إضافة البلوك أو المستطيل
            b_name = add_item.get("type", "sofa_small")
            if b_name in doc.blocks:
                msp.add_blockref(b_name, (final_x, final_y))
            else:
                # رسم Placeholder للتأكد من المكان
                msp.add_lwpolyline([
                    (final_x-5, final_y-5), (final_x+5, final_y-5),
                    (final_x+5, final_y+5), (final_x-5, final_y+5), (final_x-5, final_y-5)
                ], dxfattribs={'color': 1})
                
            print(f"✅ Precision Placement: {b_name} placed at ({final_x}, {final_y}) inside {room_id}")

from ezdxf import bbox
import random
from shapely.geometry import Polygon, Point


BLOCK_MAPPING = {
    "chair": "s2", 
    "sofa": "sofa",
    "table": "st",
    "sink": "ps sin 12",
    "toilet": "toilet",
    "bed": "Cay03_mb"
}

def generate_cad_delta(command, context_json):
    # Vertical Context Map
    room_summary = [f"{r['type']}({r['id']}) Size:[{r.get('width', 0)}x{r.get('height', 0)}]" for r in context_json.get("rooms", [])]
    
    furn_summary = [f"{f['type']}({f['id']}) at {f['centroid']}" for f in context_json.get("furniture", [])]

    for f in context_json.get("furniture", []):
        if f.get("width") is not None and f.get("height") is not None:
            furn_summary.append(
                f"{f['type']}({f['id']}) Size:[{f['width']}x{f['height']}]"
            )
        else:
            furn_summary.append(
                f"{f['type']}({f['id']})"
            )
    context_str = f"ROOMS: {', '.join(room_summary)}\nFURNITURE: {', '.join(furn_summary)}"
    # 2. The EXACT Training Template
    prompt = (
        f"### System:\n"
        f"You are a CAD Assistant. Based on the JSON context, output a 'delta' JSON. "
        f"You MUST use the EXACT 'width' and 'height' from the Context Size:[WxH] "
        f"for 'old_width' and 'old_height'. "
        f"If the user asks to resize (e.g. 50% larger), you MUST compute "
        f"new_width = old_width * scale and new_height = old_height * scale.\n\n"f"### Context:\n{context_str}\n\n"
        f"### User:\n{command}\n\n"
        f"### Assistant:\n"
    )


    inputs = tokenizer(prompt, return_tensors="pt")
    model.eval()
    
    with torch.no_grad():
        output_tokens = model.generate(
            **inputs, max_new_tokens=512, temperature=0.1, 
            do_sample=False, repetition_penalty=1.2
        )
    result = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    
    # 3. Extraction Logic
    # We split by '### Assistant:' to get ONLY what the model generated
    json_part = result.split("### Assistant:")[-1].strip()
    
    # Standardize those pesky quotes
    json_part = json_part.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")

    print("--- AI RESPONSE ---")
    print(json_part)
    
    try:
        return json.loads(json_part)
    except Exception as e:
        # Final fallback: find the JSON boundaries manually
        try:
            start = json_part.find("{")
            end = json_part.rfind("}") + 1
            return json.loads(json_part[start:end])
        except:
            print(f"❌ Failed to parse: {e}")
            return None
        
def get_plan_anchor_from_furniture(context):
    furn = context.get("furniture", [])
    valid = [f for f in furn if abs(f["centroid"][0]) < 5000 and abs(f["centroid"][1]) < 5000]
    if not valid:
        return (0.0, 0.0), (0.0, 0.0, 0.0, 0.0)

    xs = [f["centroid"][0] for f in valid]
    ys = [f["centroid"][1] for f in valid]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    return (cx, cy), (minx, miny, maxx, maxy)
def find_best_block_name(doc, requested_type):
    """
    Try to map a clean type (sofa_small) to an existing DXF block name.
    Returns best matching block name or None.
    """
    req = (requested_type or "").lower().strip()

    # 1) direct hit
    for b in doc.blocks:
        if b.name.lower() == req:
            return b.name

    # 2) synonyms → search
    synonyms = {
        "sofa_small": ["sofa", "s2", "sofa-46", "sofa_46", "sofa46"],
        "sofa_large": ["sofa", "sofa-50", "sofa_50", "sofa50"],
        "sofa_loveseat": ["s2", "sofa", "love", "loveseat"],
        "sofa": ["sofa", "s2"],
        "chair_modern": ["cay03", "cay03_mb", "chair"],
        "dining_table_set": ["table", "dsadas"],
        "sink_kitchen": ["sin", "ps sin 12", "sink"],
        "toilet": ["toilet", "wc"],
    }

    candidates = synonyms.get(req, [req])

    block_names = [b.name for b in doc.blocks]
    block_names_low = [n.lower() for n in block_names]

    # 3) contains match
    for cand in candidates:
        cand = cand.lower()
        for i, bn in enumerate(block_names_low):
            if cand in bn:
                return block_names[i]

    return None

import ezdxf
from ezdxf import bbox

def apply_changes_to_dxf(original_dxf, delta_output, output_dxf, original_context):
    doc = ezdxf.readfile(original_dxf)
    msp = doc.modelspace()
    delta = delta_output.get("delta", delta_output)
    furniture_list = original_context.get('furniture', [])

    # دالة داخلية ذكية لإيجاد الـ ID الحقيقي
    def find_real_id(input_id):
        if "_" not in input_id:
            match = next((f for f in furniture_list if f['type'] == input_id), None)
            return match['id'] if match else input_id
        return input_id
        
    # --- 1. تنفيذ الـ Add (نسخة الـ Clusters الذكية) ---
    for add_item in delta.get("added_ids", []) + delta.get("added", []):
        try:
            b_name = add_item.get("block_name") or add_item.get("type")
            # Mapping للأسماء لو الـ AI بعت اسم عام
            if b_name == "sofa": b_name = "sofa_small"
            
            # تحديد الإحداثيات
            target_room_id = add_item.get("room_id")
            # بنجيب بيانات الأوضة من الـ clusters اللي بعتناها للـ AI
            target_room = next((r for r in original_context.get('rooms', []) if r['id'] == target_room_id), None)
            
            if not target_room:
                # لو الـ AI منساش النوع بس نسي الـ ID، هندور بالنوع
                target_type = "living_room" if "sofa" in b_name else "bathroom" if "toilet" in b_name else None
                target_room = next((r for r in original_context.get('rooms', []) if r['type'] == target_type), None)

            if target_room:
                pos_x, pos_y = target_room['centroid']
                print(f"📍 Smart Placement: Putting {b_name} in {target_room['type']} ({target_room['id']})")
            else:
                # لو ملقاش خالص، يروح لأول أوضة وخلاص
                target_room = original_context.get('rooms', [{}])[0]
                pos_x, pos_y = target_room.get('centroid', [0,0])

            # الإضافة الفعلية للبلوك
            if b_name in doc.blocks:
                new_item = msp.add_blockref(b_name, (pos_x, pos_y))
                print(f"✨ Added {b_name} successfully!")
            else:
                # Placeholder لو البلوك مش موجود (المستطيل الأحمر)
                print(f"📦 Block {b_name} not found, drawing placeholder.")
                msp.add_lwpolyline([
                    (pos_x-5, pos_y-5), (pos_x+5, pos_y-5), 
                    (pos_x+5, pos_y+5), (pos_x-5, pos_y+5), (pos_x-5, pos_y-5)
                ], dxfattribs={'color': 1})
        except Exception as e:
            print(f"⚠️ Add error: {e}")

    # --- 2. تنفيذ الـ Resize (مع تصحيح الـ Recentering) ---
    for resize in delta.get("resized", []):
        target_id = find_real_id(resize.get("id"))
        try:
            handle = target_id.split("_")[-1]
            entity = doc.entitydb.get(handle)
            if entity and entity.dxftype() == "INSERT":
                # حساب الـ Scale Factor
                new_w = float(resize.get("new_width", 1.0))
                # بنجيب العرض الحقيقي من الـ context أو الـ bbox بدل الـ 0.01 بتاعة الـ AI
                bbox_before = bbox.extents([entity])
                if bbox_before.has_data:
                    current_w = bbox_before.size.x
                    # لو الـ AI بعت عرض 2 متر، بنقسمه على العرض الحالي
                    scale_factor = new_w / current_w if current_w > 0 else 1.0
                    
                    center_before = bbox_before.center
                    
                    # Apply Scaling
                    entity.dxf.xscale *= scale_factor
                    entity.dxf.yscale *= scale_factor
                    
                    # Recenter logic
                    bbox_after = bbox.extents([entity])
                    center_after = bbox_after.center
                    entity.dxf.insert = (
                        entity.dxf.insert.x - (center_after.x - center_before.x),
                        entity.dxf.insert.y - (center_after.y - center_before.y),
                        entity.dxf.insert.z
                    )
                    print(f"📏 Resized {target_id} to width {new_w}")
        except Exception as e:
            print(f"⚠️ Resize Error for {target_id}: {e}")


    # 2. منطق التحريك (Moves)
    for move in delta.get("moved", []):
        target_id = move.get("id")
        
        # ربط الـ النوع بالـ ID الحقيقي لو الـ AI بعت "toilet" بس
        real_id = target_id
        if "_" not in target_id:
            match = next((f for f in original_context.get('furniture', []) if f['type'] == target_id), None)
            if match:
                real_id = match['id']
                print(f"🔗 Mapped '{target_id}' to real ID: {real_id}")

        try:
            handle = real_id.split("_")[-1] 
            entity = doc.entitydb.get(handle)
            
            if entity:
                dx, dy = float(move.get("dx", 0)), float(move.get("dy", 0))
                
                # لو بلوك (INSERT)
                if hasattr(entity.dxf, 'insert'):
                    old_pos = entity.dxf.insert
                    entity.dxf.insert = (old_pos.x + dx, old_pos.y + dy, old_pos.z)
                # لو خطوط أو بولي لاين
                else:
                    entity.translate(dx, dy, 0)
                    
                print(f"✅ Moved {real_id} by {dx}, {dy}")
        except Exception as e: # الـ except دي كانت ناقصة
            print(f"⚠️ Error moving {real_id}: {e}")
    # --- 3. تنفيذ الـ Delete ---
    for item_id in delta.get("removed_ids", []):
        target_id = find_real_id(item_id)
        try:
            handle = target_id.split("_")[-1]
            entity = doc.entitydb.get(handle)
            if entity:
                msp.delete_entity(entity)
                print(f"🗑️ Deleted {target_id}")
        except: pass

    doc.saveas(output_dxf)
    print(f"💾 Processed file saved as: {output_dxf}")


import requests
import json
import ezdxf
# تأكدي إن كل الدوال اللي بعتيهالي (dxf_to_json_clustered, normalize_furniture_name, etc.) موجودة في نفس الملف

# 1. إعدادات المسارات واللينك
KAGGLE_API_URL = "https://kennedy-footed-epexegetically.ngrok-free.dev/process"
INPUT_DXF = "C:\\Users\\Hassan Hatem\\Downloads\\Drawing 1.dxf"  # اسم ملفك
OUTPUT_DXF = "floorplan_edited.dxf"

def run_ai_edit(user_command):
    # 2. استخراج الـ Context الحقيقي من ملف الـ DXF
    print("🔍 Analyzing DXF file...")
    try:
        context = dxf_to_json_clustered(INPUT_DXF)
    except Exception as e:
        print(f"❌ Error reading DXF: {e}")
        return

    # 3. إرسال البيانات لكاجل
    payload = {
        "command": user_command,
        "context": context
    }
    
    print(f"🧠 Asking AI to: '{user_command}'...")
    response = requests.post(KAGGLE_API_URL, json=payload)
    
    if response.status_code == 200:
        res_data = response.json()
        if res_data.get("success"):
            delta = res_data["delta"]
            print(f"✨ AI Decision: {json.dumps(delta, indent=2)}")
            
            # 4. تطبيق التعديلات فوراً على الملف
            print("💾 Applying changes to DXF...")
            apply_changes_to_dxf(INPUT_DXF, delta, OUTPUT_DXF, context)
            print(f"🎉 Done! Saved to {OUTPUT_DXF}")
        else:
            print(f"⚠️ AI Error: {res_data.get('error')}")
    else:
        print(f"🌐 Connection Error: {response.status_code}")

# --- جربي التشغيل الآن ---
if __name__ == "__main__":
    command = input(" Move the toilet 100 units left ")
    run_ai_edit(command)