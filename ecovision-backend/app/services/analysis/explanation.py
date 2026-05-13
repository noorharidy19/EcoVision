"""
EcoVision - Floor Plan Explanation (Merged Final Version)
==========================================================
Architecture: Hybrid — Python pre-computes all facts, LLM only writes prose.
Validator:    Strong — checks hallucinated directions, missed rooms,
              wrong concern flags, with retry on failure.

Best of both worlds:
  - explanation.py          → factual accuracy (pre-computed concerns)
  - floorplan_pure_llm.py   → strong validator + retry loop
"""

from groq import Groq
from collections import Counter
import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────
# LOAD CONFIG
# ─────────────────────────────────────────────

_CFG_PATH = Path(__file__).parent / "config.json"

with open(_CFG_PATH, "r", encoding="utf-8") as _f:
    CFG = json.load(_f)

LLM_MODEL        = CFG["llm"]["model"]
LLM_TEMPERATURE  = CFG["llm"]["temperature"]
GROQ_API_KEY     = CFG["llm"]["groq_api_key"]

_groq_client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

SERVICE_KEYWORDS = {"toilet", "bathroom", "wc", "bath", "lavatory"}


def _is_service(room_name: str) -> bool:
    return any(kw in room_name.lower() for kw in SERVICE_KEYWORDS)


# ─────────────────────────────────────────────
# STEP 1 — BUILD ROOM SUMMARY LINES
# Python resolves every direction count and rating label.
# The LLM receives finished sentences, not raw fields.
# ─────────────────────────────────────────────

def _build_room_lines(features: dict) -> str:
    lines = []
    for r in features["rooms"]:
        name       = r["name"]
        area       = r["area_m2"]
        win_count  = r["window_count"]
        rating     = r["window_direction_rating"]
        all_dirs   = r.get("all_window_directions", [])
        primary    = all_dirs[0].upper() if all_dirs else "NONE"

        # ── Exact per-direction counts (no LLM collapsing) ──────────────
        if all_dirs:
            dir_counts   = Counter(d.upper() for d in all_dirs)
            dir_parts    = [f"{cnt} {d}-facing" for d, cnt in dir_counts.items()]
            dir_sentence = f"Has {win_count} window(s): {', '.join(dir_parts)}."
        elif rating != "no_window":
            dir_sentence = f"Has {win_count} window(s), all {primary}-facing."
        else:
            dir_sentence = "Has no windows."

        # ── Window sizes ─────────────────────────────────────────────────
        win_sizes = [
            f"{d['width_mm']}mm"
            for d in r.get("window_dimensions", [])
            if d.get("width_mm")
        ]
        size_str = f" ({', '.join(win_sizes)})" if win_sizes else ""

        # ── Window-to-floor ratio ────────────────────────────────────────
        total_win_area = sum(
            (d["width_mm"] / 1000) * (d["height_mm"] / 1000)
            for d in r.get("window_dimensions", [])
            if d.get("width_mm") and d.get("height_mm")
        )
        ratio = (total_win_area / area * 100) if area > 0 else 0

        # ── Orientation label — correct reason per room type ────────────
        if rating == "good":
            rating_label = "well oriented — low heat gain"
        elif rating == "no_window":
            rating_label = "no window"
        elif rating == "poor":
            if _is_service(name) and primary == "N":
                rating_label = (
                    "poorly oriented — north-facing causes poor natural ventilation "
                    "and odor issues (not a heat gain problem)"
                )
            else:
                rating_label = "poorly oriented — causes excessive heat gain"
        elif rating == "acceptable":
            if primary == "W":
                rating_label = (
                    "acceptably oriented but faces west — afternoon sun causes heat gain"
                    if not _is_service(name)
                    else "acceptably oriented but faces west — some afternoon heat gain, odor exhaust manageable"
                )
            elif primary == "N" and _is_service(name):
                rating_label = "acceptably oriented — faces prevailing breeze, monitor odor exhaust"
            elif primary == "E":
                rating_label = "acceptably oriented — morning sun only, manageable heat gain"
            else:
                rating_label = "acceptably oriented"
        else:
            rating_label = rating

        lines.append(
            f"- {name}: {area}m² | {dir_sentence}{size_str}"
            f" | window-to-floor ratio: {ratio:.0f}%"
            f" | orientation: {rating_label}"
            f" | high_use={r['is_high_use']} | circulation={r['is_circulation']}"
        )

    return "\n".join(lines)


