"""
EcoVision - Recommendation Engine
===================================================
Python  → Space & Geometry recommendations (accurate)
Mistral → Orientation & Layout recommendations (natural language)

All configuration loaded from config.json — no hard-coded data.
"""
from groq import Groq
import json
from pathlib import Path
from .orientation_prompt import ORIENTATION_PROMPT
from .space_geometry_prompt import SPACE_GEOMETRY_PROMPT

# ─────────────────────────────────────────────
# 0. LOAD CONFIG + PROMPT TEMPLATE
# ─────────────────────────────────────────────

_CFG_PATH = Path(__file__).parent / "config.json"

with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    CFG = json.load(_f)

CORRIDOR_MAX_PCT = CFG["thresholds"]["corridor_ratio_max_pct"]
LARGE_ROOM_M2    = CFG["thresholds"]["large_room_area_m2"]
SERVICE_ROOMS    = CFG["room_categories"]["service"]
LLM_MODEL        = CFG["llm"]["model"]
LLM_TEMPERATURE  = CFG["llm"]["temperature"]
GROQ_API_KEY     = CFG["llm"]["groq_api_key"]
_groq_client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def is_service_room(name: str) -> bool:
    return any(w in name.lower() for w in SERVICE_ROOMS)


# ─────────────────────────────────────────────
# 1. SPACE & GEOMETRY DETECTION (PYTHON)
# ─────────────────────────────────────────────

def detect_space_problems(features: dict) -> list:
    """
    Python detects all Space & Geometry problems with exact numbers.
    Returns a list of raw problem dicts — no text yet.
    """
    problems = []
    corridor_pct = features["corridor_area_ratio"] * 100

    if corridor_pct > CORRIDOR_MAX_PCT:
        problems.append({
            "room":    "Building",
            "type":    "corridor",
            "details": f"Circulation area is {corridor_pct:.0f}% of total floor area, above the {CORRIDOR_MAX_PCT}% threshold.",
        })

    for r in features["rooms"]:
        if r["area_m2"] > LARGE_ROOM_M2 and r["is_high_use"]:
            problems.append({
                "room":    r["name"],
                "type":    "large_room",
                "details": f"{r['name']} is {r['area_m2']}m², significantly above the {LARGE_ROOM_M2}m² threshold — "
                        f"large undivided spaces are hard to thermally zone and ventilate efficiently in hot dry climates.",
            })
    
        valid_dims = [w for w in r["window_dimensions"] if w["width_mm"] and w["height_mm"]]
        if r["is_high_use"] and valid_dims:
            total_win_area = sum(
                (w["width_mm"] / 1000) * (w["height_mm"] / 1000)
                for w in valid_dims
            )
            total_ratio = total_win_area / r["area_m2"]
            if total_ratio < 0.10:
                target_area = r["area_m2"] * 0.10
                problems.append({
                    "room": r["name"],
                    "type": "small_window",
                    "details": (
                        f"{r['name']} window-to-floor ratio is {total_ratio:.0%} "
                        f"({len(valid_dims)} window(s), {total_win_area:.2f}m² total "
                        f"out of {r['area_m2']}m² room area), below the 10% minimum. "
                        f"The target window area is {target_area:.2f}m² — "  # ← explicit label
                        f"currently missing {target_area - total_win_area:.2f}m²."  # ← gap also given
                    )
                })

    # Your current code only catches "poor", missing "no_window" rooms
        if r["window_direction_rating"] == "no_window" and r["is_high_use"]:
            problems.append({
                "room":    r["name"],
                "type":    "no_window",
                "details": f"{r['name']} ({r['area_m2']}m²) has no window — "
                        f"zero natural light and ventilation in a high-use room "
                        f"in hot dry Cairo climate is a critical thermal comfort issue."
            })


    # You have total_windows and num_rooms sitting unused
    window_per_room = features["total_windows"] / features["num_rooms"]
    if window_per_room < 0.7:
        problems.append({
            "room": "Building",
            "type": "low_window_coverage",
            "details": f"Building averages only {window_per_room:.1f} windows per room — insufficient natural ventilation overall."
        })

    return problems


def build_space_prompt(features: dict, problems: list) -> str | None:
    """Fill space_geometry_prompt.py with detected problems. Returns None if no problems."""
    if not problems:
        return None

    problems_str = "\n".join([f"- {p['details']}" for p in problems])

    return SPACE_GEOMETRY_PROMPT.format(
        climate             = features["climate"].replace("_", " "),
        city                = features["city"],
        total_floor_area_m2 = features["total_floor_area_m2"],
        problems            = problems_str,
        num_problems        = len(problems),
        large_room_threshold = LARGE_ROOM_M2,
    )

def normalize_impact(impact: str) -> str:
    impact = impact.lower().strip()
    if impact in ["moderate", "med"]:
        return "medium"
    if impact in ["critical", "severe"]:
        return "high"
    if impact in ["minor", "minimal"]:
        return "low"
    return impact if impact in ["high", "medium", "low"] else "medium"

