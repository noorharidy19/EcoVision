import math
import joblib
import numpy as np
from pathlib import Path

# ── Model paths ────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "visual_comfort_models"

_model = None
_scaler = None
_encoder = None
_feat_cols = None


def _load_models():
    global _model, _scaler, _encoder, _feat_cols

    if _model is None:
        _model = joblib.load(MODEL_DIR / "visual_comfort_rf.pkl")
        _scaler = joblib.load(MODEL_DIR / "scaler.pkl")
        _encoder = joblib.load(MODEL_DIR / "label_encoder.pkl")
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
def _calculate_lux(
    window_area_m2: float,
    room_area_m2: float,
    ceiling_height: float = 2.7
) -> float:

    if room_area_m2 <= 0 or window_area_m2 <= 0:
        return 0

    depth_factor = min(
        1.0,
        (2.5 * ceiling_height) / math.sqrt(room_area_m2)
    )

    df = min(
        (
            window_area_m2
            * 0.7
            * 0.7
            * depth_factor
        ) / room_area_m2,
        0.25
    )

    return round(df * 10000, 2)


def _calculate_dgi(window_area_m2: float, lux: float) -> float:

    if window_area_m2 <= 0 or lux <= 0:
        return 0

    # Updated residential sky luminance
    sky_lum = 2000

    bg_lum = max(50, lux * 0.08)

    # Removed omega cap
    omega = window_area_m2 / (2.0 ** 2)

    try:
        num = (sky_lum ** 1.6) * (omega ** 0.8)
        den = bg_lum + 0.07 * (omega ** 0.5) * sky_lum

        return round(
            max(0, min(10 * math.log10(num / den), 40)),
            2
        )

    except (ValueError, ZeroDivisionError):
        return 0


def _calculate_cct(wwr: float) -> float:

    if wwr <= 0:
        return 4000

    return round(
        min(3500 + (wwr / 0.40) * 2500, 6500),
        0
    )


def _calculate_view_score(
    num_windows: int,
    num_rooms: int,
    total_window_area_m2: float,
    total_area_m2: float
) -> float:

    if num_rooms == 0 or total_area_m2 <= 0:
        return 0

    score = 0

    score += min(
        (num_windows / num_rooms) / 2.0,
        1.0
    ) * 40

    avg_win = (
        total_window_area_m2 / num_windows
        if num_windows > 0 else 0
    )

    score += min(avg_win / 1.5, 1.0) * 35

    wfr = total_window_area_m2 / total_area_m2

    if 0.15 <= wfr <= 0.30:
        wfr_score = 1.0

    elif wfr < 0.15:
        wfr_score = wfr / 0.15

    else:
        wfr_score = max(
            0,
            1 - (wfr - 0.30) / 0.30
        )

    score += wfr_score * 25

    return round(min(score, 100), 2)


# ── Status helpers ─────────────────────────────────────────────────
def _lux_status(lux, dgi):

    if 300 <= lux <= 500 and dgi < 24:
        return "Optimal — good light with controlled glare"

    elif 300 <= lux <= 500 and dgi >= 24:
        return "Light level is good but glare is high — shading recommended"

    elif lux < 300 and dgi < 18:
        return "Low light but glare is controlled — increasing windows is safe"

    elif lux < 300 and dgi >= 18:
        return "Low light with glare present — adding windows may worsen glare"

    elif lux > 500 and dgi < 24:
        return "Slightly bright but glare is controlled"

    return "Over-lit with high glare — shading recommended"


def _dgi_status(dgi):

    if dgi < 18:
        return "Imperceptible glare"

    elif dgi < 24:
        return "Perceptible but acceptable"

    elif dgi < 28:
        return "Uncomfortable glare"

    return "Intolerable glare"


def _cct_status(cct, lux):

    if 3000 <= cct <= 5000 and lux >= 200:
        return "Comfortable color temperature for current light level"

    elif cct > 5000 and lux < 200:
        return "Cool light in a dim room — uncomfortable combination"

    elif cct > 5000 and lux >= 300:
        return "Cool light acceptable at this brightness level"

    elif 3000 <= cct <= 5000 and lux < 200:
        return "Good color temperature but room is too dim"

    return "Color temperature outside comfort range"