# ─────────────────────────────────────────────
# STEP 2 — PRE-COMPUTE KEY CONCERNS IN PYTHON
# LLM is told exactly what to write — it cannot invent or miss anything.
# ─────────────────────────────────────────────

def _build_concerns_block(features: dict) -> str:
    bullets = []

    for r in features["rooms"]:
        rating   = r["window_direction_rating"]
        name     = r["name"]
        all_dirs = r.get("all_window_directions", [])
        primary  = all_dirs[0].upper() if all_dirs else "NONE"

        if rating == "poor" and (r["is_high_use"] or _is_service(r["name"])):
            # Only flag poor orientation for HIGH-USE rooms (bedrooms, living, master bathroom etc.)
            # Low-use service rooms (bathroom) are noted in ROOM DIRECTIONS but not KEY CONCERNS.
            if _is_service(name) and primary == "N":
                bullets.append(
                    f"- {name}: north-facing causes poor ventilation and odor issues. "
                    f"Recommend a mechanical exhaust fan or relocating the window to a south-facing wall."
                )
            else:
                bullets.append(
                    f"- {name}: poorly oriented ({primary}-facing) causes excessive heat gain. "
                    f"Recommend external shading or high-performance glazing."
                )

        elif rating == "no_window" and r["is_high_use"] and not r["is_circulation"]:
            bullets.append(
                f"- {name}: no window causes poor natural light and ventilation. "
                f"Recommend adding a window or a light well."
            )

        elif rating != "no_window" and r["is_high_use"] and not r["is_circulation"]:
            # Low daylight ratio check
            total_win_area = sum(
                (d["width_mm"] / 1000) * (d["height_mm"] / 1000)
                for d in r.get("window_dimensions", [])
                if d.get("width_mm") and d.get("height_mm")
            )
            ratio = (total_win_area / r["area_m2"] * 100) if r["area_m2"] > 0 else 0
            if ratio < 10:
                bullets.append(
                    f"- {name}: window-to-floor ratio is low ({ratio:.0f}%), "
                    f"resulting in insufficient natural light."
                )

    corridor_ratio = features["corridor_area_ratio"]
    if corridor_ratio > 0.15:
        bullets.append(
            f"- Corridor ratio is {corridor_ratio * 100:.0f}% — above the recommended 15%. "
            f"Consider consolidating circulation space to reduce wasted area."
        )

    return "\n".join(bullets) if bullets else "- No major concerns identified."


# ─────────────────────────────────────────────
# STEP 3 — BUILD PROMPT
# LLM receives pre-resolved facts; its only job is prose.
# ─────────────────────────────────────────────