def validate_space_recs(recs: list, problems: list) -> list:
    """
    Guard against LLM hallucination: discard any item whose room does not
    correspond to an actual detected problem.

    Matching rules:
      - corridor problems  → room must be "Building" (case-insensitive)
      - large_room problems → room must match the problem's room name exactly
    """
    # Build allowed rooms from detected problems
    allowed = set()
    for p in problems:
        if p["type"] == "corridor":
            allowed.add("building")
        elif p["type"] == "low_window_coverage":
            allowed.add("building")
        else:
            allowed.add(p["room"].lower())

    validated = []
    for rec in recs:
        room_key = rec.get("room", "").lower()
        if room_key in allowed:
            validated.append(rec)
        else:
            print(f"   🚫 Hallucinated item removed: room='{rec.get('room')}' "
                  f"not in detected problems {[p['room'] for p in problems]}")

    print(f"   ✅ Validation: {len(validated)}/{len(recs)} items kept")
    return validated


def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = _groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=LLM_TEMPERATURE,
    )
    return response.choices[0].message.content.strip()

def get_space_recommendations(features: dict, model: str = None) -> list:
    model    = model or LLM_MODEL
    problems = detect_space_problems(features)

    if not problems:
        print("✅ No space & geometry problems — skipping LLM")
        return []

    prompt = build_space_prompt(features, problems)
    print(f"\n🤖 Sending Space & Geometry problems to {model}...")
    print("─" * 50)

    try:
        raw = call_llm(
            system_prompt="You are a sustainable architecture expert. Respond with valid JSON only. Never include text outside the JSON array.",
            user_prompt=prompt
        )
        print(f"📨 Raw LLM response:\n{raw}\n")
        print("─" * 50)
        recs = parse_response(raw, label="space & geometry")
        recs = validate_space_recs(recs, problems)
        return recs

    except Exception as e:
        print(f"❌ Groq error (space): {e}")
        return []


# ─────────────────────────────────────────────
# 2. ORIENTATION & LAYOUT (LLM)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# REPLACE your existing build_prompt() with this
# ─────────────────────────────────────────────

def build_prompt(features: dict) -> str | None:

    def room_line(r, note=""):
        dirs = r["all_window_directions"]
        secondary = [d for d in dirs if d != r["window_direction"]]
        base = (
            f"- {r['name']}: main window faces {r['window_direction']}"
            + (f", also has windows facing {', '.join(secondary)}" if secondary else "")
            + f", area {r['area_m2']}m², {r['window_count']} window(s)"
        )
        if r["window_dimensions"]:
            base += f", {r['window_dimensions'][0]['width_mm']}mm wide"
        if note:
            base += f" [{note}]"
        return base

    # 1. Rooms with poor main direction
    poor_rooms = [
        r for r in features["rooms"]
        if r.get("window_direction_rating") == "poor"
        and not r["is_circulation"]
    ]

    # 2. Rooms with good/acceptable main direction BUT bad secondary windows (W or SW)
    mixed_rooms = [
        r for r in features["rooms"]
        if r["window_direction_rating"] in ["good", "acceptable"]
        and len(r["all_window_directions"]) > 1
        and any(d in ["W", "SW"] for d in r["all_window_directions"])
        and r["window_direction"] not in ["W", "SW"]
        and not r["is_circulation"]
    ]

    # 3. Small rooms (<15m²) with more than 1 window — regardless of rating
    overcrowded_rooms = [
        r for r in features["rooms"]
        if r["area_m2"] < 15
        and r["window_count"] > 1
        and not r["is_circulation"]
    ]

    already_flagged = (
        {r["name"] for r in poor_rooms} |
        {r["name"] for r in mixed_rooms}
    )

    # Only add overcrowded rooms not already flagged by poor or mixed
    overcrowded_only = [
        r for r in overcrowded_rooms
        if r["name"] not in already_flagged
    ]

    if not poor_rooms and not mixed_rooms and not overcrowded_only:
        return None

    problems_lines = (
        [room_line(r) for r in poor_rooms] +
        [room_line(r, note="good main direction but has problematic secondary windows") for r in mixed_rooms if r["name"] not in {x["name"] for x in poor_rooms}] +
        [room_line(r, note="small room with multiple windows — consider removing extra window") for r in overcrowded_only]
    )

    problems = "\n".join(problems_lines)

    return ORIENTATION_PROMPT.format(
        climate         = features["climate"].replace("_", " "),
        building_facing = features["north_arrow_direction"],
        problems        = problems,
    )

VALID_CATEGORIES = {"Orientation & Layout", "Space & Geometry"}

def validate_orientation_recs(recs: list, features: dict) -> list:
    actual_rooms = {r["name"].lower() for r in features["rooms"]}
    actual_rooms.add("building")

    validated = []
    for rec in recs:
        room_key = rec.get("room", "").lower()
        category = rec.get("category", "")
        
        if category not in VALID_CATEGORIES:
            print(f"   🚫 Invalid category removed: '{category}' for room '{rec.get('room')}'")
            continue
        if room_key not in actual_rooms:
            print(f"   🚫 Hallucinated room removed: '{rec.get('room')}'")
            continue
        validated.append(rec)

    print(f"   ✅ Orientation validation: {len(validated)}/{len(recs)} items kept")
    return validated

