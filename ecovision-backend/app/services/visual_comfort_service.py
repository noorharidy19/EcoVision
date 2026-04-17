import math
import joblib
import numpy as np
from pathlib import Path

# ── Model paths ────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "visual_comfort_models"

_model   = None
_scaler  = None
_encoder = None
_feat_cols = None

def _load_models():
    global _model, _scaler, _encoder, _feat_cols
    if _model is None:
        _model     = joblib.load(MODEL_DIR / "visual_comfort_rf.pkl")
        _scaler    = joblib.load(MODEL_DIR / "scaler.pkl")
        _encoder   = joblib.load(MODEL_DIR / "label_encoder.pkl")
        _feat_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")


# ── Unit normalization ─────────────────────────────────────────────
def _normalize_window_area(raw_area: float, floor_area: float) -> float:
    if floor_area <= 0 or raw_area <= 0:
        return 0
    for scale in [1, 1e-2, 1e-4, 1e-6]:
        scaled = raw_area * scale
        if 0.01 <= (scaled / floor_area) <= 0.85:
            return scaled
    return floor_area * 0.10


# ── Physics functions ──────────────────────────────────────────────
def _calculate_lux(window_area_m2: float, room_area_m2: float,
                   ceiling_height: float = 2.7) -> float:
    if room_area_m2 <= 0 or window_area_m2 <= 0:
        return 0
    depth_factor = min(1.0, (2.5 * ceiling_height) / math.sqrt(room_area_m2))
    df = min((window_area_m2 * 0.7 * 0.7 * depth_factor) / room_area_m2, 0.25)
    return round(df * 10000, 2)


def _calculate_dgi(window_area_m2: float, lux: float) -> float:
    if window_area_m2 <= 0 or lux <= 0:
        return 0
    sky_lum = 4000
    bg_lum  = max(50, lux * 0.08)
    omega   = min(window_area_m2 / 4.0, 0.5)
    try:
        num = (sky_lum ** 1.6) * (omega ** 0.8)
        den = bg_lum + 0.07 * (omega ** 0.5) * sky_lum
        return round(max(0, min(10 * math.log10(num / den), 40)), 2)
    except (ValueError, ZeroDivisionError):
        return 0


def _calculate_cct(wwr: float) -> float:
    if wwr <= 0:
        return 4000
    return round(min(3500 + (wwr / 0.40) * 2500, 6500), 0)


def _calculate_view_score(num_windows: int, num_rooms: int,
                           total_window_area_m2: float,
                           total_area_m2: float) -> float:
    if num_rooms == 0 or total_area_m2 <= 0:
        return 0
    score = min((num_windows / num_rooms) / 2.0, 1.0) * 40
    avg_win = total_window_area_m2 / num_windows if num_windows > 0 else 0
    score  += min(avg_win / 1.5, 1.0) * 35
    wfr = total_window_area_m2 / total_area_m2
    if 0.15 <= wfr <= 0.30:
        wfr_score = 1.0
    elif wfr < 0.15:
        wfr_score = wfr / 0.15
    else:
        wfr_score = max(0, 1 - (wfr - 0.30) / 0.30)
    score += wfr_score * 25
    return round(min(score, 100), 2)


# ── Status helpers ─────────────────────────────────────────────────
def _lux_status(lux):
    if 300 <= lux <= 500:  return "Optimal (300–500 lux target)"
    if 150 <= lux < 300:   return "Slightly Low (target: 300–500 lux)"
    if 500 < lux <= 750:   return "Slightly High (minor glare risk)"
    if lux < 150:          return "Too Low — insufficient daylight"
    return "Too High — glare likely"

def _dgi_status(dgi):
    if dgi < 18:  return "Imperceptible glare"
    if dgi < 24:  return "Perceptible but acceptable"
    if dgi < 28:  return "Uncomfortable glare"
    return "Intolerable glare"

def _cct_status(cct):
    if 3000 <= cct <= 5000: return "Comfortable (Kruithof comfort zone)"
    if cct < 3000:          return "Very warm — may feel dim"
    if 5000 < cct <= 6000:  return "Slightly cool — neutral daylight"
    return "Very cool/blue — may feel clinical"

