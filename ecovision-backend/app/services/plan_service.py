import os
import ezdxf
from typing import Dict, Any, Optional
from app.services.plan_model import generate_delta


def apply_delta_to_dxf(original_dxf: str, delta_output: Dict[str, Any], output_dxf: str, original_context: Dict[str, Any]):
    doc = ezdxf.readfile(original_dxf)
    msp = doc.modelspace()
    delta = delta_output.get("delta", delta_output)

    def find_real_id(input_id: str):
        if "_" not in input_id:
            match = next((f for f in original_context.get('furniture', []) if f['type'] == input_id), None)
            return match['id'] if match else input_id
        return input_id

    # Adds
    for add_item in delta.get("added_ids", []) + delta.get("added", []):
        try:
            b_name = add_item.get("block_name") or add_item.get("type")
            if b_name == "sofa": b_name = "sofa_small"
            target_room_id = add_item.get("room_id")
            target_room = next((r for r in original_context.get('rooms', []) if r['id'] == target_room_id), None)
            if not target_room:
                target_type = "living_room" if "sofa" in b_name else "bathroom" if "toilet" in b_name else None
                target_room = next((r for r in original_context.get('rooms', []) if r['type'] == target_type), None)

            if target_room:
                pos_x, pos_y = target_room['centroid']
            else:
                target_room = original_context.get('rooms', [{}])[0]
                pos_x, pos_y = target_room.get('centroid', [0,0])

            if b_name in doc.blocks:
                msp.add_blockref(b_name, (pos_x, pos_y))
            else:
                msp.add_lwpolyline([
                    (pos_x-5, pos_y-5), (pos_x+5, pos_y-5), (pos_x+5, pos_y+5), (pos_x-5, pos_y+5), (pos_x-5, pos_y-5)
                ], dxfattribs={'color': 1})
        except Exception:
            continue

    # Resize
    from ezdxf import bbox as ez_bbox
    for resize in delta.get("resized", []):
        target_id = find_real_id(resize.get("id"))
        try:
            handle = target_id.split("_")[-1]
            entity = doc.entitydb.get(handle)
            if entity and entity.dxftype() == "INSERT":
                new_w = float(resize.get("new_width", 1.0))
                bbox_before = ez_bbox.extents([entity])
                if bbox_before.has_data:
                    current_w = bbox_before.size.x
                    scale_factor = new_w / current_w if current_w > 0 else 1.0
                    center_before = bbox_before.center
                    entity.dxf.xscale *= scale_factor
                    entity.dxf.yscale *= scale_factor
                    bbox_after = ez_bbox.extents([entity])
                    center_after = bbox_after.center
                    entity.dxf.insert = (
                        entity.dxf.insert.x - (center_after.x - center_before.x),
                        entity.dxf.insert.y - (center_after.y - center_before.y),
                        entity.dxf.insert.z
                    )
        except Exception:
            continue

    # Moves
    for move in delta.get("moved", []):
        target_id = move.get("id")
        real_id = target_id
        if "_" not in target_id:
            match = next((f for f in original_context.get('furniture', []) if f['type'] == target_id), None)
            if match:
                real_id = match['id']
        try:
            handle = real_id.split("_")[-1]
            entity = doc.entitydb.get(handle)
            if entity:
                dx, dy = float(move.get("dx", 0)), float(move.get("dy", 0))
                if hasattr(entity.dxf, 'insert'):
                    old_pos = entity.dxf.insert
                    entity.dxf.insert = (old_pos.x + dx, old_pos.y + dy, old_pos.z)
                else:
                    entity.translate(dx, dy, 0)
        except Exception:
            continue

    # Deletes
    for item_id in delta.get("removed_ids", []):
        target_id = find_real_id(item_id)
        try:
            handle = target_id.split("_")[-1]
            entity = doc.entitydb.get(handle)
            if entity:
                msp.delete_entity(entity)
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_dxf), exist_ok=True)
    doc.saveas(output_dxf)


def process_command_and_apply(original_dxf: str, command: str, context: Dict[str, Any], output_dir: str, ai_url: Optional[str] = None) -> Dict[str, Any]:
    delta = generate_delta(command, context, ai_url=ai_url)
    base_name = os.path.splitext(os.path.basename(original_dxf))[0]
    edited_path = os.path.join(output_dir, f"{base_name}_edited.dxf")
    apply_delta_to_dxf(original_dxf, delta, edited_path, context)
    return {"delta": delta, "edited_path": edited_path}
