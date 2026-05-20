from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from app.services.material_mapper import map_user_materials_to_values
from app.services.thermal_comfort_engine import analyze_thermal_comfort
from app.services.thermal_input_converter import convert_test_json_to_engine_features
from app.services.analysis.sustainability_model import (
    optimize_building_from_ids,
    optimize_building_with_user_materials,
    run_building_optimization_test,
    load_materials_from_csv
)
from app.services.auth_service import get_current_user
from app.core.database import get_db
from app.models.floorplan import Floorplan
from sqlalchemy.orm import Session
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# -----------------------------
# Load climate features
# -----------------------------
CLIMATE_FILE = os.path.join(
    os.path.dirname(__file__),
    "../../services/climate_features.json"
)

def load_climate_data() -> Dict:
    try:
        with open(CLIMATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load climate file: {e}")
        return {}

# -----------------------------
# Request Models
# -----------------------------
class MaterialSelection(BaseModel):
    wall_base: str
    wall_insulation: Optional[str] = "None"
    roof_base: str
    roof_insulation: Optional[str] = "None"
    floor_base: str
    floor_insulation: Optional[str] = "None"
    window_type: str


class ThermalAnalysisRequest(BaseModel):
    floorplan_id: int
    materials: MaterialSelection


class ThermalAnalysisResponse(BaseModel):
    comfort_score: float
    comfort_class: str
    pmv: float
    ppd: float
    tdb_est: float
    tr_est: float
    u_wall: float
    u_roof: float
    u_floor: float
    u_window: float
    shgc: float


class SustainabilityAnalysisRequest(BaseModel):
    """Request for sustainability analysis using ML model"""
    floorplan_id: int
    materials: Dict[str, str]  # e.g., {'wall_base': 'MAT001', 'roof_base': 'MAT021', ...}
    rooms: Optional[list] = None  # Optional room data from floorplan

# -----------------------------
# Climate Logic
# -----------------------------
def get_climate_from_floorplan(floorplan: Floorplan) -> Dict:
    climate_data = load_climate_data()

    json_data = floorplan.json_data or {}

    city = (
        json_data.get("city")
        or json_data.get("location")
        or getattr(floorplan, "location", None)
    )

    if city and city in climate_data:
        c = climate_data[city][0]
        return {
            "avg_temp": float(c["avg_temp"]),
            "avg_humidity": float(c["avg_humidity"]),
            "avg_solar": float(c["avg_solar"]),
        }

    # fallback (Cairo)
    return {
        "avg_temp": 22.13,
        "avg_humidity": 54.91,
        "avg_solar": 245.26,
    }

# ─────────────────────────────────────────────
# WINDOW SURFACE KEYS — excluded from optimizer
# The optimizer only handles wall / floor / ceiling
# surfaces. Window-related keys are for the thermal
# model only and must never be forwarded to the
# sustainability optimizer.
# ─────────────────────────────────────────────
WINDOW_KEYS = {"window", "window_type", "window_base"}


# -----------------------------
# MAIN ENDPOINT
# -----------------------------
@router.post("/thermal", response_model=ThermalAnalysisResponse)
async def analyze_thermal(
    request: ThermalAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        print("\n" + "="*50)
        print("🔍 THERMAL ANALYSIS REQUEST RECEIVED")
        print("="*50)
        print(f"📌 Request Type: {type(request)}")
        print(f"📌 Floorplan ID: {request.floorplan_id}")
        print(f"📌 Materials Input: {request.materials.dict()}")
        
        # -----------------------------
        # 1. Fetch floorplan
        # -----------------------------
        print("\n[1] Fetching Floorplan...")
        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()

        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")

        if not floorplan.json_data:
            raise HTTPException(status_code=400, detail="Floorplan has no JSON data")

        print(f"✓ Floorplan Found: ID={floorplan.id}, Type={floorplan.file_type}")
        print(f"  JSON Data Keys: {list(floorplan.json_data.keys()) if isinstance(floorplan.json_data, dict) else 'Not a dict'}")

        # -----------------------------
        # 2. Convert JSON → features
        # -----------------------------
        print("\n[2] Converting JSON to Engine Features...")
        print(f"  Input JSON: {json.dumps(floorplan.json_data, indent=2)[:200]}...")
        
        floorplan_features = convert_test_json_to_engine_features(
            floorplan.json_data
        )
        
        print(f"✓ Floorplan Features Generated:")
        print(f"  {floorplan_features}")

        # -----------------------------
        # 3. Climate from city
        # -----------------------------
        print("\n[3] Getting Climate Data...")
        climate_features = get_climate_from_floorplan(floorplan)
        print(f"✓ Climate Features:")
        print(f"  Avg Temp: {climate_features['avg_temp']}°C")
        print(f"  Avg Humidity: {climate_features['avg_humidity']}%")
        print(f"  Avg Solar: {climate_features['avg_solar']} W/m²")

        # -----------------------------
        # 4. Materials → U-values
        # -----------------------------
        print("\n[4] Mapping Materials to U-Values...")
        print(f"  Input Materials:")
        for key, value in request.materials.dict().items():
            print(f"    - {key}: {value}")
        
        u_values = map_user_materials_to_values(
            request.materials.dict()
        )
        
        print(f"✓ U-Values Generated:")
        print(f"  {u_values}")

        # -----------------------------
        # 5. Thermal Analysis
        # -----------------------------
        print("\n[5] Running Thermal Comfort Analysis...")
        print(f"  Inputs Summary:")
        print(f"    - Floorplan: {type(floorplan_features)}")
        print(f"    - Climate: {type(climate_features)}")
        print(f"    - Materials: {type(u_values)}")
        
        result = analyze_thermal_comfort(
            floorplan_features=floorplan_features,
            climate_features=climate_features,
            material_uvalues=u_values
        )
        
        print(f"\n✓ Analysis Result:")
        print(f"  {result}")

        # -----------------------------
        # 6. Response
        # -----------------------------
        print("\n[6] Preparing Response...")
        response_data = {**result, **u_values}
        print(f"✓ Final Response:")
        print(f"  {response_data}")
        print("="*50 + "\n")
        
        return ThermalAnalysisResponse(
            **response_data
        )

    except ValueError as e:
        print(f"❌ ValueError: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Thermal analysis error: {str(e)}"
        )


# ─────────────────────────────────────────────
# SUSTAINABILITY ANALYSIS ENDPOINT
# ─────────────────────────────────────────────
@router.post("/sustainability")
async def analyze_sustainability(
    request: SustainabilityAnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Analyze sustainability of material selections using trained ML model.

    Takes material IDs and room data, returns sustainability scores and carbon footprint.

    Args:
        floorplan_id: ID of the floorplan being analyzed
        materials: Dictionary mapping building elements to material IDs
                  e.g., {'wall_base': 'MAT001', 'wall_insulation': 'MAT037', ...}
        rooms: Optional list of room data from floorplan

    Returns:
        Sustainability scores, carbon footprint breakdown, and alternative suggestions
    """
    try:
        logger.info(f"🔍 SUSTAINABILITY ANALYSIS REQUEST RECEIVED")
        logger.info(f"📌 Floorplan ID: {request.floorplan_id}")
        logger.info(f"📌 Materials: {request.materials}")

        # Check authentication
        if not current_user:
            logger.warning("❌ Authentication failed: No current user")
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Fetch and validate floorplan
        floorplan = db.query(Floorplan).filter(
            Floorplan.id == request.floorplan_id
        ).first()

        if not floorplan:
            raise HTTPException(status_code=404, detail="Floorplan not found")

        # Verify ownership
        if not floorplan.project or floorplan.project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Get rooms from floorplan if not provided
        rooms = request.rooms
        if not rooms and floorplan.json_data:
            rooms = floorplan.json_data.get('rooms', [])

        if not rooms:
            raise HTTPException(status_code=400, detail="No rooms data available for analysis")

        logger.info(f"📊 Analyzing {len(rooms)} rooms with {len(request.materials)} materials")

        # ── FIX 6: Filter materials for the optimizer ─────────────────
        # Window keys and empty/None values are excluded.
        # The optimizer only handles wall / floor / ceiling surfaces.
        # We filter by KEY NAME (not by MAT number) so any window ID
        # format is correctly excluded regardless of its prefix.
        valid_materials = {}
        for key, value in request.materials.items():
            # Skip window-related keys entirely — the optimizer doesn't use them
            if key.lower() in WINDOW_KEYS:
                logger.info(f"   Skipping window key: {key}={value}")
                continue

            # Skip empty / None values
            if value is None or value == "" or (isinstance(value, str) and value.upper() in ("NONE", "NULL")):
                logger.info(f"   Skipping empty value for key: {key}")
                continue

            valid_materials[key] = value
        # ─────────────────────────────────────────────────────────────

        if not valid_materials:
            raise HTTPException(status_code=400, detail="No valid materials provided")

        logger.info(f"📦 Valid materials for optimizer: {valid_materials}")

        # Run room-by-room optimization with materials dictionary
        # Request only 1 recommendation (single alternative) per room
        result = optimize_building_with_user_materials(valid_materials, rooms, top_n=1)

        if result.get("status") == "error" or "error" in result:
            logger.error(f"❌ Optimization error: {result.get('error')}")
            raise HTTPException(status_code=400, detail=result.get("error", "Optimization failed"))

        logger.info(f"✅ Room-by-room analysis completed for {len(result.get('rooms', []))} rooms")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sustainability analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sustainability analysis error: {str(e)}"
        )


@router.get("/sustainability/test")
async def sustainability_test(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Run the internal model test harness and return its sample output.

    This is provided as a developer helper so the frontend can request
    the exact sample BEFORE/AFTER output the model produces.
    """
    try:
        # Require simple auth check
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        result = run_building_optimization_test(debug=False)

        if not result:
            raise HTTPException(status_code=500, detail="Test run failed")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running sustainability test", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# THERMAL RECOMMENDATIONS ENDPOINT
# ─────────────────────────────────────────────
@router.post("/thermal/recommendations")
async def thermal_recommendations(
    request: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Generate thermal improvement scenarios based on current analysis.
    Shows design modifications that could improve thermal comfort.
    """
    try:
        analysis_result = request.get("analysis_result", {})
        floorplan_json = request.get("floorplan_json", {})
        
        comfort_score = analysis_result.get("comfort_score", 0)
        comfort_class = analysis_result.get("comfort_class", "Neutral")
        
        scenarios = []
        main_issue = ""
        has_recommendations = False
        
        # Generate scenarios based on current comfort class
        if comfort_class == "Warm":
            main_issue = "Space is too warm - indoor temperature exceeds comfort zone"
            has_recommendations = True
            
            scenarios = [
                {
                    "design_action": "Reduce South/West Window Area",
                    "description": "Decrease solar gain by reducing south and west-facing windows",
                    "why_it_helps": "Less direct solar radiation reduces cooling load and interior temperature",
                    "projected_score": min(100, comfort_score + 8),
                    "projected_pmv": analysis_result.get("pmv", 0.5) - 0.3,
                    "projected_ppd": max(0, analysis_result.get("ppd", 10) - 5),
                    "projected_tdb": analysis_result.get("tdb_est", 25) - 1.5,
                    "projected_tr": analysis_result.get("tr_est", 28) - 2.0
                },
                {
                    "design_action": "Add Thermal Insulation",
                    "description": "Increase wall/roof insulation to reduce radiant heat transfer",
                    "why_it_helps": "Better insulation minimizes solar heat penetration through envelope",
                    "projected_score": min(100, comfort_score + 12),
                    "projected_pmv": analysis_result.get("pmv", 0.5) - 0.5,
                    "projected_ppd": max(0, analysis_result.get("ppd", 10) - 8),
                    "projected_tdb": analysis_result.get("tdb_est", 25) - 2.0,
                    "projected_tr": analysis_result.get("tr_est", 28) - 2.5
                },
                {
                    "design_action": "Install Shading Devices",
                    "description": "Add external shading (overhangs, blinds, louvers) on solar-exposed facades",
                    "why_it_helps": "Blocks direct solar radiation before it enters the building",
                    "projected_score": min(100, comfort_score + 15),
                    "projected_pmv": analysis_result.get("pmv", 0.5) - 0.6,
                    "projected_ppd": max(0, analysis_result.get("ppd", 10) - 10),
                    "projected_tdb": analysis_result.get("tdb_est", 25) - 2.5,
                    "projected_tr": analysis_result.get("tr_est", 28) - 3.0
                }
            ]
            
        elif comfort_class == "Cool":
            main_issue = "Space is too cool - indoor temperature is below comfort zone"
            has_recommendations = True
            
            scenarios = [
                {
                    "design_action": "Increase South Window Area",
                    "description": "Expand south-facing windows to maximize beneficial solar gains",
                    "why_it_helps": "More solar access increases passive heating, naturally warming the space",
                    "projected_score": min(100, comfort_score + 10),
                    "projected_pmv": analysis_result.get("pmv", -1.5) + 0.4,
                    "projected_ppd": max(0, analysis_result.get("ppd", 20) - 6),
                    "projected_tdb": analysis_result.get("tdb_est", 18) + 1.5,
                    "projected_tr": analysis_result.get("tr_est", 16) + 2.0
                },
                {
                    "design_action": "Reduce Window Glazing Area",
                    "description": "Minimize total window area to reduce heat loss",
                    "why_it_helps": "Smaller window openings reduce thermal transmission and air leakage",
                    "projected_score": min(100, comfort_score + 8),
                    "projected_pmv": analysis_result.get("pmv", -1.5) + 0.3,
                    "projected_ppd": max(0, analysis_result.get("ppd", 20) - 4),
                    "projected_tdb": analysis_result.get("tdb_est", 18) + 1.0,
                    "projected_tr": analysis_result.get("tr_est", 16) + 1.5
                },
                {
                    "design_action": "Improve Thermal Mass",
                    "description": "Use high thermal mass materials (concrete, masonry) to store heat",
                    "why_it_helps": "Thermal mass absorbs solar heat and stabilizes indoor temperature",
                    "projected_score": min(100, comfort_score + 12),
                    "projected_pmv": analysis_result.get("pmv", -1.5) + 0.5,
                    "projected_ppd": max(0, analysis_result.get("ppd", 20) - 8),
                    "projected_tdb": analysis_result.get("tdb_est", 18) + 2.0,
                    "projected_tr": analysis_result.get("tr_est", 16) + 2.5
                }
            ]
            
        else:  # Neutral
            main_issue = "Excellent! Space is within optimal thermal comfort zone"
            has_recommendations = False
        
        message = ""
        if not has_recommendations:
            message = "Your design is already in the comfort zone. No urgent modifications needed!"
        
        return {
            "has_recommendations": has_recommendations,
            "main_issue": main_issue,
            "message": message,
            "current_score": comfort_score,
            "current_class": comfort_class,
            "scenarios": scenarios
        }
        
    except Exception as e:
        logger.error(f"❌ Thermal recommendations error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Thermal recommendations error: {str(e)}"
        )


# ─────────────────────────────────────────────
# MATERIALS ENDPOINT
# ─────────────────────────────────────────────
@router.get("/materials")
async def get_materials(
    current_user=Depends(get_current_user)
):
    """
    Get all available materials from the database.
    Returns materials with predictions for carbon footprint and thermal properties.
    """
    try:
        materials_df = load_materials_from_csv()
        
        if materials_df is None:
            raise HTTPException(status_code=500, detail="Failed to load materials database")
        
        # Convert to list of dictionaries for JSON serialization
        materials_list = materials_df.to_dict('records')
        
        return {
            "status": "success",
            "total_materials": len(materials_list),
            "materials": materials_list
        }
    
    except Exception as e:
        logger.error(f"❌ Error loading materials: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load materials: {str(e)}"
        )


@router.post("/materials/by-category")
async def get_materials_by_category(
    category: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    """
    Get materials filtered by category (brick, concrete, insulation, stone, etc.)
    """
    try:
        materials_df = load_materials_from_csv()
        
        if materials_df is None:
            raise HTTPException(status_code=500, detail="Failed to load materials database")
        
        if category:
            materials_df = materials_df[materials_df["category"] == category]
        
        materials_list = materials_df.to_dict('records')
        
        return {
            "status": "success",
            "category": category,
            "total_materials": len(materials_list),
            "materials": materials_list
        }
    
    except Exception as e:
        logger.error(f"❌ Error loading materials by category: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load materials: {str(e)}"
        )