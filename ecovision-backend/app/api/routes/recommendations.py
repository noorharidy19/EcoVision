"""
Recommendation Engine Routes
Generates sustainability recommendations based on floorplan JSON data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.floorplan import Floorplan
from app.services.analysis.recommender import run_pipeline
from app.services.analysis.explanation import generate_floor_plan_summary
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationRequest(BaseModel):
    """Request body for generating recommendations"""
    floorplan_id: int


@router.post("/generate")
async def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate sustainability recommendations for a floorplan.
    
    Takes floorplan JSON data and runs the recommendation pipeline.
    Does NOT save recommendations to database.
    
    Args:
        floorplan_id: ID of the floorplan to analyze
        
    Returns:
        Recommendations with formatting
    """
    try:
        # Fetch floorplan
        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()
        
        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")
        
        # Verify user owns the project
        project = floorplan.project
        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        logger.info(f"🎯 Generating recommendations for floorplan {request.floorplan_id}")
        
        # Get floorplan JSON data
        features = floorplan.json_data
        
        if not features:
            raise HTTPException(
                status_code=400,
                detail="Floorplan has no extracted features yet"
            )
        
        # Add metadata to features
        if "city" not in features:
            features["city"] = project.location
        if "north_arrow_direction" not in features:
            features["north_arrow_direction"] = "N"
        
        logger.info(f"📊 Features loaded: {list(features.keys())}")
        
        # Run recommendation pipeline
        result = run_pipeline(features)
        
        logger.info(f"✅ Generated {result['total']} recommendations")
        
        return {
            "status": "success",
            "floorplan_id": request.floorplan_id,
            "recommendations": result["recommendations"],
            "formatted": result["formatted"],
            "total": result["total"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recommendation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.post("/project/{project_id}/recommendations")
async def get_project_recommendations(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate recommendations for the latest floorplan of a project.
    """
    try:
        # Fetch project
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get latest floorplan
        floorplan = db.query(Floorplan).filter(
            Floorplan.project_id == project_id
        ).order_by(Floorplan.id.desc()).first()
        
        if not floorplan:
            raise HTTPException(status_code=404, detail="No floorplan found for project")
        
        if not floorplan.json_data:
            raise HTTPException(
                status_code=400,
                detail="Floorplan has no extracted features"
            )
        
        # Prepare features
        features = floorplan.json_data.copy()
        features["city"] = project.location
        features["north_arrow_direction"] = "N"
        
        # Run pipeline
        result = run_pipeline(features)
        
        return {
            "status": "success",
            "project_id": project_id,
            "floorplan_id": floorplan.id,
            "recommendations": result["recommendations"],
            "formatted": result["formatted"],
            "total": result["total"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def generate_explanation(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a client-facing floor plan explanation/summary.
    
    Takes floorplan JSON data and generates a professional summary using LLM.
    
    Args:
        floorplan_id: ID of the floorplan to explain
        
    Returns:
        Professional floor plan summary
    """
    try:
        # Fetch floorplan
        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()
        
        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")
        
        # Verify user owns the project
        project = floorplan.project
        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        logger.info(f"📝 Generating explanation for floorplan {request.floorplan_id}")
        
        # Get floorplan JSON data
        features = floorplan.json_data
        
        if not features:
            raise HTTPException(
                status_code=400,
                detail="Floorplan has no extracted features yet"
            )
        
        # Add metadata to features
        if "city" not in features:
            features["city"] = project.location
        if "north_arrow_direction" not in features:
            features["north_arrow_direction"] = "N"
        
        logger.info(f"📊 Generating summary for {features.get('num_rooms', 0)} rooms")
        
        # Generate explanation
        explanation = generate_floor_plan_summary(features)
        
        logger.info(f"✅ Explanation generated")
        
        return {
            "status": "success",
            "floorplan_id": request.floorplan_id,
            "explanation": explanation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Explanation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Explanation generation failed: {str(e)}"
        )