def _build_prompt(features: dict, retry: bool = False) -> str:
    rooms_summary  = _build_room_lines(features)
    concerns_block = _build_concerns_block(features)

    good_rooms     = [r["name"] for r in features["rooms"] if r["window_direction_rating"] == "good"]
    corridor_ratio = features["corridor_area_ratio"]
    corridor_note  = (
        f"Corridor ratio is {corridor_ratio * 100:.0f}% — above recommended 15%"
        if corridor_ratio > 0.15
        else f"Corridor ratio is {corridor_ratio * 100:.0f}% — within acceptable range"
    )

    correction = (
        "\n\n⚠️ CORRECTION REQUIRED: Your previous response had errors. "
        "Re-read EVERY room entry. Match window directions EXACTLY. "
        "Write a SEPARATE sentence per room — never group two rooms. "
        "Only use concerns listed in PRE-COMPUTED KEY CONCERNS.\n"
        if retry else ""
    )

    return f"""{correction}You are a sustainable architecture advisor writing a floor plan summary for a client.

═══════════════════════════════════════
BUILDING OVERVIEW:
═══════════════════════════════════════
City:             {features['city']}
Climate:          {features['climate'].replace('_', ' ')}
North arrow:      {features['north_arrow_direction']}
Total area:       {features['total_floor_area_m2']}m²
Total rooms:      {features['num_rooms']}
Total windows:    {features['total_windows']}
Total doors:      {features['total_doors']}
Corridor ratio:   {corridor_ratio * 100:.0f}% of total area

═══════════════════════════════════════
ROOM-BY-ROOM BREAKDOWN:
═══════════════════════════════════════
{rooms_summary}

CRITICAL ACCURACY RULES:
- Each room entry states EXACTLY how many windows face each direction.
- Reflect these exact counts. Never say "north-facing windows" if only 1 of 3 is north.
- Correct: "The Gym has one north-facing window and two west-facing windows."
- Wrong:   "The Gym has north-facing windows." ← DO NOT DO THIS.
- Write ONE sentence per room. Never group two rooms together.
- For north-facing SERVICE ROOMS (toilets/bathrooms): the problem is poor ventilation
  and odor, NOT heat gain.

═══════════════════════════════════════
KEY FINDINGS:
═══════════════════════════════════════
Well-oriented rooms:   {', '.join(good_rooms) if good_rooms else 'none'}
Corridor assessment:   {corridor_note}

PRE-COMPUTED KEY CONCERNS — use these EXACTLY:
(Do NOT add, remove, invent, or rephrase. Cover every bullet below.)
{concerns_block}

═══════════════════════════════════════
TASK — Write with EXACTLY these 4 section headers:
═══════════════════════════════════════

1. OVERVIEW
   2 sentences: building size, number of rooms, general layout quality.

2. ROOM DIRECTIONS
   One sentence per room — NEVER group two rooms in one sentence.
   State the exact window direction(s) and orientation assessment.
   Use exact counts from the data (e.g. "one north-facing, two west-facing").

3. KEY STRENGTHS
   What is working well (good orientations, adequate windows, no corridor waste).
   Only call a room "well oriented" if its orientation field says "well oriented".

4. KEY CONCERNS
   Rewrite the PRE-COMPUTED KEY CONCERNS above in professional prose.
   Cover EVERY bullet. Do NOT add or invent concerns not in the list.
   IMPORTANT: Only rooms listed in PRE-COMPUTED KEY CONCERNS belong here.
   If a room has poor orientation but is NOT in that list (e.g. low-use bathrooms),
   do NOT add it to KEY CONCERNS — it was already described in ROOM DIRECTIONS.

RULES:
- Clear professional English for a client (not an engineer).
- The "one sentence per room" rule applies to ALL sections, not just ROOM DIRECTIONS.
- Use DEFINITIVE language: write "causes", never "may cause" or "may lead to".
- Do NOT use raw field names like 'window_direction_rating' or 'is_high_use'.
- A corridor ratio of 0% is always a STRENGTH — never flag it as a concern.
- Keep total length under 350 words.
- Use section headers EXACTLY: OVERVIEW, ROOM DIRECTIONS, KEY STRENGTHS, KEY CONCERNS.
"""


# ─────────────────────────────────────────────
# STEP 4 — STRONG VALIDATOR (from pure LLM version)
# Returns summary if valid, None if retry needed.
# ─────────────────────────────────────────────