def _view_status(score, dgi):

    if score >= 70 and dgi < 24:
        return "Excellent view access with acceptable glare"

    elif score >= 70 and dgi >= 24:
        return "Good view but windows are causing glare"

    elif score >= 40:
        return "Adequate view access"

    return "Poor view access"


# ── Comfort percentage ─────────────────────────────────────────────
# ── Comfort percentage (Option C: physics + model combined) ────────
def _comfort_percentage(avg_lux, avg_dgi, avg_cct, view_score,
                         predicted_class, probabilities, class_names):
    """
    60% physics-based score + 40% model confidence position.
    Prevents inflated scores when metrics are poor.
    """

    # Physics score per metric 0-100
    if 300 <= avg_lux <= 500:
        lux_pct = 100
    elif avg_lux < 300:
        lux_pct = max(0, (avg_lux / 300) * 80)
    else:
        lux_pct = max(0, 100 - ((avg_lux - 500) / 500) * 60)

    if avg_dgi < 18:
        dgi_pct = 100
    elif avg_dgi < 24:
        dgi_pct = 100 - ((avg_dgi - 18) / 6) * 30
    elif avg_dgi < 28:
        dgi_pct = 70 - ((avg_dgi - 24) / 4) * 30
    else:
        dgi_pct = max(0, 40 - ((avg_dgi - 28) / 10) * 40)

    if 3000 <= avg_cct <= 5000:
        cct_pct = 100
    elif avg_cct < 3000:
        cct_pct = max(0, (avg_cct / 3000) * 70)
    else:
        cct_pct = max(0, 100 - ((avg_cct - 5000) / 1500) * 60)

    view_pct = min(100, (view_score / 70) * 100)

    # Weighted physics score
    physics_score = (
        lux_pct  * 0.30 +
        dgi_pct  * 0.35 +
        cct_pct  * 0.15 +
        view_pct * 0.20
    )

    # Model confidence position
    prob_dict = dict(zip(class_names, probabilities))
    model_confidence = prob_dict.get(predicted_class, 0.5)
    class_position = {"Poor": 20, "Acceptable": 50, "Good": 85}
    model_score = class_position.get(predicted_class, 50) * model_confidence

    # 60% physics, 40% model
    final = (physics_score * 0.60) + (model_score * 0.40)
    return round(min(max(final, 1), 99), 1)


# ── Analysis text ──────────────────────────────────────────────────
def _generate_analysis(
    lux,
    dgi,
    cct,
    view_score,
    predicted_class
):

    lines = []

    summaries = {
        "Good":
            "This floor plan demonstrates good visual comfort. "
            "The combination of light levels, glare control, "
            "color temperature, and view access are well balanced.",

        "Acceptable":
            "Visual comfort is acceptable but improvable. "
            "Some criteria are outside optimal ranges.",

        "Poor":
            "This floor plan has poor visual comfort. "
            "The combination of light, glare, and view factors "
            "is below acceptable standards."
    }

    lines.append(summaries.get(predicted_class, ""))

    if lux < 300 and dgi >= 24:

        lines.append(
            f"Light is low ({lux:.0f} lux) but glare is already high "
            f"(DGI: {dgi:.1f}). Simply adding more windows would worsen glare."
        )

    elif lux < 300 and dgi < 18:

        lines.append(
            f"Light is low ({lux:.0f} lux) and glare is controlled "
            f"(DGI: {dgi:.1f}). Increasing window area is safe."
        )

    elif lux > 500 and dgi >= 28:

        lines.append(
            f"Over-lit ({lux:.0f} lux) with intolerable glare "
            f"(DGI: {dgi:.1f}). External shading is recommended."
        )

    else:

        lines.append(
            f"Light intensity ({lux:.0f} lux) and glare "
            f"(DGI: {dgi:.1f}) are within acceptable ranges."
        )

    if cct > 5000 and lux < 200:

        lines.append(
            f"Color temperature ({cct:.0f}K) is cool while the room is dim "
            f"({lux:.0f} lux), creating an uncomfortable combination."
        )

    elif 3000 <= cct <= 5000 and lux >= 200:

        lines.append(
            f"Color temperature ({cct:.0f}K) is comfortable "
            f"for the current light level."
        )

    if view_score >= 70 and dgi >= 24:

        lines.append(
            f"View quality is good ({view_score:.0f}/100) "
            f"but glare is high (DGI: {dgi:.1f}). "
            "External shading is recommended."
        )

    elif view_score < 40:

        lines.append(
            f"View quality is poor ({view_score:.0f}/100). "
            "More rooms need direct window access."
        )

    return lines


