from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
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
import json

router = APIRouter(prefix="/floorplans", tags=["Floorplans"])



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
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check authorization
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
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
