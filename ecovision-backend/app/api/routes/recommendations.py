"""
Recommendation Engine Routes
Generates sustainability recommendations based on floorplan JSON data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
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


class RoomDirectionUpdate(BaseModel):
    """Request body for saving user-selected room orientation"""
    floorplan_id: int
    room_name: str
    orientation: str


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


@router.post("/rooms/explanations")
async def get_room_explanations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return room-by-room explanations with current orientation data."""
    try:
        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()

        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")

        project = floorplan.project
        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        features = floorplan.json_data or {}
        rooms = features.get("rooms", [])

        room_explanations = []
        for room in rooms:
            room_name = room.get("name", "Unknown Room")
            area = room.get("area_m2", 0)
            window_directions = room.get("window_directions", [])
            orientation = (
                room.get("orientation")
                or room.get("primary_direction")
                or (window_directions[0] if window_directions else "unknown")
            )

            if window_directions:
                exp = (
                    f"{room_name} is around {area} m2. Windows face {', '.join(window_directions)}. "
                    f"Current orientation is {orientation}."
                )
            else:
                exp = (
                    f"{room_name} is around {area} m2 with no mapped windows. "
                    f"Current orientation is {orientation}."
                )

            room_explanations.append({
                "room_name": room_name,
                "area_m2": area,
                "window_directions": window_directions,
                "current_orientation": orientation,
                "explanation": exp,
                "can_edit": True,
            })

        return {
            "status": "success",
            "floorplan_id": request.floorplan_id,
            "rooms": room_explanations,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Room explanation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get room explanations: {str(e)}")


@router.post("/rooms/update-orientation")
async def update_room_orientation(
    request: RoomDirectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update one room orientation in floorplan.json_data and persist it."""
    try:
        orientation = request.orientation.strip().upper()
        valid = {"N", "S", "E", "W", "NE", "NW", "SE", "SW", "UNKNOWN"}
        if orientation not in valid:
            raise HTTPException(status_code=400, detail="Invalid orientation")

        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()

        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")

        project = floorplan.project
        if project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        features = floorplan.json_data or {}
        rooms = features.get("rooms", [])

        target_found = False
        for room in rooms:
            if room.get("name") == request.room_name:
                room["orientation"] = orientation
                # Keep backward compatibility with existing room direction usage.
                room["primary_direction"] = orientation
                room["user_edited_orientation"] = True
                target_found = True
                break

        if not target_found:
            raise HTTPException(status_code=404, detail="Room not found")

        floorplan.json_data = features
        flag_modified(floorplan, "json_data")
        db.add(floorplan)
        db.commit()

        return {
            "status": "success",
            "message": "Room orientation updated",
            "room_name": request.room_name,
            "orientation": orientation,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Update room orientation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update orientation: {str(e)}")