# =========================
# RECOMMENDATIONS ENGINE
# Simulates realistic design fixes and projects the new score
# =========================

def _simulate_fix(avg_lux, avg_dgi, avg_cct, view_score,
                  fix_type, total_window_area, total_area,
                  num_windows, num_rooms):
    """
    Applies a single design fix and returns new physics values.
    All fixes are physically realistic — they change the geometry
    that feeds the physics formulas, not the scores directly.
    """
    new_lux = avg_lux
    new_dgi = avg_dgi
    new_cct = avg_cct
    new_view = view_score

    if fix_type == "increase_windows":
        # Simulate adding 20% more window area
        # Effect: lux increases, DGI also increases (trade-off)
        new_window_area = total_window_area * 1.20
        new_wwr = new_window_area / total_area if total_area > 0 else 0
        per_window = new_window_area / num_windows if num_windows > 0 else 0
        room_area = total_area / num_rooms if num_rooms > 0 else total_area

        new_lux = _calculate_lux(per_window, room_area)
        new_dgi = _calculate_dgi(per_window, new_lux)
        new_cct = float(_calculate_cct(new_wwr))
        new_view = _calculate_view_score(
            num_windows, num_rooms, new_window_area, total_area)

    elif fix_type == "add_shading":
        # Simulate external shading — reduces effective sky luminance by 35%
        # Effect: DGI drops significantly, lux drops slightly
        new_lux = avg_lux * 0.85
        # Shading reduces sky luminance seen through window
        # Recalculate DGI with reduced sky luminance factor
        per_window = total_window_area / num_windows if num_windows > 0 else 0
        room_area = total_area / num_rooms if num_rooms > 0 else total_area
        omega = per_window / (2.0 ** 2)
        shaded_sky = 2000 * 0.65  # 35% reduction from shading
        bg_lum = max(50, new_lux * 0.08)
        try:
            import math
            num = (shaded_sky ** 1.6) * (omega ** 0.8)
            den = bg_lum + 0.07 * (omega ** 0.5) * shaded_sky
            new_dgi = round(max(0, min(10 * math.log10(num / den), 40)), 2)
        except Exception:
            new_dgi = avg_dgi * 0.75

    elif fix_type == "add_windows_per_room":
        # Simulate adding 1 window per room
        # Effect: view score and lux improve
        new_num_windows = num_windows + num_rooms
        new_view = _calculate_view_score(
            new_num_windows, num_rooms, total_window_area, total_area)
        room_area = total_area / num_rooms if num_rooms > 0 else total_area
        per_window = total_window_area / new_num_windows
        new_lux = _calculate_lux(per_window, room_area)
        new_dgi = _calculate_dgi(per_window, new_lux)

    elif fix_type == "reduce_windows":
        # Simulate reducing window area by 15% to control glare
        # Effect: DGI drops, lux drops slightly — acceptable trade-off
        new_window_area = total_window_area * 0.85
        new_wwr = new_window_area / total_area if total_area > 0 else 0
        per_window = new_window_area / num_windows if num_windows > 0 else 0
        room_area = total_area / num_rooms if num_rooms > 0 else total_area

        new_lux = _calculate_lux(per_window, room_area)
        new_dgi = _calculate_dgi(per_window, new_lux)
        new_cct = float(_calculate_cct(new_wwr))
        new_view = _calculate_view_score(
            num_windows, num_rooms, new_window_area, total_area)

    return new_lux, new_dgi, new_cct, new_view


def _project_score(lux, dgi, cct, view):
    """
    Runs the model on projected values and returns the new comfort percentage.
    This is what the user would get IF the recommendation was applied.
    """
    _load_models()
    feature_dict = {
        "avg_lux": lux,
        "avg_dgi": dgi,
        "avg_cct": cct,
        "view_quality_score": view
    }
    X = np.array([[feature_dict[col] for col in _feat_cols]])
    X_scaled = _scaler.transform(X)
    pred_idx = _model.predict(X_scaled)[0]
    probs = _model.predict_proba(X_scaled)[0]
    pred_class = _encoder.inverse_transform([pred_idx])[0]
    class_names = list(_encoder.classes_)
    return _comfort_percentage(lux, dgi, cct, view, pred_class, probs, class_names), pred_class


