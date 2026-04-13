"""
EcoVision - Floor Plan Explanation
====================================
Generates a client-facing summary of the floor plan analysis.
Called after DXF parsing and architect corrections are applied.
"""

import ollama
import json


def generate_floor_plan_summary(features: dict, model: str = "mistral") -> str:

    # ── Build room details for prompt ─────────────────────────────────
    room_lines = []
    for r in features["rooms"]:
        direction   = r["window_direction"].upper() if r["window_direction"] != "none" else "no window"
        rating      = r["window_direction_rating"]   # "good" | "acceptable" | "poor" | "no_window"
        win_count   = r["window_count"]
        win_sizes   = [str(d["width_mm"]) + "mm" for d in r.get("window_dimensions", []) if d.get("width_mm")]
        size_str    = f" ({', '.join(win_sizes)})" if win_sizes else ""

        # Translate rating to plain English for the prompt
        rating_label = {
            "good":       "well oriented",
            "acceptable": "acceptably oriented",
            "poor":       "poorly oriented — causes excessive heat gain",
            "no_window":  "no window",
        }.get(rating, rating)

        room_lines.append(
            f"- {r['name']}: {r['area_m2']}m² | window faces {direction}{size_str}"
            f" | {win_count} window(s) | orientation: {rating_label}"
        )

    rooms_summary = "\n".join(room_lines)

    # ── Derive summary groups from window_direction_rating ────────────
    good_rooms   = [r["name"] for r in features["rooms"] if r["window_direction_rating"] == "good"]
    poor_rooms   = [r["name"] for r in features["rooms"]
                    if r["window_direction_rating"] == "poor" and r["is_high_use"]]
    no_win_rooms = [r["name"] for r in features["rooms"]
                    if r["window_direction_rating"] == "no_window"
                    and r["is_high_use"]
                    and not r["is_circulation"]]

    prompt = f"""You are a sustainable architecture advisor writing a floor plan summary for a client.

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
Corridor ratio:   {features['corridor_area_ratio'] * 100:.0f}% of total area

═══════════════════════════════════════
ROOM-BY-ROOM BREAKDOWN:
═══════════════════════════════════════
{rooms_summary}

═══════════════════════════════════════
KEY FINDINGS:
═══════════════════════════════════════
Well-oriented rooms:              {', '.join(good_rooms) if good_rooms else 'none'}
Poorly oriented high-use rooms:   {', '.join(poor_rooms) if poor_rooms else 'none'}
High-use rooms with no window:    {', '.join(no_win_rooms) if no_win_rooms else 'none'}

═══════════════════════════════════════
TASK:
═══════════════════════════════════════
Write a professional floor plan summary for the client with these sections:

1. OVERVIEW — 2 sentences about the building size, number of rooms, and general layout quality.
2. ROOM DIRECTIONS — For each room, mention its window direction and whether it is well oriented,
   acceptable, or poor for Cairo's hot dry climate. Be specific per room.
3. KEY STRENGTHS — What is working well in this floor plan.
4. KEY CONCERNS — What needs attention (poor orientation, missing windows).

RULES:
- Write in clear professional English
- Do NOT use raw field names like 'window_direction_rating: poor'
- Translate ratings into natural language (e.g. poor orientation = 'causes excessive heat gain')
- Keep total length under 250 words
- Use the section headers exactly as shown above"""

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional sustainable architecture advisor. Write clear, structured summaries for clients."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={"temperature": 0.3}
        )
        return response["message"]["content"].strip()

    except Exception as e:
        print(f"❌ Summary error: {e}")
        return "Summary unavailable."


# ─────────────────────────────────────────────
# EXAMPLE USAGE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    try:
        with open("extracted_features_room.json", "r") as f:
            features = json.load(f)
        print("✅ Loaded extracted_features_room.json")
    except FileNotFoundError:
        print("❌ Run dxf_parser.py first")
        exit(1)

    summary = generate_floor_plan_summary(features)
    print("\n📋 FLOOR PLAN SUMMARY:")
    print("─" * 50)
    print(summary)
    print("─" * 50)

    with open("summary.json", "w") as f:
        json.dump({"summary": summary}, f, indent=2)
    print("\n✅ Saved to summary.json")