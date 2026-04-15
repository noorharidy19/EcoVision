
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Polygon
from typing import Dict, Any













"""
EcoVision - DXF Parser v10
==========================================
All configuration loaded from config.json — no hard-coded data.
"""

import ezdxf
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

# ─────────────────────────────────────────────
# 0. LOAD CONFIG
# ─────────────────────────────────────────────

_CFG_PATH = Path(__file__).parent / "config.json"
with open(_CFG_PATH, "r") as _f:
    CFG = json.load(_f)

CITY_CLIMATE             = CFG["city_climate"]
CIRCULATION_ROOMS        = CFG["room_categories"]["circulation"]
HIGH_USE_ROOMS           = CFG["room_categories"]["high_use"]
ROOM_KEYWORDS            = CFG["room_categories"]["keywords"]
SKIP_LAYER_KEYWORDS      = CFG["dxf"]["skip_layer_keywords"]
MULTI_WINDOW_AREA_M2     = CFG["dxf"]["multi_window_area_m2"]
DIM_SEARCH_RADIUS        = CFG["dxf"]["dim_search_radius_m"]
DIM_WIDTH_MIN_MM         = CFG["dxf"]["dim_width_min_mm"]
DIM_WIDTH_MAX_MM         = CFG["dxf"]["dim_width_max_mm"]
DEFAULT_WINDOW_HEIGHT_MM = CFG["dxf"]["default_window_height_mm"]
WINDOW_RATINGS           = CFG["window_ratings"]


# ─────────────────────────────────────────────
# 1. HELPERS
# ─────────────────────────────────────────────

def get_climate(city):
    return CITY_CLIMATE.get(city, "hot_dry")

def is_high_use(name):
    return any(h in name.lower() for h in HIGH_USE_ROOMS)

def is_circulation(name):
    return any(c in name.lower() for c in CIRCULATION_ROOMS)


# ─────────────────────────────────────────────
# 2. BUILDING BOUNDS + UNIT AUTO-DETECT
# ─────────────────────────────────────────────

