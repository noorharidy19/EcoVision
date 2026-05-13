from fastapi import APIRouter, HTTPException, Depends
from app.services.visual_comfort_service import analyze_visual_comfort
from app.api.routes.auth import get_current_user   
import json, os

from app.services.visual_comfort_service import (
    analyze_visual_comfort,
    generate_visual_recommendations
)
router = APIRouter()

@router.post("/analysis/visual")
async def visual_comfort_analysis(
    payload: dict,
    current_user = Depends(get_current_user)
):
    """
    Accepts floorplan JSON and returns visual comfort analysis.
    
    Expected payload:
    {
        "floorplan_id": 123,
        "floorplan_json": { ...the parsed floorplan data... }
    }
    """
    try:
        floorplan_data = payload.get("floorplan_json")

        if not floorplan_data:
            raise HTTPException(
                status_code=400,
                detail="floorplan_json is required"
            )

        result = analyze_visual_comfort(floorplan_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Visual comfort analysis failed: {str(e)}"
        )
        
@router.post("/analysis/visual/recommendations")
async def visual_comfort_recommendations(
    payload: dict,
    current_user = Depends(get_current_user)
):
    """
    Takes the existing analysis result + floorplan JSON
    and returns improvement scenarios with projected scores.
    """
    try:
        analysis_result = payload.get("analysis_result")
        floorplan_data  = payload.get("floorplan_json")

        if not analysis_result or not floorplan_data:
            raise HTTPException(
                status_code=400,
                detail="Both analysis_result and floorplan_json are required"
            )

        result = generate_visual_recommendations(analysis_result, floorplan_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendations failed: {str(e)}"
        )