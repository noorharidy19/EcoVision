from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.file_storage import save_uploaded_file
from app.services.analysis.floorplan_processor import dxf_to_json_clustered
from app.core.dependencies import get_db
from app.models.floorplan import Floorplan
from app.models.enum import FileType
from app.models.analysis_result import AnalysisResult
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
