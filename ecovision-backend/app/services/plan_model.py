import json
import re
import requests
from typing import Dict, Any, Optional


def prepare_prompt(command: str, context: Dict[str, Any]) -> str:
    room_summary = [f"{r['type']}({r['id']}) Size:[{r.get('width',0)}x{r.get('height',0)}]" for r in context.get('rooms', [])]
    furn_summary = [f"{f['type']}({f['id']}) at {f['centroid']}" for f in context.get('furniture', [])]
    context_str = f"ROOMS: {', '.join(room_summary)}\nFURNITURE: {', '.join(furn_summary)}"

    prompt = (
        "### System:\n"
        "You are a CAD Assistant. Based on the JSON context, output a 'delta' JSON. "
        "You MUST use the EXACT 'width' and 'height' from the Context Size:[WxH] "
        "for 'old_width' and 'old_height'. "
        "If the user asks to resize (e.g. 50% larger), you MUST compute "
        "new_width = old_width * scale and new_height = old_height * scale.\n\n"
        "### Context:\n" + context_str + "\n\n"
        "### User:\n" + (command or "") + "\n\n"
        "### Assistant:\n"
    )
    return prompt


def call_external_model(ai_url: str, command: str, context: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    payload = {"command": command, "context": context}
    resp = requests.post(ai_url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("delta") or data


def parse_simple_command(command: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cmd = (command or "").strip().lower()
    if not cmd:
        return {"status": "empty", "reason": "no command provided"}

    m = re.match(r"move (?:the )?(?P<target>[a-z0-9_\-]+) (?P<amount>-?\d+(?:\.\d+)?) ?(?:units )?(?P<dir>left|right|up|down)", cmd)
    if m:
        target = m.group("target")
        amount = float(m.group("amount"))
        direction = m.group("dir")
        dx = 0.0; dy = 0.0
        if direction == "left": dx = -amount
        elif direction == "right": dx = amount
        elif direction == "up": dy = amount
        elif direction == "down": dy = -amount

        furn = context.get("furniture", [])
        match = next((f for f in furn if target in (f.get("type", "") or "") or target in f.get("id", "")), None)
        if match:
            return {"status": "ok", "delta": {"moved": [{"id": match["id"], "dx": dx, "dy": dy}]}}
        return {"status": "invalid", "reason": f"'{target}' does not exist - cannot move invalid item", "target": target}

    m = re.match(r"add (?:a |an )?(?P<type>[a-z0-9_\-]+) (?:to|in) (?P<room>[a-z0-9_\-]+)", cmd)
    if m:
        btype = m.group("type")
        room = m.group("room")
        rooms = context.get("rooms", [])
        rmatch = next((r for r in rooms if room in (r.get("type", "") or "") or room == r.get("id")), None)
        if rmatch:
            return {"status": "ok", "delta": {"added": [{"type": btype, "room_id": rmatch["id"]}]}}
        return {"status": "ok", "delta": {"added": [{"type": btype}]}}

    m = re.match(r"remove (?:the )?(?P<target>[a-z0-9_\-]+)", cmd)
    if m:
        target = m.group("target")
        furn = context.get("furniture", [])
        match = next((f for f in furn if target in (f.get("type", "") or "") or target in f.get("id", "")), None)
        if match:
            return {"status": "ok", "delta": {"removed_ids": [match["id"]]}}
        return {"status": "invalid", "reason": f"'{target}' does not exist - cannot remove invalid item", "target": target}

    m = re.match(r"resize (?:the )?(?P<target>[a-z0-9_\-]+) to (?P<number>\d+(?:\.\d+)?)", cmd)
    if m:
        target = m.group("target")
        number = float(m.group("number"))
        furn = context.get("furniture", [])
        match = next((f for f in furn if target in (f.get("type", "") or "") or target in f.get("id", "")), None)
        if match:
            return {"status": "ok", "delta": {"resized": [{"id": match["id"], "new_width": number}]}}
        return {"status": "invalid", "reason": f"'{target}' does not exist - cannot resize invalid item", "target": target}

    return {"status": "unrecognized", "reason": "unrecognized command - use: move/remove/add/resize"}


def generate_delta(command: str, context: Dict[str, Any], ai_url: Optional[str] = None) -> Dict[str, Any]:
    if ai_url:
        return call_external_model(ai_url, command, context)

    parsed = parse_simple_command(command, context)

    # parsed is a structured result with status
    if isinstance(parsed, dict):
        status = parsed.get("status")
        if status == "ok":
            return parsed.get("delta", {})
        # For empty / invalid / unrecognized / cannot_parse, return an explicit error-shaped dict
        return {"error": status or "unknown", "message": parsed.get("reason", "")}

    # Fallback (shouldn't happen) — return empty delta
    return {}
