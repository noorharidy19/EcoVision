from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import io

# Make matplotlib optional so the server can run without image/PDF export support
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False
from sqlalchemy.orm import Session
from app.services.file_storage import save_uploaded_file
from app.services.analysis.floorplan_processor import dxf_to_json_clustered
from app.core.database import get_db
from app.models.floorplan import Floorplan
from app.models.enum import FileType
from app.models.analysis_result import AnalysisResult
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.project import Project
from app.services.plan_service import process_command_and_apply
import json
import os
from fastapi import BackgroundTasks
from ezdxf import bbox
import ezdxf

router = APIRouter(prefix="/floorplans", tags=["Floorplans"])


@router.get("/{floorplan_id}/export")
def export_floorplan(
    floorplan_id: int,
    format: str = "dxf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export floorplan in requested format. Supported formats: dxf, dwg, png, pdf."""
    floorplan = db.query(Floorplan).filter(Floorplan.id == floorplan_id).first()
    if not floorplan:
        raise HTTPException(status_code=404, detail="Floorplan not found")

    # Authorization: require project ownership or admin or collaborator
    project = db.query(Project).filter(Project.id == floorplan.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    is_admin = str(role_val).upper() == "ADMIN"
    is_owner = project.user_id == current_user.id
    if not is_admin and not is_owner:
        # try collaborator table if exists
        try:
            from app.models.project_collab import ProjectCollaborator
            collaborator = db.query(ProjectCollaborator).filter(
                ProjectCollaborator.project_id == project.id,
                ProjectCollaborator.user_id == current_user.id
            ).first()
            if not collaborator:
                raise HTTPException(status_code=403, detail="Not authorized")
        except Exception:
            raise HTTPException(status_code=403, detail="Not authorized")

    file_path = floorplan.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Source file not found on server")

    fmt = (format or "dxf").lower()
    if fmt in ("dxf", "dwg"):
        # serve original file
        filename = os.path.basename(file_path)
        return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")

    if fmt in ("png", "pdf"):
        if not HAS_MATPLOTLIB:
            raise HTTPException(status_code=501, detail="Server missing 'matplotlib' dependency required to render PNG/PDF exports. Install it in the backend environment (pip install matplotlib).")

        try:
            doc = ezdxf.readfile(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read DXF: {e}")

        try:
            msp = doc.modelspace()
            fig = plt.figure(figsize=(12, 12))
            ax = fig.add_axes([0, 0, 1, 1])
            ctx = RenderContext(doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(msp, finalize=True)

            buf = io.BytesIO()
            if fmt == "png":
                plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
                media_type = "image/png"
                ext = "png"
            else:
                plt.savefig(buf, format="pdf", bbox_inches='tight')
                media_type = "application/pdf"
                ext = "pdf"
            plt.close(fig)
            buf.seek(0)
            return StreamingResponse(buf, media_type=media_type, headers={"Content-Disposition": f"attachment; filename=\"{project.name or 'floorplan'}.{ext}\""})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render export: {e}")

    raise HTTPException(status_code=400, detail="Unsupported export format")



@router.post("/upload")
def upload_floorplan(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Only DXF files supported")

    saved_path = save_uploaded_file(file)

    try:
        parsed = dxf_to_json_clustered(saved_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse DXF: {e}")

    try:
        floorplan = Floorplan(
            project_id=project_id,
            file_path=saved_path,
            file_type=FileType.DXF
            
        )
        db.add(floorplan)
        db.flush()

        
       

        db.commit()
        db.refresh(floorplan)
       

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "floorplan_id": floorplan.id,
        
    }


@router.get("/project/{project_id}")
def get_floorplan_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get floorplan for a project"""
    from app.models.project_collab import ProjectCollaborator
    
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check authorization
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    is_admin = str(role_val).upper() == "ADMIN"
    is_owner = project.user_id == current_user.id
    is_collaborator = False
    
    if not is_admin and not is_owner:
        # Check if user is a collaborator
        collaborator = db.query(ProjectCollaborator).filter(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == current_user.id
        ).first()
        is_collaborator = collaborator is not None
    
    if not is_admin and not is_owner and not is_collaborator:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get floorplan
    floorplan = db.query(Floorplan).filter(Floorplan.project_id == project_id).first()
    if not floorplan:
        raise HTTPException(status_code=404, detail="No floorplan found for this project")
    
    return {
        "id": floorplan.id,
        "project_id": floorplan.project_id,
        "file_path": floorplan.file_path,
        "file_type": floorplan.file_type,
        "json_data": floorplan.json_data,
        "version": floorplan.version
    }



@router.post("/{floorplan_id}/ai_edit")
def ai_edit_floorplan(
    floorplan_id: int,
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Endpoint: run AI command against a DXF floorplan, return delta and saved edited file.
    payload expected: { "command": "move the toilet 100 left", "ai_url": "https://..." (optional) }
    If no `ai_url` provided, a demo delta will be returned.
    """
    project = db.query(Project).filter(Project.id == db.query(Floorplan).filter(Floorplan.id == floorplan_id).first().project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # authorization check
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    floorplan = db.query(Floorplan).filter(Floorplan.id == floorplan_id).first()
    if not floorplan:
        raise HTTPException(status_code=404, detail="Floorplan not found")

    dxf_path = floorplan.file_path
    try:
        context = dxf_to_json_clustered(dxf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse DXF: {e}")

    cmd = payload.get("command") if isinstance(payload, dict) else None
    ai_url = payload.get("ai_url") if isinstance(payload, dict) else None

    if not cmd or not cmd.strip():
        return {"success": False, "error": "Command cannot be empty"}

    edited_dir = os.path.abspath(os.path.join(os.getcwd(), "uploaded_files", "edited"))
    os.makedirs(edited_dir, exist_ok=True)

    try:
        result = process_command_and_apply(dxf_path, cmd, context, edited_dir, ai_url=ai_url)
    except Exception as e:
        return {"success": False, "error": str(e)}

    edited_path = result.get("edited_path")
    delta = result.get("delta")
    
    # Check if delta has actual changes (or has an error)
    has_error = isinstance(delta, dict) and "error" in delta
    has_changes = isinstance(delta, dict) and any(k in delta for k in ["moved", "removed_ids", "added", "resized"])
    
    if has_error:
        return {"success": False, "error": delta.get("message", "Invalid command")}
    
    if not has_changes:
        return {"success": False, "error": "There is no changes"}

    # Simplify file path: just use filename in uploaded_files, not full path
    file_name = os.path.basename(edited_path)
    file_url = f"/files/{file_name}"

    # If caller asked to confirm, UPDATE the existing Floorplan with new version
    if isinstance(payload, dict) and payload.get("confirm"):
        try:
            # parse new context from edited DXF
            new_context = dxf_to_json_clustered(edited_path)

            # UPDATE existing floorplan: increment version and update file_path + json_data
            new_version = (floorplan.version or 1) + 1
            floorplan.version = new_version
            floorplan.file_path = edited_path
            floorplan.json_data = new_context

            db.commit()
            db.refresh(floorplan)

            return {"success": True, "edited_file": file_url, "floorplan_id": floorplan.id, "new_version": floorplan.version}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to save version: {e}"}

    # default response (no confirm): return edited file URL
    return {"success": True, "edited_file": file_url}


def _apply_delta_to_dxf(original_dxf, delta_output, output_dxf, original_context):
    """Simplified apply function: supports moved, removed_ids, and added simple placeholders.
    This mirrors a minimal behavior from the developer's modeltest script.
    """
    doc = ezdxf.readfile(original_dxf)
    msp = doc.modelspace()
    delta = delta_output.get("delta", delta_output)

    def find_real_id(input_id):
        if "_" not in input_id:
            match = next((f for f in original_context.get('furniture', []) if f['type'] == input_id), None)
            return match['id'] if match else input_id
        return input_id

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
            if entity and hasattr(entity.dxf, 'insert'):
                dx, dy = float(move.get('dx', 0)), float(move.get('dy', 0))
                old = entity.dxf.insert
                entity.dxf.insert = (old.x + dx, old.y + dy, old.z)
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

    # Adds (simple placeholders at room centroids)
    for add_item in delta.get("added_ids", []) + delta.get("added", []):
        try:
            room_id = add_item.get("room_id")
            room = next((r for r in original_context.get('rooms', []) if r['id'] == room_id), None)
            if room:
                pos_x, pos_y = room['centroid']
            else:
                pos_x, pos_y = (0, 0)
            # draw small rectangle placeholder
            msp.add_lwpolyline([
                (pos_x-50, pos_y-50), (pos_x+50, pos_y-50), (pos_x+50, pos_y+50), (pos_x-50, pos_y+50), (pos_x-50, pos_y-50)
            ], dxfattribs={'color': 1})
        except Exception:
            continue

    doc.saveas(output_dxf)
