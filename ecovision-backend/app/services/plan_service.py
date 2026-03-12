import os
import ezdxf
import logging
from typing import Dict, Any, Optional
from ezdxf import bbox as ez_bbox
from app.services.plan_model import generate_delta
from app.core.parsers.dxf_normalizer import DXFNormalizer

logger = logging.getLogger(__name__)


def apply_delta_to_dxf(original_dxf: str, delta_output: Dict[str, Any], output_dxf: str, original_context: Dict[str, Any]):
    logger.info(f"apply_delta_to_dxf START")
    logger.info(f"  original_dxf: {original_dxf}")
    logger.info(f"  output_dxf: {output_dxf}")
    
    doc = ezdxf.readfile(original_dxf)
    msp = doc.modelspace()
    delta = delta_output.get("delta", delta_output)
    
    logger.info(f"  delta content: {delta}")

    def find_furniture_by_enumerated_id(enum_id: str):
        """Find furniture item by enumerated_id - NO FALLBACK"""
        return next((f for f in original_context.get('furniture', []) if f.get('enumerated_id') == enum_id), None)

    def find_room_by_enumerated_id(enum_id: str):
        """Find room by enumerated_id - NO FALLBACK"""
        return next((r for r in original_context.get('rooms', []) if r.get('id') == enum_id), None)

    def get_available_furniture_ids():
        """Get list of all available furniture IDs"""
        return [f.get('enumerated_id') for f in original_context.get('furniture', [])]

    def get_available_room_ids():
        """Get list of all available room IDs"""
        return [r.get('id') for r in original_context.get('rooms', [])]

    # Adds
    for add_item in delta.get("added_ids", []) + delta.get("added", []):
        try:
            b_name = add_item.get("block_name") or add_item.get("type")
            if b_name == "sofa": b_name = "sofasmall"
            target_room_id = add_item.get("room_id")
            
            target_room = None
            if target_room_id:
                target_room = find_room_by_enumerated_id(target_room_id)
                if not target_room:
                    available_rooms = get_available_room_ids()
                    logger.warning(f"Add: Room '{target_room_id}' does not exist. Available rooms: {available_rooms}")
                    continue
            else:
                # If no room specified, use first room as fallback
                target_room = original_context.get('rooms', [{}])[0]

            if target_room:
                pos_x, pos_y = target_room['centroid']
            else:
                logger.warning(f"Add: No target room found for {b_name}")
                continue

            if b_name in doc.blocks:
                msp.add_blockref(b_name, (pos_x, pos_y))
                logger.info(f"Added block {b_name} to {target_room_id}")
            else:
                msp.add_lwpolyline([
                    (pos_x-5, pos_y-5), (pos_x+5, pos_y-5), (pos_x+5, pos_y+5), (pos_x-5, pos_y+5), (pos_x-5, pos_y-5)
                ], dxfattribs={'color': 1})
                logger.info(f"Added polyline {b_name} to {target_room_id}")
        except Exception as e:
            logger.error(f"Error adding {b_name}: {str(e)}")
            continue

    # Build a map of enumerated_id -> DXF handle using original_context
    # This ensures we use the SAME enumeration as the backend analysis
    furniture_enum_to_handle = {}
    for furn in original_context.get('furniture', []):
        enum_id = furn.get('enumerated_id')
        if enum_id:
            furniture_enum_to_handle[enum_id] = None  # Will be filled from DXF
    
    # Now extract all furniture from DXF and match by position/type to find handles
    # We use the backend's enumeration order as ground truth
    dxf_furniture_list = []
    for ent in msp.query("INSERT"):
        try:
            handle = ent.dxf.handle
            x = float(ent.dxf.insert.x)
            y = float(ent.dxf.insert.y)
            raw_name = (ent.dxf.name or "").lower()
            if raw_name.startswith("*"):
                continue
            normalized_type = DXFNormalizer.normalize_furniture_name(raw_name)
            dxf_furniture_list.append({
                'handle': handle,
                'raw_name': raw_name,
                'type': normalized_type,
                'x': x,
                'y': y
            })
        except Exception as e:
            logger.debug(f"Error extracting furniture: {e}")
    
    # Match DXF items to backend furniture by type and position
    # First pass: count each type in DXF (same as backend)
    dxf_type_counts = {}
    for item in dxf_furniture_list:
        furn_type = item["type"]
        dxf_type_counts[furn_type] = dxf_type_counts.get(furn_type, 0) + 1
    
    # Second pass: assign using backend's enumeration order
    dxf_type_counters = {}
    for item in dxf_furniture_list:
        furn_type = item["type"]
        if dxf_type_counters.get(furn_type) is None:
            dxf_type_counters[furn_type] = 0
        dxf_type_counters[furn_type] += 1
        count = dxf_type_counters[furn_type]
        
        if dxf_type_counts[furn_type] > 1:
            enum_id = f"{furn_type}{count}"
        else:
            enum_id = furn_type
        
        # Store the handle for this enumerated_id
        if enum_id in furniture_enum_to_handle:
            furniture_enum_to_handle[enum_id] = item['handle']
    
    logger.info(f"Matched {len(furniture_enum_to_handle)} items to DXF handles")
    logger.info(f"Enumerated furniture IDs: {list(furniture_enum_to_handle.keys())}")
    
    # Resize
    for resize in delta.get("resized", []):
        target_enum_id = resize.get("id") or resize.get("enumerated_id")
        try:
            if target_enum_id not in furniture_enum_to_handle:
                logger.error(f"❌ '{target_enum_id}' does not exist. Available: {list(furniture_enum_to_handle.keys())}")
                continue
            
            handle = furniture_enum_to_handle[target_enum_id]
            if not handle:
                logger.error(f"❌ No handle for '{target_enum_id}'")
                continue
                
            entity = doc.entitydb.get(handle)
            if not entity or entity.dxftype() != "INSERT":
                logger.error(f"❌ Invalid entity for '{target_enum_id}'")
                continue
            
            new_w = float(resize.get("new_width", 1.0))
            if new_w <= 0:
                logger.error(f"❌ Invalid width {new_w} for '{target_enum_id}'")
                continue
            
            bbox_before = ez_bbox.extents([entity])
            if not bbox_before.has_data:
                logger.error(f"❌ Cannot measure '{target_enum_id}'")
                continue
            
            current_w = bbox_before.size.x
            if current_w <= 0:
                logger.error(f"❌ Invalid current width {current_w} for '{target_enum_id}'")
                continue
            
            # Incremental scaling: add the difference instead of multiplying
            # This prevents huge jumps with large scale factors
            scale_diff = (new_w - current_w) / current_w
            scale_factor = 1.0 + (scale_diff * 0.5)  # Apply 50% of the change for gentler scaling
            
            logger.info(f"Resizing '{target_enum_id}': current={current_w}, target={new_w}, scale_factor={scale_factor}")
            
            center_before = bbox_before.center
            
            entity.dxf.xscale *= scale_factor
            entity.dxf.yscale *= scale_factor
            
            bbox_after = ez_bbox.extents([entity])
            center_after = bbox_after.center
            
            dx_center = center_after.x - center_before.x
            dy_center = center_after.y - center_before.y
            
            entity.dxf.insert = (
                entity.dxf.insert.x - dx_center,
                entity.dxf.insert.y - dy_center,
                entity.dxf.insert.z
            )
            logger.info(f"✅ Resized '{target_enum_id}' (scale: {scale_factor})")
            
        except Exception as e:
            logger.error(f"Error resizing {target_enum_id}: {str(e)}")
            continue

    # Moves
    for move in delta.get("moved", []):
        target_enum_id = move.get("id") or move.get("enumerated_id")
        try:
            if target_enum_id not in furniture_enum_to_handle:
                logger.error(f"❌ '{target_enum_id}' not found. Available: {list(furniture_enum_to_handle.keys())}")
                continue
            
            handle = furniture_enum_to_handle[target_enum_id]
            if not handle:
                logger.error(f"❌ No handle for '{target_enum_id}'")
                continue
            
            entity = doc.entitydb.get(handle)
            if not entity:
                logger.error(f"❌ Invalid entity for '{target_enum_id}'")
                continue
            
            # Get movement values
            dx = float(move.get("dx", 0))
            dy = float(move.get("dy", 0))
            
            logger.info(f"Moving '{target_enum_id}' by dx={dx}, dy={dy}")
            
            # Apply translation
            if hasattr(entity.dxf, 'insert'):
                old_pos = entity.dxf.insert
                new_x = old_pos.x + dx
                new_y = old_pos.y + dy
                entity.dxf.insert = (new_x, new_y, old_pos.z)
                logger.info(f"  Old pos: ({old_pos.x}, {old_pos.y}), New pos: ({new_x}, {new_y})")
            else:
                entity.translate(dx, dy, 0)
                logger.info(f"  Translated entity")
            
            logger.info(f"✅ Moved '{target_enum_id}'")
            
        except Exception as e:
            logger.error(f"❌ Error moving {target_enum_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            continue

    # Deletes
    logger.info(f"=== DELETE OPERATION ===")
    logger.info(f"Available IDs: {list(furniture_enum_to_handle.keys())}")
    
    for item_enum_id in delta.get("removed_ids", []):
        try:
            if item_enum_id not in furniture_enum_to_handle:
                logger.error(f"❌ '{item_enum_id}' does not exist. Available: {list(furniture_enum_to_handle.keys())}")
                continue
            
            handle = furniture_enum_to_handle[item_enum_id]
            if not handle:
                logger.error(f"❌ No handle for '{item_enum_id}'")
                continue
            
            entity = doc.entitydb.get(handle)
            if not entity:
                logger.error(f"❌ Invalid entity for '{item_enum_id}'")
                continue
            
            msp.delete_entity(entity)
            logger.info(f"✅ Deleted '{item_enum_id}'")
            
        except Exception as e:
            logger.error(f"Error deleting {item_enum_id}: {str(e)}")
            continue

    # Save edited DXF
    try:
        os.makedirs(os.path.dirname(output_dxf), exist_ok=True)
        doc.saveas(output_dxf)
        logger.info(f"✅ Saved to: {output_dxf}")
    except Exception as e:
        logger.error(f"❌ Failed to save: {str(e)}")
        raise


def process_command_and_apply(original_dxf: str, command: str, context: Dict[str, Any], output_dir: str, ai_url: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"\n{'='*60}")
    logger.info(f"🔄 START: process_command_and_apply")
    logger.info(f"Command: {command}")
    logger.info(f"Context has {len(context.get('furniture', []))} furniture, {len(context.get('rooms', []))} rooms")
    
    delta = generate_delta(command, context, ai_url=ai_url)
    logger.info(f"Generated delta: {delta}")
    
    base_name = os.path.splitext(os.path.basename(original_dxf))[0]
    edited_path = os.path.join(output_dir, f"{base_name}_edited.dxf")
    
    logger.info(f"Calling apply_delta_to_dxf with edited_path: {edited_path}")
    apply_delta_to_dxf(original_dxf, delta, edited_path, context)
    
    logger.info(f"✅ DONE: process_command_and_apply")
    logger.info(f"{'='*60}\n")
    return {"delta": delta, "edited_path": edited_path}