def _validate_summary(summary: str, features: dict):
    actual_rooms  = [r["name"].lower() for r in features["rooms"]]
    summary_lower = summary.lower()
    has_warning   = False

    # 1. All rooms must be mentioned
    mentioned     = [r for r in actual_rooms if r in summary_lower]
    not_mentioned = [r for r in actual_rooms if r not in mentioned]
    if not_mentioned:
        print(f"   ⚠️  WARNING: Rooms not mentioned: {not_mentioned}")
        has_warning = True

    # 2. Poor high-use rooms must be flagged
    poor_rooms = [
        r["name"] for r in features["rooms"]
        if r["window_direction_rating"] == "poor" and r["is_high_use"]
    ]
    for room in poor_rooms:
        if room.lower() not in summary_lower:
            print(f"   ⚠️  WARNING: Poor high-use room '{room}' not mentioned")
            has_warning = True

    # 3. No-window high-use non-circulation rooms must be flagged
    no_win_rooms = [
        r["name"] for r in features["rooms"]
        if r["window_direction_rating"] == "no_window"
        and r["is_high_use"]
        and not r["is_circulation"]
    ]
    for room in no_win_rooms:
        if room.lower() not in summary_lower:
            print(f"   ⚠️  WARNING: No-window high-use room '{room}' not mentioned")
            has_warning = True

    # 4. Direction hallucination check
    opposites = {"N": ["south"], "S": ["north"], "E": ["west"], "W": ["east"]}
    for r in features["rooms"]:
        name      = r["name"].lower()
        direction = r["window_direction"].upper()
        wrong     = opposites.get(direction, [])
        if name in summary_lower and wrong:
            idx     = summary_lower.find(name)
            context = summary_lower[max(0, idx - 10): idx + 120]
            for w in wrong:
                if w in context:
                    print(
                        f"   ⚠️  WARNING: '{r['name']}' direction hallucinated — "
                        f"actual={direction}, found '{w}' nearby"
                    )
                    has_warning = True

    concern_section = (
        summary_lower.split("key concerns")[-1]
        if "key concerns" in summary_lower else ""
    )

    # 5. Circulation/low-use no-window rooms must NOT appear in KEY CONCERNS
    should_not_flag_nowin = [
        r["name"].lower() for r in features["rooms"]
        if r["window_direction_rating"] == "no_window"
        and (r["is_circulation"] or not r["is_high_use"])
    ]
    for room in should_not_flag_nowin:
        if room in concern_section:
            print(f"   WARNING: '{room}' incorrectly in KEY CONCERNS (no-window but not high-use/circulation)")
            has_warning = True

    print(f"   ✅ Rooms mentioned: {mentioned}")
    if not_mentioned:
        print(f"   ⚠️  Rooms NOT mentioned: {not_mentioned}")

    if has_warning:
        print("   🔄 Validation failed — will retry")
        return None

    print("   ✅ Validation passed — no issues found")
    return summary


# ─────────────────────────────────────────────
# STEP 5 — GENERATE WITH RETRY
# ─────────────────────────────────────────────

def generate_floor_plan_summary(features: dict) -> str:
    last_summary = "Summary unavailable."

    for attempt in range(2):  # max 2 attempts
        is_retry = attempt == 1
        prompt   = _build_prompt(features, retry=is_retry)

        print(f"\n🤖 Attempt {attempt + 1} — Sending to {LLM_MODEL}...")
        print("─" * 50)

        try:
            response = _groq_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional sustainable architecture advisor. "
                            "Write clear, structured summaries for clients. "
                            "Always use the exact section headers provided."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=LLM_TEMPERATURE,
            )

            summary      = response.choices[0].message.content.strip()
            last_summary = summary

            print(f"📨 Raw summary:\n{summary}\n")
            print("─" * 50)

            result = _validate_summary(summary, features)
            if result is not None:
                return result  # ✅ passed

        except Exception as e:
            print(f"❌ Groq error (attempt {attempt + 1}): {e}")

    print("   ⚠️  Returning best available summary after 2 attempts")
    return last_summary


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    json_path = r"C:\Users\lenovo\Desktop\ecovision recommendation\results\rooms1 final.json"

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            features = json.load(f)
        print(f"✅ Loaded {json_path}")
    except FileNotFoundError:
        print(f"❌ File not found: {json_path} — run dxf_parser.py first")
        exit(1)

    summary = generate_floor_plan_summary(features)

    print("\n📋 FLOOR PLAN SUMMARY (Final Merged Version):")
    print("─" * 50)
    print(summary)
    print("─" * 50)

    output_path = json_path.replace(".json", "_summary_final.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary}, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {output_path}")