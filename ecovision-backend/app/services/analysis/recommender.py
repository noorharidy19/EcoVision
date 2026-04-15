"""
EcoVision - Recommendation Engine
===================================================
Python  → Space & Geometry recommendations (accurate)
Mistral → Orientation & Layout recommendations (natural language)

All configuration loaded from config.json — no hard-coded data.
"""

import ollama
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
LLM_TOP_P        = CFG["llm"]["top_p"]


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
                "details": f"{r['name']} is {r['area_m2']}m², above the {LARGE_ROOM_M2}m² threshold for efficient thermal zoning.",
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
    )


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
        elif p["type"] == "large_room":
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
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a sustainable architecture expert. Respond with valid JSON only. Never include text outside the JSON array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={"temperature": LLM_TEMPERATURE, "top_p": LLM_TOP_P}
        )

        raw = response["message"]["content"].strip()
        print(f"📨 Raw LLM response:\n{raw}\n")
        print("─" * 50)
        recs = parse_response(raw, label="space & geometry")
        recs = validate_space_recs(recs, problems)
        return recs

    except Exception as e:
        print(f"❌ Ollama error (space): {e}")
        return []


# ─────────────────────────────────────────────
# 2. ORIENTATION & LAYOUT (LLM)
# ─────────────────────────────────────────────

def build_prompt(features: dict) -> str | None:
    """Fill orientation_prompt.txt with runtime values. Returns None if no problems."""

    poor_rooms = [
        r for r in features["rooms"]
        if r.get("window_direction_rating") == "poor"
        and r["is_high_use"]
        and not is_service_room(r["name"])
    ]

    if not poor_rooms:
        return None

    problems = "\n".join([
        f"- {r['name']} window faces {r['window_direction']} → excessive heat gain in hot dry climate"
        for r in poor_rooms
    ])

    return ORIENTATION_PROMPT.format(
        climate        = features["climate"].replace("_", " "),
        building_facing= features["north_arrow_direction"],
        problems       = problems,
    )


def get_orientation_recommendations(features: dict, model: str = None) -> list:
    model  = model or LLM_MODEL
    prompt = build_prompt(features)
    if prompt is None:
        print("✅ No orientation problems — skipping LLM")
        return []

    print(f"\n🤖 Sending to {model}...")
    print("─" * 50)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a sustainable architecture expert. Respond with valid JSON only. Never include text outside the JSON array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={"temperature": LLM_TEMPERATURE, "top_p": LLM_TOP_P}
        )

        raw = response["message"]["content"].strip()
        print(f"📨 Raw LLM response:\n{raw}\n")
        print("─" * 50)
        return parse_response(raw, label="orientation")

    except Exception as e:
        print(f"❌ Ollama error: {e}")
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
        print(f"✅ Parsed {len(recs)} {label} recommendations")
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

    return [
        r for r in recommendations
        if not (
            r.get("category") == "Space & Geometry"
            and r["room"] in orientation_rooms
            and "window faces" in r.get("issue", "")
        )
    ]


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
        with open("C:\\Users\\lenovo\\Desktop\\ecovision recommendation\\final recommendation\\extracted_features_room.json", "r") as f:
            features = json.load(f)
        print("✅ Loaded extracted_features_room.json")
    except FileNotFoundError:
        print("❌ Run dxf_parser.py first to generate extracted_features_room.json")
        exit(1)

    result = run_pipeline(features)

    print(result["formatted"])

    with open("recommendations.json", "w") as f:
        json.dump(result["recommendations"], f, indent=2)
    print(f"✅ Saved {result['total']} recommendations to recommendations.json")