def _view_status(score):
    if score >= 70: return "Excellent view access (WELL compliant)"
    if score >= 40: return "Adequate view access"
    return "Poor view access — insufficient window coverage"


# ── Comfort percentage ─────────────────────────────────────────────
_CLASS_RANGES = {"Poor": (5, 33), "Acceptable": (34, 66), "Good": (67, 95)}

def _comfort_percentage(predicted_class, probabilities, class_names):
    prob_dict = dict(zip(class_names, probabilities))
    low, high = _CLASS_RANGES.get(predicted_class, (34, 66))
    confidence = prob_dict.get(predicted_class, 0.5)
    base = low + confidence * (high - low)
    score = base + prob_dict.get("Good", 0) * 10 - prob_dict.get("Poor", 0) * 10
    return round(min(max(score, 1), 99), 1)


# ── Analysis text ──────────────────────────────────────────────────
def _generate_analysis(lux, dgi, cct, view_score, predicted_class):
    lines = []
    summaries = {
        "Good":       "This floor plan demonstrates good visual comfort. "
                      "Daylight levels and glare conditions are within acceptable ranges.",
        "Acceptable": "This floor plan has acceptable but improvable visual comfort. "
                      "Some criteria fall outside optimal ranges.",
        "Poor":       "This floor plan has poor visual comfort. "
                      "Multiple criteria are outside acceptable ranges. "
                      "Design changes are recommended."
    }
    lines.append(summaries.get(predicted_class, ""))

    if lux < 150:
        lines.append(f"Light intensity is critically low at {lux:.0f} lux "
                     "(target: 300–500 lux per EN 12464-1). "
                     "Consider increasing window area or adding skylights.")
    elif lux > 750:
        lines.append(f"Light intensity is high at {lux:.0f} lux — "
                     "this increases glare risk. External shading is recommended.")
    else:
        lines.append(f"Light intensity of {lux:.0f} lux is within acceptable range "
                     "(EN 12464-1 target: 300–500 lux).")

    if dgi >= 28:
        lines.append(f"Glare index (DGI: {dgi:.1f}) indicates intolerable glare. "
                     "Venetian blinds or diffusing glazing are strongly recommended.")
    elif dgi >= 24:
        lines.append(f"Glare index (DGI: {dgi:.1f}) is uncomfortable. "
                     "Consider light shelves or external overhangs.")
    else:
        lines.append(f"Glare conditions are acceptable (DGI: {dgi:.1f}).")

    if cct > 5500:
        lines.append(f"Color temperature ({cct:.0f}K) is cool. "
                     "South-facing windows would improve light warmth.")
    else:
        lines.append(f"Color temperature ({cct:.0f}K) is within a comfortable range.")

    if view_score < 40:
        lines.append(f"View quality ({view_score:.0f}/100) is below WELL Standard minimum. "
                     "More rooms need direct window access.")
    elif view_score >= 70:
        lines.append(f"View quality ({view_score:.0f}/100) meets WELL Building Standard v2.")

    return lines


