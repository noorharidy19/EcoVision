"""
Sustainability Model Service
Loads and uses the trained best_model.joblib for material sustainability predictions
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from itertools import product
import warnings

# Suppress sklearn version warnings - model works fine across versions
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')
warnings.filterwarnings('ignore', message='.*InconsistentVersionWarning.*')
warnings.filterwarnings('ignore', message='.*feature names.*')

logger = logging.getLogger(__name__)

# Path to the trained model - try multiple locations and formats
MODEL_DIR = Path(__file__).parent.parent.parent / "models"
MODEL_PATH_JOBLIB = MODEL_DIR / "best_model.joblib"
MODEL_PATH_PKL = MODEL_DIR / "best_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
COLUMNS_PATH = MODEL_DIR / "model_columns.pkl"
NEEDS_SCALE_PATH = MODEL_DIR / "model_needs_scale.pkl"

# Materials CSV is in the project root (one level above ecovision-backend)
MATERIALS_CSV_PATH = Path(__file__).parent.parent.parent.parent.parent / "materials_master.csv"

# Cache the model and scaler in memory
_model = None
_scaler = None
_materials_df = None
_feature_columns = None
_needs_scale = None


def load_model():
    """Load the trained model and scaler from joblib/pkl files"""
    global _model, _scaler, _feature_columns, _needs_scale

    if _model is not None:
        return _model, _scaler, _feature_columns

    try:
        # Try loading three separate pkl files first (standard scikit-learn format)
        if COLUMNS_PATH.exists() and MODEL_PATH_PKL.exists():
            logger.info(f"Loading model from separate pkl files...")
            _model = joblib.load(str(MODEL_PATH_PKL))
            _feature_columns = joblib.load(str(COLUMNS_PATH))

            _needs_scale = False
            if NEEDS_SCALE_PATH.exists():
                _needs_scale = joblib.load(str(NEEDS_SCALE_PATH))

            if _needs_scale and SCALER_PATH.exists():
                _scaler = joblib.load(str(SCALER_PATH))
                logger.info(f"✅ Loaded scaler from {SCALER_PATH}")

            logger.info(f"✅ Model loaded: {type(_model)}, Columns: {len(_feature_columns) if _feature_columns else 0}")
            return _model, _scaler, _feature_columns

        # Fall back to single joblib file
        if MODEL_PATH_JOBLIB.exists():
            logger.info(f"Loading model from joblib file...")
            loaded_data = joblib.load(str(MODEL_PATH_JOBLIB))

            if isinstance(loaded_data, dict):
                _model = loaded_data.get('model')
                _scaler = loaded_data.get('scaler')
                _feature_columns = loaded_data.get('feature_columns')
            else:
                _model = loaded_data
                _scaler = None
                _feature_columns = None

            logger.info(f"✅ Model loaded from joblib: {type(_model)}")
            return _model, _scaler, _feature_columns

        # If nothing found, raise error
        raise FileNotFoundError(
            f"Model files not found. Looked for:\n"
            f"  - {MODEL_PATH_PKL}\n"
            f"  - {MODEL_PATH_JOBLIB}\n"
            f"  - {COLUMNS_PATH}"
        )

    except Exception as e:
        logger.error(f"❌ Error loading model: {str(e)}")
        raise


def load_materials():
    """Load materials database from CSV"""
    global _materials_df

    if _materials_df is not None:
        return _materials_df

    try:
        if not MATERIALS_CSV_PATH.exists():
            logger.error(f"Materials CSV not found at {MATERIALS_CSV_PATH}")
            raise FileNotFoundError(f"Materials CSV not found at {MATERIALS_CSV_PATH}")

        _materials_df = pd.read_csv(str(MATERIALS_CSV_PATH))
        logger.info(f"✅ Loaded {len(_materials_df)} materials from CSV")
        return _materials_df

    except Exception as e:
        logger.error(f"❌ Error loading materials: {str(e)}")
        raise


def get_material_by_id(material_id: str) -> dict:
    """Get material properties by ID"""
    materials_df = load_materials()
    material = materials_df[materials_df['material_id'] == material_id]

    if material.empty:
        return None

    return material.iloc[0].to_dict()


def prepare_features_for_prediction(materials: dict, rooms: list = None) -> pd.DataFrame:
    """
    Prepare feature matrix for model prediction

    Args:
        materials: Dict with keys like 'wall_base', 'wall_insulation', etc.
                  Values are material IDs (can be None for optional fields)
        rooms: List of room dicts with area and other properties

    Returns:
        DataFrame with features ready for prediction
    """
    materials_df = load_materials()
    features_list = []

    for material_id in materials.values():
        if material_id is not None:
            material = materials_df[materials_df['material_id'] == material_id]

            if not material.empty:
                mat_row = material.iloc[0]
                mat_features = {}
                for col in material.columns:
                    val = mat_row[col]
                    if col not in ['material_id', 'name', 'category', 'roughness']:
                        try:
                            mat_features[col] = float(val) if pd.notna(val) else 0.0
                        except (ValueError, TypeError):
                            pass
                features_list.append(mat_features)
            else:
                logger.warning(f"Material ID {material_id} not found in database")

    if not features_list:
        return None

    features_df = pd.DataFrame(features_list)
    return features_df


def _normalize_predictions(predictions):
    """
    FIX 1: Only normalize predictions if they are genuinely out of the expected 0-1 range.
    Avoids compressing valid predictions into an artificial range.
    """
    if len(predictions) == 0:
        return predictions

    pred_min = float(np.min(predictions))
    pred_max = float(np.max(predictions))

    # Only normalize if values are actually outside the expected 0-1 range
    if pred_max > 1.0 or pred_min < 0.0:
        if pred_max != pred_min:
            predictions = (predictions - pred_min) / (pred_max - pred_min)
        else:
            logger.warning("All predictions identical — model may not be working correctly")
            predictions = np.full_like(predictions, 0.5)

    # Clamp to valid range
    predictions = np.clip(predictions, 0.0, 1.0)
    return predictions


def predict_sustainability_score(material_features: dict, rooms: list = None) -> dict:
    """
    Predict sustainability score for material selections

    Args:
        material_features: Dict with material IDs for each building element
                          e.g., {'wall_base': 'MAT001', 'roof_base': 'MAT021', ...}
        rooms: List of room dictionaries from floorplan

    Returns:
        Dict with sustainability predictions and scores
    """
    try:
        model, scaler, feature_columns = load_model()

        if model is None:
            return {
                "error": "Model not loaded",
                "status": "error"
            }

        features_df = prepare_features_for_prediction(material_features, rooms)

        if features_df is None or features_df.empty:
            return {
                "error": "Could not prepare features from materials",
                "status": "error"
            }

        numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
        features_numeric = features_df[numeric_cols].copy()

        if feature_columns:
            available_cols = [col for col in feature_columns if col in numeric_cols]
            if len(available_cols) != len(feature_columns):
                logger.warning(f"Feature mismatch: expected {len(feature_columns)} features, got {len(available_cols)}")
            features_numeric = features_df[available_cols].copy()

        if scaler and features_numeric.shape[1] != scaler.n_features_in_:
            logger.warning(f"Feature count mismatch: scaler expects {scaler.n_features_in_} features, got {features_numeric.shape[1]}")
            features_numeric = features_numeric.iloc[:, :scaler.n_features_in_]

        if scaler:
            try:
                features_scaled = scaler.transform(features_numeric.values)
                features_df_scaled = pd.DataFrame(features_scaled, columns=features_numeric.columns)
            except Exception as e:
                logger.error(f"Scaler transform error: {e}")
                features_df_scaled = features_numeric
        else:
            features_df_scaled = features_numeric

        predictions = model.predict(features_df_scaled.values)

        # FIX 1: Use safe normalization — only when truly out of range
        predictions = _normalize_predictions(predictions)

        avg_score = float(np.mean(predictions))
        max_score = float(np.max(predictions))
        min_score = float(np.min(predictions))

        logger.info(f"Prediction scores (0-1 scale): avg={avg_score:.4f}, max={max_score:.4f}, min={min_score:.4f}")

        # FIX 4: Calculate carbon using actual room area when available
        materials_df = load_materials()
        total_area = sum(r.get('area_m2', 0) for r in rooms) if rooms else 1.0
        total_carbon = 0
        carbon_breakdown = {}

        for key, material_id in material_features.items():
            if material_id:
                material = materials_df[materials_df['material_id'] == material_id]
                if not material.empty:
                    # Multiply by actual area for realistic carbon figures
                    carbon = float(material['carbon_kgCO2_per_m2'].iloc[0]) * total_area
                    total_carbon += carbon
                    carbon_breakdown[key] = round(carbon, 2)

        return {
            "status": "success",
            "sustainability_scores": {
                "average": avg_score,
                "max": max_score,
                "min": min_score,
                "all_scores": [float(x) for x in predictions]
            },
            "carbon_footprint": {
                "total_kgCO2": round(total_carbon, 2),
                "total_area_m2": round(total_area, 2),
                "breakdown": carbon_breakdown
            },
            "material_count": len(material_features),
            "prediction_count": len(predictions)
        }

    except Exception as e:
        logger.error(f"❌ Error in sustainability prediction: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }


def get_alternative_materials(material_id: str, category: str = None, limit: int = 5) -> list:
    """
    Get alternative materials with better sustainability scores

    Args:
        material_id: Current material ID
        category: Material category (e.g., 'Insulation', 'brick')
        limit: Number of alternatives to return

    Returns:
        List of alternative materials sorted by sustainability
    """
    try:
        if not material_id:
            logger.warning("get_alternative_materials called with None material_id")
            return []

        materials_df = load_materials()
        current_material = materials_df[materials_df['material_id'] == material_id]

        if current_material.empty:
            logger.warning(f"Material ID {material_id} not found")
            return []

        current_carbon = current_material['carbon_kgCO2_per_kg'].iloc[0]

        if category:
            alternatives = materials_df[materials_df['category'] == category]
        else:
            alternatives = materials_df.copy()

        alternatives = alternatives[alternatives['carbon_kgCO2_per_kg'] < current_carbon]
        alternatives = alternatives.sort_values('carbon_kgCO2_per_kg').head(limit)

        return alternatives.to_dict('records')

    except Exception as e:
        logger.error(f"❌ Error getting alternatives: {str(e)}")
        return []


# =========================================================
# ROOM-BY-ROOM OPTIMIZATION
# =========================================================

SURFACES = {
    "wall": 0.6,
    "floor": 0.25,
    "ceiling": 0.15
}

SURFACE_CATEGORY_RULES = {
    "wall": ["brick", "concrete_block", "stone"],
    "floor": ["concrete", "stone"],
    "ceiling": ["insulation", "concrete"]
}

# FIX 2: Realistic default thickness per surface type (meters)
DEFAULT_THICKNESS = {
    "wall": 0.20,
    "floor": 0.15,
    "ceiling": 0.10
}


def filter_user_materials(df, selected_ids):
    """Filter materials to only user-selected IDs"""
    return df[df["material_id"].isin(selected_ids)].copy()


def validate_selection(df):
    """Check if all required surface categories are covered"""
    categories = set(df["category"])
    missing = []

    for surface, cats in SURFACE_CATEGORY_RULES.items():
        if not any(cat in categories for cat in cats):
            missing.append(surface)

    return missing



# ✅ الحساب الصح
def embodied_carbon(area, mat, surface=None):
    """
    Calculate total embodied carbon for a surface area.
    
    CRITICAL: Use carbon_kgCO2_per_m2 DIRECTLY from CSV.
    This is already calculated and avoids incorrect scaling.
    
    Formula: Total Carbon = area (m²) × carbon_kgCO2_per_m2
    """
    carbon_per_m2 = mat.get('carbon_kgCO2_per_m2')
    
    # ✅ Use pre-calculated carbon_per_m2 (most accurate)
    if carbon_per_m2 is not None and carbon_per_m2 > 0:
        return area * carbon_per_m2
    
    # Fallback: Calculate from components if per_m2 not available
    thickness = mat.get('thickness_m', DEFAULT_THICKNESS.get(surface, 0.15))
    if thickness <= 0 or thickness > 2.0:
        thickness = DEFAULT_THICKNESS.get(surface, 0.15)
    
    density = mat.get('density_kg_m3', 1000)
    carbon_per_kg = mat.get('carbon_kgCO2_per_kg', 0)
    
    logger.warning(f"⚠️  Using fallback for {mat.get('name')}: density×thickness×carbon_per_kg")
    return area * density * thickness * carbon_per_kg


def compute_user_combo(room, df, selected_ids):
    """
    Calculate current material selection baseline using ACTUAL embodied carbon.
    
    CRITICAL: Use same selection criteria as get_surface_candidates() to ensure
    consistent carbon calculations throughout the optimization pipeline.
    """
    combo = {}
    total_carbon = 0

    user_df = df[df["material_id"].isin(selected_ids)]

    logger.info(f"\n{'='*80}")
    logger.info(f"📊 BASELINE CALCULATION FOR ROOM: {room.get('name', 'Unknown')} (Area: {room.get('area_m2', 0)} m²)")
    logger.info(f"{'='*80}")

    for surface, ratio in SURFACES.items():
        cats = SURFACE_CATEGORY_RULES[surface]
        subset = user_df[user_df["category"].isin(cats)].copy()

        if subset.empty:
            return None, None

        # FIX: Calculate ACTUAL embodied carbon per material for fair comparison
        subset["actual_embodied_carbon"] = subset.apply(
            lambda row: calculate_embodied_carbon_per_m2(row, surface),
            axis=1
        )
        
        # Sort by actual embodied carbon (not just per_kg)
        mat = subset.sort_values('actual_embodied_carbon').iloc[0]
        surface_area = room.get("area_m2", 1) * ratio
        carbon = embodied_carbon(surface_area, mat, surface=surface)

        # DETAILED LOGGING
        logger.info(f"\n  📍 SURFACE: {surface.upper()}")
        logger.info(f"     Area ratio: {ratio} | Calculated area: {surface_area:.2f} m²")
        logger.info(f"     Material: {mat['name']}")
        logger.info(f"     ID: {mat.get('material_id', 'N/A')}")
        logger.info(f"     Density: {mat.get('density_kg_m3', 'N/A')} kg/m³")
        logger.info(f"     Thickness: {mat.get('thickness_m', 'N/A')} m")
        logger.info(f"     Carbon/kg: {mat.get('carbon_kgCO2_per_kg', 'N/A')} kg CO₂/kg")
        logger.info(f"     Carbon/m²: {mat.get('carbon_kgCO2_per_m2', 'N/A')} kg CO₂/m²")
        logger.info(f"     Embodied Carbon (per m²): {mat['actual_embodied_carbon']:.4f} kg CO₂/m²")
        logger.info(f"     ✅ TOTAL for this surface: {carbon:.2f} kg CO₂")

        combo[surface] = {
            "name": mat["name"],
            "carbon_kg": round(carbon, 2)
        }

        total_carbon += carbon

    logger.info(f"\n  {'─'*80}")
    logger.info(f"  🔢 BASELINE TOTAL: {total_carbon:.2f} kg CO₂")
    logger.info(f"  {'='*80}\n")

    return combo, total_carbon


def calculate_embodied_carbon_per_m2(material_row, surface):
    """
    Get embodied carbon per m² for a material.
    
    CRITICAL FIX: Use carbon_kgCO2_per_m2 from CSV DIRECTLY.
    This avoids incorrect scaling and gives accurate comparisons.
    """
    try:
        # ✅ ALWAYS use pre-calculated carbon_kgCO2_per_m2 from CSV
        carbon_per_m2 = material_row.get('carbon_kgCO2_per_m2')
        if carbon_per_m2 is not None and carbon_per_m2 > 0:
            return float(carbon_per_m2)
        
        # Fallback (should rarely happen): calculate from components
        thickness = material_row.get('thickness_m', 0)
        if not thickness or thickness <= 0 or thickness > 2.0:
            thickness = DEFAULT_THICKNESS.get(surface, 0.15)
        
        density = material_row.get('density_kg_m3', 1000)
        carbon_per_kg = material_row.get('carbon_kgCO2_per_kg', 0)
        
        calculated = float(density) * float(thickness) * float(carbon_per_kg)
        logger.warning(f"⚠️  Using fallback calculation: {calculated:.4f} kg CO₂/m²")
        return calculated
    
    except Exception as e:
        logger.warning(f"Error calculating embodied carbon: {str(e)}")
        return 1000  # High default to de-prioritize


def get_surface_candidates(df, top_k=3, weight_carbon=0.6, weight_thermal=0.4):
    """Get top eco-friendly materials per surface by multi-objective score (carbon + thermal)
    
    CRITICAL LOGIC:
    For EACH surface (wall, floor, ceiling):
    - Get all categories for that surface (e.g., wall has brick, concrete_block, stone)
    - For EACH category: Calculate actual embodied carbon for all materials
    - Select top-k materials from EACH category (not just top-k overall)
    - This ensures we have low-carbon options from ALL material types per surface
    """
    try:
        surface_candidates = {}

        model, scaler, feature_columns = load_model()

        if model is None:
            logger.error("Model failed to load")
            return surface_candidates

        numeric_cols = df.select_dtypes(include=['float64', 'float32', 'int64', 'int32']).columns.tolist()

        exclude_cols = {'material_id', 'name', 'category', 'roughness', 'predicted_score', 
                        'building_element', 'total_floor_area_m2'}
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

        X = df[numeric_cols].fillna(0)

        if feature_columns and len(X.columns) > 0:
            for col in feature_columns:
                if col not in X.columns:
                    X[col] = 0
            X = X[feature_columns]

        logger.info(f"Feature matrix shape: {X.shape}, Columns: {X.columns.tolist()}")

        if scaler:
            X = scaler.transform(X.values)

        scores = model.predict(X)
        scores = _normalize_predictions(scores)

        df_copy = df.copy()
        df_copy["predicted_score"] = scores

        for surface, categories in SURFACE_CATEGORY_RULES.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"SURFACE: {surface.upper()}")
            logger.info(f"Categories for this surface: {categories}")
            logger.info(f"{'='*60}")
            
            surface_all_candidates = []

            # Process EACH category separately
            for category in categories:
                subset = df_copy[df_copy["category"] == category].copy()

                if subset.empty:
                    logger.warning(f"  ⚠️  {category}: No materials found")
                    continue

                # Calculate actual embodied carbon for this category
                subset["actual_embodied_carbon"] = subset.apply(
                    lambda row: calculate_embodied_carbon_per_m2(row, surface),
                    axis=1
                )
                
                # Sort by embodied carbon within this category
                subset_sorted = subset.sort_values("actual_embodied_carbon", ascending=True)
                
                # Get top_k from THIS category
                subset_top = subset_sorted.head(top_k)
                
                logger.info(f"\n  📦 {category}:")
                logger.info(f"     Total materials: {len(subset)}")
                logger.info(f"     Carbon range: {subset['actual_embodied_carbon'].min():.2f} to {subset['actual_embodied_carbon'].max():.2f} kg CO₂/m²")
                
                for idx, (_, row) in enumerate(subset_top.iterrows(), 1):
                    logger.info(f"     #{idx}: {row['name']} → {row['actual_embodied_carbon']:.2f} kg CO₂/m²")
                
                # Add to candidates for this surface
                surface_all_candidates.extend(subset_top.to_dict("records"))

            if not surface_all_candidates:
                logger.warning(f"❌ {surface}: No candidates found")
                continue

            # Now apply multi-objective scoring on ALL candidates for this surface
            candidates_df = pd.DataFrame(surface_all_candidates)
            
            # Normalize carbon
            carbon_min = candidates_df["actual_embodied_carbon"].min()
            carbon_max = candidates_df["actual_embodied_carbon"].max()
            if carbon_max != carbon_min:
                candidates_df["carbon_norm"] = (candidates_df["actual_embodied_carbon"] - carbon_min) / (carbon_max - carbon_min)
            else:
                candidates_df["carbon_norm"] = 0.5

            # Normalize U-value
            if "u_value" in candidates_df.columns:
                uvalue_min = candidates_df["u_value"].min()
                uvalue_max = candidates_df["u_value"].max()
                if uvalue_max != uvalue_min:
                    candidates_df["uvalue_norm"] = (candidates_df["u_value"] - uvalue_min) / (uvalue_max - uvalue_min)
                else:
                    candidates_df["uvalue_norm"] = 0.5

                candidates_df["combined_score"] = (weight_carbon * candidates_df["carbon_norm"]) + (weight_thermal * candidates_df["uvalue_norm"])
                sort_column = "combined_score"
                logger.info(f"\n  🎯 {surface}: Using multi-objective (60% carbon + 40% thermal)")
            else:
                candidates_df["combined_score"] = candidates_df["carbon_norm"]
                sort_column = "combined_score"
                logger.info(f"\n  🎯 {surface}: Using carbon only")

            # Get top overall candidates after multi-objective ranking
            final_top = candidates_df.sort_values(sort_column, ascending=True).head(top_k)
            surface_candidates[surface] = final_top.to_dict("records")
            
            logger.info(f"\n  ✅ FINAL TOP {top_k} for {surface}:")
            for idx, row in final_top.iterrows():
                logger.info(f"     - {row['name']} ({row['category']}): {row['actual_embodied_carbon']:.2f} kg CO₂/m²")

        return surface_candidates

    except Exception as e:
        logger.error(f"❌ Error in get_surface_candidates: {str(e)}", exc_info=True)
        return {}


def optimize_room(room, surface_candidates):
    """Find optimal material combination for a room with detailed logging"""
    if len(surface_candidates) < len(SURFACES):
        return None, None

    best_combo = None
    best_score = float("inf")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔧 OPTIMIZATION FOR ROOM: {room.get('name', 'Unknown')} (Area: {room.get('area_m2', 0)} m²)")
    logger.info(f"{'='*80}")

    combo_count = 0
    for combo in product(*surface_candidates.values()):
        combo_count += 1
        total_carbon = 0
        combo_details = {}

        logger.info(f"\n  Testing combination #{combo_count}:")

        for (surface, ratio), mat in zip(SURFACES.items(), combo):
            surface_area = room.get("area_m2", 1) * ratio
            carbon = embodied_carbon(surface_area, mat, surface=surface)

            logger.info(f"    {surface.upper()}: {mat['name']}")
            logger.info(f"      Density: {mat.get('density_kg_m3', 'N/A')} | Thickness: {mat.get('thickness_m', 'N/A')} | Carbon/kg: {mat.get('carbon_kgCO2_per_kg', 'N/A')}")
            logger.info(f"      Area: {surface_area:.2f} m² → Carbon: {carbon:.2f} kg CO₂")

            total_carbon += carbon

            combo_details[surface] = {
                "name": mat["name"],
                "carbon_kg": round(carbon, 2)
            }

        logger.info(f"    ➜ Combo total: {total_carbon:.2f} kg CO₂")

        if total_carbon < best_score:
            best_score = total_carbon
            best_combo = combo_details
            logger.info(f"    ✅ NEW BEST!")

    logger.info(f"\n  {'─'*80}")
    logger.info(f"  🏆 BEST COMBINATION FOUND:")
    if best_combo:
        for surface, details in best_combo.items():
            logger.info(f"     {surface}: {details['name']} → {details['carbon_kg']} kg CO₂")
    logger.info(f"  🔢 OPTIMIZED TOTAL: {best_score:.2f} kg CO₂")
    logger.info(f"  {'='*80}\n")

    return best_combo, best_score


def optimize_building(df, rooms, selected_ids):
    """Optimize building materials across all rooms"""
    try:
        user_df = filter_user_materials(df, selected_ids)

        if user_df.empty:
            return {"error": "No valid materials selected"}

        missing = validate_selection(user_df)
        if missing:
            return {"error": f"Missing materials for surfaces: {missing}"}

        results = []
        total_user = 0
        total_opt = 0

        surface_candidates = get_surface_candidates(df)

        if not surface_candidates:
            return {"error": "Could not generate material candidates"}

        for room in rooms:
            user_combo, user_carbon = compute_user_combo(room, df, selected_ids)
            opt_combo, opt_carbon = optimize_room(room, surface_candidates)

            if user_combo is None or opt_combo is None:
                results.append({
                    "room": room.get("name", "Unknown"),
                    "error": "Invalid material selection"
                })
                continue

            saving = user_carbon - opt_carbon
            saving_pct = (saving / user_carbon * 100) if user_carbon > 0 else 0

            total_user += user_carbon
            total_opt += opt_carbon

            results.append({
                "room": room.get("name", "Unknown"),
                "area_m2": room.get("area_m2", 0),
                "your_selection": {
                    "materials": user_combo,
                    "total_carbon_kg": round(user_carbon, 2)
                },
                "recommended_solution": {
                    "materials": opt_combo,
                    "total_carbon_kg": round(opt_carbon, 2)
                },
                "carbon_savings": {
                    "saved_kg": round(saving, 2),
                    "reduction_percent": round(saving_pct, 1)
                }
            })

        # FINAL SUMMARY
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 OPTIMIZATION SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Your Total Carbon:        {total_user:.2f} kg CO₂")
        logger.info(f"Optimized Total Carbon:   {total_opt:.2f} kg CO₂")
        logger.info(f"Total Savings:            {total_user - total_opt:.2f} kg CO₂")
        if total_user > 0:
            logger.info(f"Reduction %:              {((total_user - total_opt) / total_user * 100):.1f}%")
        logger.info(f"{'='*80}\n")

        return {
            "summary": {
                "your_total_carbon": round(total_user, 2),
                "optimized_total_carbon": round(total_opt, 2),
                "total_savings": round(total_user - total_opt, 2),
                "reduction_percent": round(
                    (total_user - total_opt) / total_user * 100, 1
                ) if total_user > 0 else 0
            },
            "rooms": results
        }

    except Exception as e:
        logger.error(f"❌ Error in optimize_building: {str(e)}")
        return {"error": str(e), "status": "error"}


def optimize_building_from_ids(selected_material_ids: list, rooms: list):
    """
    Main entry point for room-by-room optimization analysis
    Loads materials database and returns optimized recommendations
    """
    try:
        materials_df = load_materials()
        result = optimize_building(materials_df, rooms, selected_material_ids)
        return result
    except Exception as e:
        logger.error(f"❌ Error in optimize_building_from_ids: {str(e)}")
        return {"error": str(e), "status": "error"}