def generate_visual_recommendations(analysis_result: dict,
                                     floorplan_json: dict) -> dict:
    """
    Takes the existing analysis result and generates improvement scenarios.
    Returns main issue, recommended fixes, and projected scores.
    Called by a separate API endpoint — not part of the main analysis.
    """
    current_pct   = analysis_result["comfort_percentage"]
    current_class = analysis_result["comfort_class"]
    metrics       = analysis_result["metrics"]

    avg_lux    = metrics["light_intensity"]["value"]
    avg_dgi    = metrics["glare_index"]["value"]
    avg_cct    = metrics["color_temperature"]["value"]
    view_score = metrics["view_quality"]["value"]

    # Extract geometry for simulation
    num_windows = floorplan_json.get("total_windows",
                  len(floorplan_json.get("windows", [])))
    num_rooms   = floorplan_json.get("num_rooms",
                  len(floorplan_json.get("rooms", [])))
    total_area  = floorplan_json.get("total_floor_area_m2",
                  floorplan_json.get("area", 0))

    raw_win = 0
    if "rooms" in floorplan_json:
        for room in floorplan_json["rooms"]:
            for w in room.get("window_dimensions", []):
                wm = w.get("width_mm", w.get("width", 0))
                hm = w.get("height_mm", w.get("height", 0))
                if "width_mm" in w:
                    wm /= 1000
                    hm /= 1000
                raw_win += wm * hm
    elif "windows" in floorplan_json:
        for w in floorplan_json["windows"]:
            raw_win += w.get("width", 0) * w.get("height", 0)

    total_window_area = _normalize_window_area(raw_win, total_area)

    # No recommendations needed for good designs
    if current_class == "Good" and current_pct >= 75:
        return {
            "has_recommendations": False,
            "message": "No improvements needed. "
                       "This floor plan already achieves good visual comfort.",
            "current_score": current_pct,
            "current_class": current_class,
            "scenarios": []
        }

    # ── Identify main issue ────────────────────────────────────────
    scenarios = []

    # Issue 1: High glare
    if avg_dgi >= 24:
        new_lux, new_dgi, new_cct, new_view = _simulate_fix(
            avg_lux, avg_dgi, avg_cct, view_score,
            "add_shading", total_window_area, total_area,
            num_windows, num_rooms
        )
        proj_pct, proj_class = _project_score(new_lux, new_dgi, new_cct, new_view)
        if proj_pct > current_pct + 3:
            scenarios.append({
                "fix":         "Add External Shading",
                "description": f"Installing external shading (blinds, overhangs, or "
                                f"diffusing glazing) would reduce glare from "
                                f"DGI {avg_dgi:.1f} to approximately {new_dgi:.1f}, "
                                f"while keeping light levels adequate at {new_lux:.0f} lux.",
                "projected_lux":   round(new_lux, 1),
                "projected_dgi":   round(new_dgi, 1),
                "projected_cct":   round(new_cct, 0),
                "projected_view":  round(new_view, 1),
                "projected_score": proj_pct,
                "projected_class": proj_class,
                "score_change":    round(proj_pct - current_pct, 1)
            })

    # Issue 2: Low lux and glare is low enough that adding windows is safe
    if avg_lux < 300 and avg_dgi < 22:
        new_lux, new_dgi, new_cct, new_view = _simulate_fix(
            avg_lux, avg_dgi, avg_cct, view_score,
            "increase_windows", total_window_area, total_area,
            num_windows, num_rooms
        )
        proj_pct, proj_class = _project_score(new_lux, new_dgi, new_cct, new_view)
        if proj_pct > current_pct + 3:
            scenarios.append({
                "fix":         "Increase Window Area",
                "description": f"Increasing total window area by 20% would raise "
                                f"light levels from {avg_lux:.0f} to {new_lux:.0f} lux. "
                                f"Since current glare is low (DGI {avg_dgi:.1f}), "
                                f"this is safe to do without significant glare penalty.",
                "projected_lux":   round(new_lux, 1),
                "projected_dgi":   round(new_dgi, 1),
                "projected_cct":   round(new_cct, 0),
                "projected_view":  round(new_view, 1),
                "projected_score": proj_pct,
                "projected_class": proj_class,
                "score_change":    round(proj_pct - current_pct, 1)
            })

    # Issue 3: Low view score and glare is not already critical
    if view_score < 40 and avg_dgi < 26:
        new_lux, new_dgi, new_cct, new_view = _simulate_fix(
            avg_lux, avg_dgi, avg_cct, view_score,
            "add_windows_per_room", total_window_area, total_area,
            num_windows, num_rooms
        )
        proj_pct, proj_class = _project_score(new_lux, new_dgi, new_cct, new_view)
        if proj_pct > current_pct + 3:
            scenarios.append({
                "fix":         "Improve Window Coverage Per Room",
                "description": f"Adding one window per room would improve view quality "
                                f"from {view_score:.0f} to {new_view:.0f} out of 100, "
                                f"meeting WELL Building Standard v2 requirements. "
                                f"Light levels would increase to {new_lux:.0f} lux.",
                "projected_lux":   round(new_lux, 1),
                "projected_dgi":   round(new_dgi, 1),
                "projected_cct":   round(new_cct, 0),
                "projected_view":  round(new_view, 1),
                "projected_score": proj_pct,
                "projected_class": proj_class,
                "score_change":    round(proj_pct - current_pct, 1)
            })

    # Issue 4: High lux AND high DGI — reduce windows
    if avg_lux > 750 and avg_dgi >= 28:
        new_lux, new_dgi, new_cct, new_view = _simulate_fix(
            avg_lux, avg_dgi, avg_cct, view_score,
            "reduce_windows", total_window_area, total_area,
            num_windows, num_rooms
        )
        proj_pct, proj_class = _project_score(new_lux, new_dgi, new_cct, new_view)
        if proj_pct > current_pct + 3:
            scenarios.append({
                "fix":         "Reduce Window Area",
                "description": f"Reducing window area by 15% would bring light levels "
                                f"from {avg_lux:.0f} down to {new_lux:.0f} lux and reduce "
                                f"glare from DGI {avg_dgi:.1f} to {new_dgi:.1f}. "
                                f"The space is currently over-lit — less glass improves comfort.",
                "projected_lux":   round(new_lux, 1),
                "projected_dgi":   round(new_dgi, 1),
                "projected_cct":   round(new_cct, 0),
                "projected_view":  round(new_view, 1),
                "projected_score": proj_pct,
                "projected_class": proj_class,
                "score_change":    round(proj_pct - current_pct, 1)
            })

    # Determine main issue label
    if avg_dgi >= 28:
        main_issue = "High glare — windows are causing intolerable glare"
    elif avg_dgi >= 24:
        main_issue = "Uncomfortable glare — shading or glazing changes recommended"
    elif avg_lux < 150:
        main_issue = "Insufficient daylight — floor plan needs more window area"
    elif avg_lux < 300:
        main_issue = "Below optimal light levels — some improvement possible"
    elif view_score < 40:
        main_issue = "Poor view access — not enough rooms have window coverage"
    else:
        main_issue = "Borderline comfort — minor improvements could push to Good"

    if not scenarios:
        return {
            "has_recommendations": False,
            "message": "Current design is close to optimal. "
                       "No single change would significantly improve the score.",
            "current_score": current_pct,
            "current_class": current_class,
            "scenarios": []
        }

    # Sort by biggest improvement first
    scenarios.sort(key=lambda x: x["score_change"], reverse=True)

    return {
        "has_recommendations": True,
        "main_issue":   main_issue,
        "current_score": current_pct,
        "current_class": current_class,
        "scenarios":    scenarios
    }


