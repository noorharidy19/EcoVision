from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.analysis.comfort_model import EcoVisionModelService
from app.services.analysis.floorplan_processor import dxf_to_json_clustered
from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.floorplan import Floorplan
import json
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# Initialize model service
MODEL_PATH = "C:\\Users\\Hassan Hatem\\Downloads\\EcoVision (2)\\EcoVision\\final_ecovision_model.keras"
model_service = None

try:
    logger.info(f"Loading model from: {MODEL_PATH}")
    model_service = EcoVisionModelService(MODEL_PATH)
    logger.info("✅ Model loaded successfully!")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")

@router.get("/health")
async def health_check():
    """Check if analysis service is ready"""
    return {
        "status": "ok",
        "model_loaded": model_service is not None,
        "model_path": MODEL_PATH
    }

@router.post("/analyze-floorplan")
async def analyze_floorplan(file: UploadFile = File(...)):
    """Analyze uploaded JSON floorplan data"""
    content = await file.read()
    json_data = json.loads(content)
    
    if not model_service:
        raise HTTPException(status_code=500, detail="Model not loaded - check server logs")
    
    predictions = model_service.predict(json_data)
    return {"results": predictions}


@router.post("/project/{project_id}/comfort")
async def analyze_project_comfort(
    project_id: int,
    analysis_type: str = "both",  # "thermal", "visual", or "both"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze thermal and/or visual comfort for a project
    Uses pre-converted JSON data from floorplan table
    """
    logger.info(f"🔍 Starting analysis for project {project_id}, type: {analysis_type}")
    
    if not model_service:
        logger.error("❌ Model service not initialized")
        raise HTTPException(status_code=500, detail="Model not loaded - check server logs")
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning(f"Project {project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"✅ Project found: {project.name}")
    
    # Check if user owns project (unless admin)
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if str(role_val).upper() != "ADMIN" and project.user_id != current_user.id:
        logger.warning(f"User {current_user.id} not authorized for project {project_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    
    # Get floorplan for this project
    floorplan = db.query(Floorplan).filter(Floorplan.project_id == project_id).first()
    if not floorplan:
        logger.error(f"❌ No floorplan found for project {project_id}")
        raise HTTPException(status_code=404, detail="No floorplan found for this project")
    
    # Use stored JSON data
    if not floorplan.json_data:
        logger.warning(f"⚠️ No JSON data stored in floorplan")
        # Try to convert DXF if JSON not stored
        if not os.path.exists(floorplan.file_path):
            logger.error(f"❌ File not found: {floorplan.file_path}")
            raise HTTPException(status_code=404, detail=f"Project file not found")
        
        logger.info(f"📄 Converting DXF to JSON: {floorplan.file_path}")
        try:
            json_data = dxf_to_json_clustered(floorplan.file_path)
            # Update floorplan with JSON data
            floorplan.json_data = json_data
            db.commit()
            logger.info(f"✅ DXF converted and stored")
        except Exception as e:
            logger.error(f"❌ DXF conversion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to parse DXF: {str(e)}")
    else:
        json_data = floorplan.json_data
        logger.info(f"✅ Using stored JSON data")
    
    if not json_data.get("rooms"):
        logger.warning(f"⚠️ No rooms detected in floorplan")
        raise HTTPException(status_code=400, detail="No rooms detected in floorplan")
    
    # Run model predictions
    logger.info("🤖 Running model inference...")
    try:
        predictions = model_service.predict(json_data)
        logger.info(f"✅ Model inference complete: {predictions}")
    except Exception as e:
        logger.error(f"❌ Model inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")
    
    # Filter results based on analysis_type
    filtered_results = {}
    for orientation, scores in predictions.items():
        filtered_results[orientation] = {}
        if analysis_type in ["thermal", "both"]:
            val = scores["thermal"]
            # Convert numpy types to Python float
            if isinstance(val, (np.floating, np.integer)):
                val = float(val)
            # Values from model are like 5670, normalize to 0-1 by dividing by 10000
            
            filtered_results[orientation]["thermal"] = val
        if analysis_type in ["visual", "both"]:
            val = scores["visual"]
            # Convert numpy types to Python float
            if isinstance(val, (np.floating, np.integer)):
                val = float(val)
            # Values from model are like 5670, normalize to 0-1 by dividing by 10000
            
            filtered_results[orientation]["visual"] = val
    
    logger.info(f"✅ Analysis complete for project {project_id}")
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "analysis_type": analysis_type,
        "results": filtered_results
    }
