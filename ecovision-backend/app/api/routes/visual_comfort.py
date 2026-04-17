from fastapi import APIRouter, HTTPException, Depends
from app.services.visual_comfort_service import analyze_visual_comfort
from app.api.routes.auth import get_current_user   
import json, os

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