# ── MAIN FUNCTION ──────────────────────────────────────────────────
def analyze_visual_comfort(floorplan_json: dict) -> dict:

    _load_models()

    # Geometry
    num_windows = floorplan_json.get("total_windows", 0)

    num_rooms = floorplan_json.get(
        "num_rooms",
        len(floorplan_json.get("rooms", []))
    )

    total_area = floorplan_json.get(
        "total_floor_area_m2",
        floorplan_json.get("area", 0)
    )

    # Window area
    raw_win_area = 0

    if "rooms" in floorplan_json:

        for room in floorplan_json["rooms"]:

            for w in room.get("window_dimensions", []):

                wm = w.get("width_mm", w.get("width", 0))
                hm = w.get("height_mm", w.get("height", 0))

                if "width_mm" in w:
                    wm /= 1000
                    hm /= 1000

                raw_win_area += wm * hm

    elif "windows" in floorplan_json:

        for w in floorplan_json["windows"]:
            raw_win_area += (
                w.get("width", 0)
                * w.get("height", 0)
            )

    total_win_area = _normalize_window_area(
        raw_win_area,
        total_area
    )

    wwr = (
        total_win_area / total_area
        if total_area > 0 else 0.01
    )

    # Physics calculations
    room_area = (
        total_area / num_rooms
        if num_rooms > 0 else total_area
    )

    lux_vals = []
    dgi_vals = []

    if "rooms" in floorplan_json:

        for room in floorplan_json["rooms"]:

            for w in room.get("window_dimensions", []):

                wm = w.get("width_mm", w.get("width", 0))
                hm = w.get("height_mm", w.get("height", 0))

                if "width_mm" in w:
                    wm /= 1000
                    hm /= 1000

                wa = _normalize_window_area(
                    wm * hm,
                    room_area
                )

                lux = _calculate_lux(wa, room_area)

                lux_vals.append(lux)

                dgi_vals.append(
                    _calculate_dgi(wa, lux)
                )

    elif "windows" in floorplan_json:

        for w in floorplan_json["windows"]:

            wa = _normalize_window_area(
                w.get("width", 0)
                * w.get("height", 0),
                room_area
            )

            lux = _calculate_lux(wa, room_area)

            lux_vals.append(lux)

            dgi_vals.append(
                _calculate_dgi(wa, lux)
            )

    avg_lux = (
        sum(lux_vals) / len(lux_vals)
        if lux_vals else 0
    )

    avg_dgi = (
        sum(dgi_vals) / len(dgi_vals)
        if dgi_vals else 0
    )

    avg_cct = _calculate_cct(wwr)

    view_score = _calculate_view_score(
        num_windows,
        num_rooms,
        total_win_area,
        total_area
    )

    # NEW ML FEATURE VECTOR
    feature_dict = {
        "avg_lux": avg_lux,
        "avg_dgi": avg_dgi,
        "avg_cct": avg_cct,
        "view_quality_score": view_score
    }

    X = np.array([
        [feature_dict[col] for col in _feat_cols]
    ])

    X_scaled = _scaler.transform(X)

    # Predict
    pred_idx = _model.predict(X_scaled)[0]

    probs = _model.predict_proba(X_scaled)[0]

    pred_class = _encoder.inverse_transform(
        [pred_idx]
    )[0]

    class_names = list(_encoder.classes_)

    comfort_pct = _comfort_percentage(
         avg_lux,
        avg_dgi,
        float(avg_cct),
        view_score,
        pred_class,
        probs,
        class_names
    )

    return {
        "comfort_percentage": comfort_pct,

        "comfort_class": pred_class,

        "class_probabilities": {
            cls: round(float(p), 3)
            for cls, p in zip(class_names, probs)
        },

        "metrics": {

            "light_intensity": {
                "label": "Light Intensity",
                "value": avg_lux,
                "unit": "lux",
                "target": "300–500 lux (EN 12464-1)",
                "status": _lux_status(avg_lux, avg_dgi)
            },

            "glare_index": {
                "label": "Daylight Glare Index (DGI)",
                "value": avg_dgi,
                "unit": "",
                "target": "< 24 (Hopkinson scale)",
                "status": _dgi_status(avg_dgi)
            },

            "color_temperature": {
                "label": "Color Temperature",
                "value": avg_cct,
                "unit": "K",
                "target": "3000–5000K (Kruithof)",
                "status": _cct_status(avg_cct, avg_lux)
            },

            "view_quality": {
                "label": "View Quality Score",
                "value": view_score,
                "unit": "/ 100",
                "target": "≥ 70 (WELL Standard v2)",
                "status": _view_status(view_score, avg_dgi)
            }
        },

        "geometry": {
            "total_area_m2": round(total_area, 2),

            "total_window_area_m2": round(
                total_win_area,
                3
            ),

            "wwr_percent": round(wwr * 100, 1),

            "num_windows": num_windows,

            "num_rooms": num_rooms,

            "windows_per_room": round(
                num_windows / num_rooms,
                2
            ) if num_rooms > 0 else 0,

            "avg_window_area_m2": round(
                total_win_area / num_windows,
                3
            ) if num_windows > 0 else 0
        },

        "analysis": _generate_analysis(
            avg_lux,
            avg_dgi,
            avg_cct,
            view_score,
            pred_class
        )
    }