# ── MAIN FUNCTION (called by the API endpoint) ─────────────────────
def analyze_visual_comfort(floorplan_json: dict) -> dict:
    """
    Takes the parsed floorplan JSON and returns the full visual comfort result.
    This is what the FastAPI endpoint will call.
    """
    _load_models()

    # Extract geometry
    num_windows = floorplan_json.get("total_windows", 0)
    num_rooms   = floorplan_json.get("num_rooms",
                  len(floorplan_json.get("rooms", [])))
    total_area  = floorplan_json.get("total_floor_area_m2",
                  floorplan_json.get("area", 0))

    # Window area — handle multiple JSON formats
    raw_win_area = 0
    if "rooms" in floorplan_json:
        for room in floorplan_json["rooms"]:
            for w in room.get("window_dimensions", []):
                wm = w.get("width_mm",  w.get("width",  0))
                hm = w.get("height_mm", w.get("height", 0))
                if "width_mm" in w:
                    wm /= 1000
                    hm /= 1000
                raw_win_area += wm * hm
    elif "windows" in floorplan_json:
        for w in floorplan_json["windows"]:
            raw_win_area += w.get("width", 0) * w.get("height", 0)

    total_win_area = _normalize_window_area(raw_win_area, total_area)

    wwr              = total_win_area / total_area if total_area > 0 else 0.01
    avg_win_area     = total_win_area / num_windows if num_windows > 0 else 0
    windows_per_room = num_windows / num_rooms if num_rooms > 0 else 0
    area_per_window  = total_area / num_windows if num_windows > 0 else total_area

    # Build feature vector in the exact order the model was trained on
    feature_dict = {
        "num_windows":       num_windows,
        "num_rooms":         num_rooms,
        "total_area":        total_area,
        "total_window_area": total_win_area,
        "wwr":               wwr,
        "avg_window_area":   avg_win_area,
        "windows_per_room":  windows_per_room,
        "area_per_window":   area_per_window
    }
    X = np.array([[feature_dict[col] for col in _feat_cols]])
    X_scaled = _scaler.transform(X)

    # Predict
    pred_idx    = _model.predict(X_scaled)[0]
    probs       = _model.predict_proba(X_scaled)[0]
    pred_class  = _encoder.inverse_transform([pred_idx])[0]
    class_names = list(_encoder.classes_)

    # Physics for report (NOT used in prediction — only for display)
    room_area = total_area / num_rooms if num_rooms > 0 else total_area
    lux_vals, dgi_vals = [], []

    if "rooms" in floorplan_json:
        for room in floorplan_json["rooms"]:
            for w in room.get("window_dimensions", []):
                wm = w.get("width_mm",  w.get("width",  0))
                hm = w.get("height_mm", w.get("height", 0))
                if "width_mm" in w:
                    wm /= 1000
                    hm /= 1000
                wa = _normalize_window_area(wm * hm, room_area)
                lux = _calculate_lux(wa, room_area)
                lux_vals.append(lux)
                dgi_vals.append(_calculate_dgi(wa, lux))
    elif "windows" in floorplan_json:
        for w in floorplan_json["windows"]:
            wa  = _normalize_window_area(
                w.get("width", 0) * w.get("height", 0), room_area)
            lux = _calculate_lux(wa, room_area)
            lux_vals.append(lux)
            dgi_vals.append(_calculate_dgi(wa, lux))

    avg_lux    = sum(lux_vals) / len(lux_vals) if lux_vals else 0
    avg_dgi    = sum(dgi_vals) / len(dgi_vals) if dgi_vals else 0
    avg_cct    = _calculate_cct(wwr)
    view_score = _calculate_view_score(
        num_windows, num_rooms, total_win_area, total_area)

    comfort_pct = _comfort_percentage(pred_class, probs, class_names)

    return {
        "comfort_percentage": comfort_pct,
        "comfort_class":      pred_class,
        "class_probabilities": {
            cls: round(float(p), 3)
            for cls, p in zip(class_names, probs)
        },
        "metrics": {
            "light_intensity": {
                "label":  "Light Intensity",
                "value":  avg_lux,
                "unit":   "lux",
                "target": "300–500 lux (EN 12464-1)",
                "status": _lux_status(avg_lux)
            },
            "glare_index": {
                "label":  "Daylight Glare Index (DGI)",
                "value":  avg_dgi,
                "unit":   "",
                "target": "< 24 (Hopkinson scale)",
                "status": _dgi_status(avg_dgi)
            },
            "color_temperature": {
                "label":  "Color Temperature",
                "value":  avg_cct,
                "unit":   "K",
                "target": "3000–5000K (Kruithof)",
                "status": _cct_status(avg_cct)
            },
            "view_quality": {
                "label":  "View Quality Score",
                "value":  view_score,
                "unit":   "/ 100",
                "target": "≥ 70 (WELL Standard v2)",
                "status": _view_status(view_score)
            }
        },
        "geometry": {
            "total_area_m2":        round(total_area, 2),
            "total_window_area_m2": round(total_win_area, 3),
            "wwr_percent":          round(wwr * 100, 1),
            "num_windows":          num_windows,
            "num_rooms":            num_rooms,
            "windows_per_room":     round(windows_per_room, 2),
            "avg_window_area_m2":   round(avg_win_area, 3)
        },
        "analysis": _generate_analysis(
            avg_lux, avg_dgi, avg_cct, view_score, pred_class)
    }