def get_orientation_recommendations(features: dict, model: str = None) -> list:
    model  = model or LLM_MODEL
    prompt = build_prompt(features)
    if prompt is None:
        print("✅ No orientation problems — skipping LLM")
        return []

    print(f"\n🤖 Sending to {LLM_MODEL}...")
    print("─" * 50)

    try:
        raw = call_llm(
            system_prompt="You are a sustainable architecture expert. Respond with valid JSON only. Never include text outside the JSON array.",
            user_prompt=prompt
        )
        print(f"📨 Raw LLM response:\n{raw}\n")
        print("─" * 50)
        recs = parse_response(raw, label="orientation")
        recs = validate_orientation_recs(recs, features)
        return recs

    except Exception as e:
        print(f"❌ Groq error: {e}")
        return []


# ─────────────────────────────────────────────
# 3. RESPONSE PARSER
# ─────────────────────────────────────────────

def parse_response(raw: str, label: str = "orientation") -> list:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        print(f"❌ No JSON array found ({label})")
        return []

    try:
        recs = json.loads(raw[start:end])
        for rec in recs:
            for key in ["issue", "recommendation"]:
                if key in rec:
                    rec[key] = " ".join(rec[key].split())
        for rec in recs:
            rec["impact"] = normalize_impact(rec.get("impact", "medium"))
        return recs
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error ({label}): {e}")
        return []


# ─────────────────────────────────────────────
# 4. DEDUPLICATE
# ─────────────────────────────────────────────

def deduplicate(recommendations: list) -> list:
    """Keep only the LLM version when both systems flag the same room."""
    orientation_rooms = {
        r["room"] for r in recommendations
        if r.get("category") == "Orientation & Layout"
    }

    recs = [
        r for r in recommendations
        if not (
            r.get("category") == "Space & Geometry"
            and r["room"] in orientation_rooms
            and "window faces" in r.get("issue", "")
        )
    ]
    # NEW — remove same-room same-category duplicates
    seen = set()
    deduped = []
    for r in recs:
        key = (r["room"], r["category"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
        else:
            print(f"   🚫 Duplicate removed: {r['room']} / {r['category']}")
    return deduped


# ─────────────────────────────────────────────
# 5. OUTPUT FORMATTER
# ─────────────────────────────────────────────

def format_recommendations(recommendations: list) -> str:
    if not recommendations:
        return "✅ No issues found — floor plan looks good!"

    output  = "\n🌿 ECOVISION SUSTAINABILITY RECOMMENDATIONS\n"
    output += "=" * 52 + "\n"

    impact_order = {"high": 0, "medium": 1, "low": 2}
    sorted_recs  = sorted(
        recommendations,
        key=lambda r: impact_order.get(r.get("impact", "low"), 2)
    )

    for i, rec in enumerate(sorted_recs, 1):
        emoji    = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("impact", "low"), "⚪")
        triggers = ", ".join(rec.get("triggers", []))
        output  += f"\n{i}. [{rec.get('category')}] — {rec.get('room')}\n"
        output  += f"   {emoji} Impact: {rec.get('impact', '').upper()}\n"
        output  += f"   ⚠️  Issue: {rec.get('issue')}\n"
        output  += f"   ✅ Recommendation: {rec.get('recommendation')}\n"
        if triggers:
            output += f"   🔗 Affects: {triggers}\n"
        output += "\n"

    return output


# ─────────────────────────────────────────────
# 6. MAIN PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(features: dict, model: str = None) -> dict:
    model = model or LLM_MODEL

    if "error" in features:
        return {
            "recommendations": [],
            "formatted":       f"❌ Cannot run recommendations: {features['error']}",
            "total":           0,
            "error":           features["error"],
        }

    print("\n🏗️  Detecting Space & Geometry problems...")
    space_recs = get_space_recommendations(features, model)
    print(f"✅ {len(space_recs)} space & geometry recommendations")

    print("\n🧭 Detecting Orientation & Layout problems...")
    orientation_recs = get_orientation_recommendations(features, model)
    print(f"✅ {len(orientation_recs)} orientation recommendations")

    all_recs  = deduplicate(orientation_recs + space_recs)
    formatted = format_recommendations(all_recs)

    return {
        "recommendations": all_recs,
        "formatted":       formatted,
        "total":           len(all_recs)
    }


# ─────────────────────────────────────────────
# 7. ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    try:
        with open(r"C:\Users\lenovo\Desktop\ecovision recommendation\results\basement final (added windows).json", "r", encoding="utf-8") as f:
            features = json.load(f)
        print("✅ Loaded basement final (added windows).json")
    except FileNotFoundError:
        print("❌ Run dxf_parser.py first to generate basement final (added windows).json")
        exit(1)

    result = run_pipeline(features)

    print(result["formatted"])

    with open(r"C:\Users\lenovo\Desktop\ecovision recommendation\results\recommendations basement final (added windows).json", "w",encoding="utf-8") as f:
        json.dump(result["recommendations"], f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {result['total']} recommendations to recommendations basement final (added windows).json")