def get_building_bounds(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    all_x, all_y = [], []

    for e in msp:
        try:
            if e.dxftype() == "LINE":
                all_x += [e.dxf.start.x, e.dxf.end.x]
                all_y += [e.dxf.start.y, e.dxf.end.y]
            elif e.dxftype() == "LWPOLYLINE":
                for pt in e.get_points():
                    all_x.append(pt[0]); all_y.append(pt[1])
        except:
            continue

    if not all_x:
        return (-10, 10, -15, 0, "M", 0.30)

    all_x.sort(); all_y.sort()
    n     = len(all_x)
    min_x = all_x[int(n * 0.05)]; max_x = all_x[int(n * 0.95)]
    min_y = all_y[int(n * 0.05)]; max_y = all_y[int(n * 0.95)]
    width = max_x - min_x

    if width < 500:
        unit_scale, dedup = "M",  0.30
    elif width < 5000:
        unit_scale, dedup = "CM", 30.0
    else:
        unit_scale, dedup = "MM", 300.0

    print(f"✅ Bounds: X({min_x:.3f}→{max_x:.3f}) Y({min_y:.3f}→{max_y:.3f})"
          f"  unit={unit_scale}  dedup={dedup}")
    return (min_x, max_x, min_y, max_y, unit_scale, dedup)


# ─────────────────────────────────────────────
# 3. WINDOW DIRECTION
# ─────────────────────────────────────────────

# All 8 compass points in clockwise order
_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
 
_NORTH_ARROW_OFFSET = {  # ← RENAMED from _FACING_OFFSET
    "N":  0, "NE": 1, "E": 2, "SE": 3,
    "S":  4, "SW": 5, "W": 6, "NW": 7,
}

def get_window_direction(rotation, x, y, min_x, max_x, min_y, max_y):
    rot = rotation % 360
    if rot < 45 or (135 < rot < 225) or rot > 315:
        return "N" if abs(y - max_y) < abs(y - min_y) else "S"
    else:
        return "W" if abs(x - min_x) < abs(x - max_x) else "E"

def apply_north_arrow_direction(direction: str, north_arrow_direction: str) -> str:  # ← RENAMED from apply_building_facing
    """
    Rotate a drawing direction to real-world direction based on north_arrow_direction.
 
    The drawing always assumes north = top of page.
    If the north arrow actually points East, then what the drawing calls North
    is really East in real life — so all directions shift by the arrow offset.
 
    Example:
        drawing says "N", north_arrow_direction="E" → real direction is "E"
        drawing says "E", north_arrow_direction="E" → real direction is "S"
        drawing says "W", north_arrow_direction="NW" → real direction is "SW"
    """
    offset = _NORTH_ARROW_OFFSET.get(north_arrow_direction.upper(), 0)
    if offset == 0:
        return direction  # building faces true North — no rotation needed
    if direction not in _DIRECTIONS:
        return direction  # unknown/none — leave as-is
    idx = _DIRECTIONS.index(direction)
    return _DIRECTIONS[(idx + offset) % 8]
 

# ─────────────────────────────────────────────
# 4A. DIMENSION-BASED WIDTH INDEX
# ─────────────────────────────────────────────

def extract_dimension_widths(dxf_path):
    doc  = ezdxf.readfile(dxf_path)
    msp  = doc.modelspace()
    hits = []

    for e in msp:
        if e.dxftype() != "DIMENSION":
            continue
        try:
            val = e.dxf.actual_measurement
            if val is None:
                continue
            val_mm = round(val)
            if not (DIM_WIDTH_MIN_MM <= val_mm <= DIM_WIDTH_MAX_MM):
                continue
            defpt = e.dxf.defpoint3
            hits.append({"x": defpt.x, "y": defpt.y, "width_mm": val_mm})
        except Exception:
            continue

    print(f"   📐 DIMENSION index: {len(hits)} entries in valid width range")
    return hits


def find_nearby_dim_width(wx, wy, dim_index, radius=None):
    radius = radius or DIM_SEARCH_RADIUS
    best_dist  = radius
    best_width = None
    for entry in dim_index:
        dist = math.hypot(wx - entry["x"], wy - entry["y"])
        if dist < best_dist:
            best_dist  = dist
            best_width = entry["width_mm"]
    return best_width


# ─────────────────────────────────────────────
# 4B. EXTRACT WINDOWS
# ─────────────────────────────────────────────

_MTEXT_CTRL = re.compile(
    r'\\[A-Za-z][\d.+-]*;?|\\[pPnNtT~{}\\|]|\{[^}]*\}|%%[A-Za-z0-9]+'
)

def _clean_mtext(raw):
    return re.sub(r'\s+', ' ', _MTEXT_CTRL.sub(' ', raw)).strip()


def get_block_dimensions(doc, block_name, x_scale=1.0, y_scale=1.0, _visited=None):
    if _visited is None:
        _visited = set()
    if block_name in _visited:
        return None, None
    _visited.add(block_name)

    try:
        blk = doc.blocks[block_name]
        xs, ys = [], []

        for e in blk:
            if e.dxftype() == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif e.dxftype() == "LWPOLYLINE":
                for pt in e.get_points():
                    xs.append(pt[0]); ys.append(pt[1])
            elif e.dxftype() == "ARC":
                cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
            elif e.dxftype() == "INSERT":
                nested_name = e.dxf.name
                n_xsc = getattr(e.dxf, 'xscale', 1.0)
                n_ysc = getattr(e.dxf, 'yscale', 1.0)
                n_x   = e.dxf.insert.x
                n_y   = e.dxf.insert.y
                nw, nh = get_block_dimensions(doc, nested_name, n_xsc, n_ysc, _visited)
                if nw is not None:
                    xs += [n_x, n_x + nw]; ys += [n_y, n_y + nh]

        if not xs:
            return None, None

        width  = (max(xs) - min(xs)) * abs(x_scale)
        height = (max(ys) - min(ys)) * abs(y_scale)
        return width, height
    except Exception:
        return None, None


def dims_to_mm(width, height, unit_scale):
    if width is None:
        return None, None
    factor = {"M": 1000.0, "CM": 10.0, "MM": 1.0}.get(unit_scale, 1000.0)
    w_mm = round(width  * factor) if width  is not None else None
    h_mm = round(height * factor) if height is not None else None
    return w_mm, h_mm


def extract_window_size(name):
    u = name.upper()
    m = re.search(r'W[.\-](\d+)', u)
    if m: return int(m.group(1))
    m = re.search(r'[.\-_](\d{3,4})$', u)
    if m: return int(m.group(1))
    return None


def is_real_window_layer(layer):
    lu = layer.upper()
    return "A-WIN" in lu and not any(sk in lu for sk in SKIP_LAYER_KEYWORDS)


def extract_windows(dxf_path, min_x, max_x, min_y, max_y, dedup, unit_scale, north_arrow_direction):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    dim_index = extract_dimension_widths(dxf_path)
    windows   = []
    seen_pos  = []

    for e in msp:
        layer = e.dxf.layer if hasattr(e.dxf, 'layer') else ""
        if e.dxftype() in ("INSERT", "LWPOLYLINE", "POLYLINE"):
            if not is_real_window_layer(layer): continue
        else:
            continue

        try:
            if e.dxftype() == "INSERT":
                x       = e.dxf.insert.x
                y       = e.dxf.insert.y
                rot     = getattr(e.dxf, 'rotation', 0)
                name    = e.dxf.name
                x_scale = getattr(e.dxf, 'xscale', 1.0)
                y_scale = getattr(e.dxf, 'yscale', 1.0)

                width_mm  = extract_window_size(name)
                height_mm = None

                if width_mm is None:
                    raw_w, raw_h = get_block_dimensions(doc, name, x_scale, y_scale)
                    width_mm, height_mm = dims_to_mm(raw_w, raw_h, unit_scale)
                else:
                    _, raw_h = get_block_dimensions(doc, name, x_scale, y_scale)
                    _, height_mm = dims_to_mm(None, raw_h, unit_scale)

                if width_mm is None:
                    dim_w = find_nearby_dim_width(x, y, dim_index)
                    if dim_w is not None:
                        width_mm = dim_w
                        print(f"   📐 DIM fallback (INSERT): ({x:.3f},{y:.3f}) → width={dim_w}mm")

            else:
                pts  = list(e.get_points())
                x    = sum(p[0] for p in pts) / len(pts)
                y    = sum(p[1] for p in pts) / len(pts)
                rot  = 0
                name = "WIN_POLY"
                width_mm  = None
                height_mm = None

                dim_w = find_nearby_dim_width(x, y, dim_index)
                if dim_w is not None:
                    width_mm = dim_w
                    print(f"   📐 DIM fallback (POLY): ({x:.3f},{y:.3f}) → width={dim_w}mm")

            if height_mm is None:
                height_mm = DEFAULT_WINDOW_HEIGHT_MM
                print(f"   📏 Default height applied: ({x:.3f},{y:.3f}) → height={DEFAULT_WINDOW_HEIGHT_MM}mm")

            margin = dedup * 0.5
            if not (min_x - margin <= x <= max_x + margin and
                    min_y - margin <= y <= max_y + margin):
                continue

            if any(math.hypot(x - px, y - py) < dedup for px, py in seen_pos):
                print(f"   ⚠️  Dup ({x:.3f},{y:.3f}) skipped")
                continue
            seen_pos.append((x, y))

            raw_direction  = get_window_direction(rot, x, y, min_x, max_x, min_y, max_y)
            direction = apply_north_arrow_direction(raw_direction, north_arrow_direction)  

            if direction != raw_direction:
                print(f"   🧭 Direction rotated: {raw_direction} → {direction} (north arrow points {north_arrow_direction})")

            windows.append({
                "x": x, "y": y, "rotation": rot,
                "direction": direction,
                "width_mm":  width_mm,
                "height_mm": height_mm,
                "name": name, "layer": layer,
            })
        except Exception:
            continue

    print(f"\n✅ Extracted {len(windows)} windows")
    for w in windows:
        w_str = f"{w['width_mm']}mm"  if w['width_mm']  else "⚠️ width unknown"
        h_str = f"{w['height_mm']}mm" if w['height_mm'] else "⚠️ height unknown"
        print(f"   🪟 ({w['x']:.3f},{w['y']:.3f}) rot={w['rotation']}°"
              f" → {w['direction']}  w={w_str}  h={h_str}")
    return windows


# ─────────────────────────────────────────────
# 5. EXTRACT DOORS
# ─────────────────────────────────────────────

def extract_doors(dxf_path, dedup):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    doors = []; seen_pos = []

    for e in msp:
        if e.dxftype() != "INSERT": continue
        layer = e.dxf.layer.upper()
        name  = e.dxf.name.upper() if hasattr(e.dxf, 'name') else ""
        if any(sk in layer for sk in ["ORIGINAL", "ROOF", "FRAME"]): continue
        if not any(k in layer for k in ["DOOR", "$A-DO", "DOORS"]) and \
           not any(k in name  for k in ["DOOR", "DOORS"]): continue
        try:
            x = e.dxf.insert.x; y = e.dxf.insert.y
            if any(math.hypot(x - px, y - py) < dedup for px, py in seen_pos):
                continue
            seen_pos.append((x, y))
            doors.append({"x": x, "y": y, "rotation": getattr(e.dxf, 'rotation', 0)})
        except:
            continue

    print(f"✅ Extracted {len(doors)} doors")
    return doors


# ─────────────────────────────────────────────
# 6. ASSIGN WINDOWS TO ROOMS
# ─────────────────────────────────────────────

def assign_windows_to_rooms(windows, room_labels, unit_scale):
    valid_rooms  = [r for r in room_labels if r.get("x") is not None]
    room_windows = {r["name"]: [] for r in room_labels}

    def d2(w, r):
        return math.hypot(w["x"] - r["x"], w["y"] - r["y"])

    pairs = sorted(
        [(d2(w, r), w, r) for w in windows for r in valid_rooms],
        key=lambda t: t[0]
    )

    assigned_wids = set()
    room_count    = defaultdict(int)

    for dist, w, r in pairs:
        wid = id(w); rname = r["name"]; rarea = r.get("area_m2", 9.0)
        if wid in assigned_wids: continue
        if room_count[rname] >= 1 and rarea < MULTI_WINDOW_AREA_M2: continue
        room_windows[rname].append(w)
        assigned_wids.add(wid); room_count[rname] += 1
        print(f"   [P1] Win({w['x']:.3f},{w['y']:.3f}) dir={w['direction']}"
              f" → {rname}  dist={dist:.3f}")

    for dist, w, r in pairs:
        wid = id(w); rname = r["name"]; rarea = r.get("area_m2", 9.0)
        if wid in assigned_wids: continue
        if rarea < MULTI_WINDOW_AREA_M2: continue
        room_windows[rname].append(w)
        assigned_wids.add(wid); room_count[rname] += 1
        print(f"   [P2-extra] Win({w['x']:.3f},{w['y']:.3f}) dir={w['direction']}"
              f" → {rname}  dist={dist:.3f}")

    for w in windows:
        if id(w) not in assigned_wids:
            print(f"   [unassigned] Win({w['x']:.3f},{w['y']:.3f})"
                  f" dir={w['direction']} — not in any submitted room")

    return room_windows


# ─────────────────────────────────────────────
# 7. EXTRACT TEXT LABELS
# ─────────────────────────────────────────────

def extract_text_labels(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    labels = []
    for e in msp:
        try:
            if e.dxftype() == "TEXT":
                text = e.dxf.text.strip()
            elif e.dxftype() == "MTEXT":
                try:
                    text = e.plain_mtext().strip()
                except AttributeError:
                    text = _clean_mtext(e.text)
                text = _clean_mtext(text)
            else:
                continue
            x = e.dxf.insert.x; y = e.dxf.insert.y
            if text:
                labels.append({"text": text, "x": x, "y": y})
        except:
            continue
    return labels


# ─────────────────────────────────────────────
# 8. MATCH ROOMS TO DXF LABELS
# ─────────────────────────────────────────────

def _normalize(s):
    s = unicodedata.normalize("NFD", s.upper())
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_rooms_to_labels(form_rooms, text_labels):
    label_groups = {}
    for label in text_labels:
        raw = label["text"].strip()
        if not raw or not any(k in raw.upper() for k in ROOM_KEYWORDS):
            continue
        norm = _normalize(raw)
        if norm not in label_groups:
            label_groups[norm] = []
        label_groups[norm].append({"x": label["x"], "y": label["y"], "raw": raw})

    for key in label_groups:
        label_groups[key].sort(key=lambda l: l["y"], reverse=True)
    label_usage = {k: 0 for k in label_groups}

    print(f"\n📝 DXF room labels ({len(label_groups)}):")
    for k, v in label_groups.items():
        print(f"   '{v[0]['raw']}' norm='{k}' ({len(v)}×)")

    sorted_rooms = sorted(form_rooms, key=lambda r: len(r["name"]), reverse=True)
    room_labels  = []

    for fr in sorted_rooms:
        name    = fr["name"].strip()
        area    = float(fr.get("area", 9.0))
        name_up = _normalize(name)
        base    = re.sub(r'\s*\d+\s*$', '', name_up).strip()
        room_x = room_y = matched_key = None

        for key in label_groups:
            if base == key or name_up == key:
                idx = label_usage[key]
                if idx < len(label_groups[key]):
                    pos = label_groups[key][idx]
                    room_x, room_y = pos["x"], pos["y"]
                    label_usage[key] += 1; matched_key = key; break

        if room_x is None:
            bw = set(base.split())
            for key in label_groups:
                kw = set(key.split())
                if bw and kw and (bw <= kw or kw <= bw):
                    idx = label_usage[key]
                    if idx < len(label_groups[key]):
                        pos = label_groups[key][idx]
                        room_x, room_y = pos["x"], pos["y"]
                        label_usage[key] += 1; matched_key = key; break

        if room_x is None:
            bw_parts = base.split()
            for key in label_groups:
                if all(w in key for w in bw_parts) or \
                   all(w in base for w in key.split()):
                    idx = label_usage[key]
                    if idx < len(label_groups[key]):
                        pos = label_groups[key][idx]
                        room_x, room_y = pos["x"], pos["y"]
                        label_usage[key] += 1; matched_key = key; break

        if room_x is None:
            print(f"   ⚠️  NO MATCH for '{name}' — available: {list(label_groups.keys())}")

        room_labels.append({
            "name": name, "x": room_x, "y": room_y,
            "area_m2": area, "high_use": is_high_use(name),
            "label_matched": room_x is not None,
            "matched_key": matched_key,
        })

    name_order = [r["name"] for r in form_rooms]
    room_labels.sort(key=lambda r: name_order.index(r["name"]))
    return room_labels


# ─────────────────────────────────────────────
# 9. RATINGS
# ─────────────────────────────────────────────

def get_window_rating(window_dir, room_name):
    if not window_dir or window_dir in ["none", "unknown"]:
        return "no_window"

    wd   = window_dir.upper()
    name = room_name.lower()

    for room_type, rules in WINDOW_RATINGS.items():
        if room_type in name:
            if wd in rules.get("good", []):       return "good"
            if wd in rules.get("acceptable", []): return "acceptable"
            return "poor"

    return "acceptable"


# ─────────────────────────────────────────────
# 10. MAIN
# ─────────────────────────────────────────────

def extract_features(dxf_path, city, north_arrow_direction, form_rooms):
    print(f"\n🔍 Parsing: {dxf_path}")
    try:
        ezdxf.readfile(dxf_path)
        print("✅ DXF valid")
    except Exception as e:
        return {"error": f"Invalid DXF: {e}"}

    city            = city.strip().title()
    north_arrow_direction = north_arrow_direction.strip().upper()
    climate         = get_climate(city)

    min_x, max_x, min_y, max_y, unit_scale, dedup = get_building_bounds(dxf_path)
    windows = extract_windows(dxf_path, min_x, max_x, min_y, max_y, dedup, unit_scale, north_arrow_direction)
    doors   = extract_doors(dxf_path, dedup)

    text_labels = extract_text_labels(dxf_path)
    if not text_labels:
        print("⚠️  WARNING: No text labels found in DXF — room matching will fail")

    print(f"\n🔗 Matching rooms...")
    room_labels = match_rooms_to_labels(form_rooms, text_labels)
    for rl in room_labels:
        pos = f"({rl['x']:.3f},{rl['y']:.3f})" if rl['x'] is not None else "NOT MATCHED"
        print(f"   '{rl['name']}' → {pos}")

    print(f"\n🪟 Assigning windows...")
    room_windows = assign_windows_to_rooms(windows, room_labels, unit_scale)

    processed_rooms = []
    for room in form_rooms:
        name = room["name"].strip()
        area = float(room["area"])
        wins         = room_windows.get(name, [])
        win_dirs     = [w["direction"] for w in wins]
        main_win_dir = max(set(win_dirs), key=win_dirs.count) if win_dirs else "none"
        orientation  = main_win_dir if main_win_dir != "none" else "unknown"
        win_rating   = get_window_rating(main_win_dir, name)
        window_dimensions = [
            {"width_mm": w.get("width_mm"), "height_mm": w.get("height_mm")}
            for w in wins
        ]

        print(f"   '{name}' → {win_dirs} → main:{main_win_dir}"
              f"  dims:{[(d['width_mm'], d['height_mm']) for d in window_dimensions]}")

        processed_rooms.append({
            "name":                    name,
            "area_m2":                 area,
            "orientation":             orientation,
            "window_direction":        main_win_dir,
            "all_window_directions":   win_dirs,
            "window_count":            len(wins),
            "window_dimensions":       window_dimensions,
            "window_direction_rating": win_rating,
            "is_high_use":             is_high_use(name),
            "is_circulation":          is_circulation(name),
        })

    total_area     = sum(r["area_m2"] for r in processed_rooms)
    corridor_area  = sum(r["area_m2"] for r in processed_rooms if r["is_circulation"])
    corridor_ratio = round(corridor_area / total_area, 2) if total_area else 0
    bad_windows = sum(1 for r in processed_rooms
                      if r["window_direction_rating"] == "poor")

    return {
        "city":                    city,
        "climate":                 climate,
        "north_arrow_direction":   north_arrow_direction,
        "dxf_unit_scale":          unit_scale,
        "total_floor_area_m2":     total_area,
        "corridor_area_ratio":     corridor_ratio,
        "num_rooms":               len(processed_rooms),
        "poorly_oriented_windows": bad_windows,
        "total_windows":           len(windows),
        "total_doors":             len(doors),
        "rooms":                   processed_rooms,
    }
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
