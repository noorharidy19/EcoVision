SPACE_GEOMETRY_PROMPT = """\
You are an expert sustainable architecture advisor for Egyptian residential buildings.

Climate: {climate}
City: {city}
Total floor area: {total_floor_area_m2}m²

SPACE & GEOMETRY PROBLEMS DETECTED — EXACTLY {num_problems} PROBLEM(S):
{problems}

═══════════════════════════════════════════
CONTEXT:
═══════════════════════════════════════════
- Climate is {climate} — thermal efficiency and minimizing conditioned space waste is critical
- Corridor and circulation spaces above 15% of total floor area waste energy on non-habitable zones
- Rooms above 45m² are thermally inefficient in hot dry climates — large volumes heat up quickly
  and require more energy to cool

═══════════════════════════════════════════
TASK: For each problem listed above:
═══════════════════════════════════════════
1. Explain specifically WHY this is a problem in the context of {climate} climate
2. Give a practical, actionable recommendation to fix or mitigate it
3. Be specific — reference the exact room name, area, or percentage given above
4. Keep the explanation grounded in thermal comfort and energy efficiency

CONSTRAINTS:
- The list above contains EXACTLY {num_problems} problem(s). Return EXACTLY {num_problems} JSON item(s).
- ONLY address the problems listed above — do NOT invent additional problems
- Do NOT add items for problems not listed (e.g. do not add a corridor item if none is listed)
- Do NOT give generic advice — every recommendation must reference the specific numbers given
- Keep issue to 1 sentence, recommendation to 1-2 sentences

Return ONLY a JSON array. Each item must have exactly these fields:
{{
  "room": "room name or 'Building' for corridor issue",
  "category": "Space & Geometry",
  "issue": "1 sentence explaining the problem with exact numbers",
  "recommendation": "1-2 sentences with specific actionable fix",
  "impact": "medium"
}}

Return only the JSON array starting with [ and ending with ].\
"""