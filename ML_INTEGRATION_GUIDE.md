# ML Model Integration Guide

## Overview

The `best_model.joblib` machine learning model has been successfully integrated into the EcoVision project. This model provides AI-powered sustainability predictions for material selections, analyzing carbon footprint and environmental impact.

## Architecture

### Backend Components

#### 1. **Sustainability Model Service** (`app/services/analysis/sustainability_model.py`)
- **Purpose**: Loads and manages the ML model for predictions
- **Key Functions**:
  - `load_model()`: Loads the trained model and scaler from joblib
  - `load_materials()`: Loads the materials database from CSV
  - `predict_sustainability_score()`: Makes sustainability predictions
  - `get_alternative_materials()`: Suggests greener alternatives
  - `prepare_features_for_prediction()`: Prepares data for model input

#### 2. **API Endpoint** (`app/api/routes/analysis.py`)
- **Endpoint**: `POST /analysis/sustainability`
- **Request Body**:
  ```json
  {
    "floorplan_id": 1,
    "materials": {
      "wall_base": "MAT001",
      "wall_insulation": "MAT037",
      "roof_base": "MAT005",
      "roof_insulation": "MAT037",
      "floor_base": "MAT001",
      "floor_insulation": "MAT037",
      "window": "MAT042"
    },
    "rooms": [
      {"name": "Room 1", "area_m2": 20},
      {"name": "Room 2", "area_m2": 25}
    ]
  }
  ```

- **Response**:
  ```json
  {
    "status": "success",
    "floorplan_id": 1,
    "sustainability": {
      "average": 0.85,
      "max": 0.95,
      "min": 0.75,
      "all_scores": [0.85, 0.87, 0.82, ...]
    },
    "carbon_footprint": {
      "total_kgCO2_per_m2": 45.32,
      "breakdown": {
        "wall_base": 41.55,
        "wall_insulation": 2.72,
        ...
      }
    },
    "material_count": 7,
    "alternatives": {
      "wall_base": [
        {"material_id": "MAT002", "name": "...", ...}
      ]
    }
  }
  ```

### Frontend Components

#### **Sustainability Page** (`src/pages/sustainability.tsx`)

**New Features**:
1. **ML Analysis Button**: In the Sustainability tab, click "🔍 Analyze Sustainability with ML Model"
2. **Part 2: AI Sustainability Prediction**: Displays AI-powered analysis results with:
   - Average sustainability score
   - Min/Max scores
   - Total carbon footprint
   - Alternative material suggestions

**States Added**:
- `mlSustainabilityScore`: Stores model prediction results
- `mlAnalysisLoading`: Loading state during prediction

**Functions Added**:
- `analyzeWithMLModel()`: Calls the backend API to run predictions

## Material IDs Reference

The model works with material IDs from the materials database. Common IDs:

### Walls (Base Materials)
- MAT001-MAT010: Fired clay bricks (various densities)
- MAT011-MAT019: Stone (various types)

### Insulation
- MAT037: Cellular polyurethane
- MAT038-MAT040: Expanded Polystyrene (various densities)

### Concrete
- MAT021-MAT032: Concrete blocks and stone aggregate

### Windows
- MAT041: Single Glazing
- MAT042: Double Glazing
- MAT043: Low-E Double Glazing

See `materials_master.csv` for complete list.

## Usage Flow

1. **Select Materials**: Go to "🏗️ Material Selection" mode
   - Choose wall base material
   - Choose wall insulation (optional)
   - Choose roof base and insulation
   - Choose floor base and insulation
   - Choose window type

2. **Analyze with AI**: Click "🔍 Analyze Sustainability with ML Model"
   - The system sends selected materials and room data to backend
   - ML model processes the data
   - Results display with sustainability scores and carbon footprint

3. **View Results**:
   - **Part 1**: Shows current material selections and basic carbon calculation
   - **Part 2**: Shows AI-powered predictions with detailed analysis

4. **Compare Options**: Use the alternative materials suggestions to find greener options

## Testing

Run the integration test:

```bash
cd d:\Gradproj\EcoVision
python test_ml_integration.py
```

This will verify:
- ✓ Model can be loaded
- ✓ Materials database can be accessed
- ✓ Predictions can be made

## API Workflow Diagram

```
Frontend (sustainability.tsx)
    |
    | POST /analysis/sustainability
    | {floorplan_id, materials, rooms}
    |
    v
Backend API (analysis.py)
    |
    | Validates floorplan and permissions
    |
    v
Sustainability Service (sustainability_model.py)
    |
    +-- Load Model & Scaler
    +-- Load Materials Database
    +-- Prepare Features
    +-- Run Prediction
    +-- Calculate Carbon Footprint
    +-- Get Alternative Materials
    |
    v
Response to Frontend
    |
    | {sustainability_scores, carbon_footprint, alternatives}
    |
    v
Display Results (sustainability.tsx)
```

## Error Handling

The integration includes comprehensive error handling:

- **Model not found**: Checks if best_model.joblib exists at startup
- **Invalid material IDs**: Returns error if material not in database
- **Missing features**: Handles incomplete material selections
- **API errors**: Returns detailed error messages to frontend

## Performance Considerations

- **Model Caching**: Loads model once and caches in memory
- **Batch Processing**: Processes multiple materials efficiently
- **Scaler Management**: Uses cached scaler for feature normalization

## Future Enhancements

1. Add historical prediction tracking
2. Store sustainability analysis results in database
3. Export analysis results as PDF reports
4. Compare multiple material options side-by-side
5. Integration with cost estimation

## Troubleshooting

### Model Not Loading
- **Error**: "Model file not found"
- **Solution**: Ensure `best_model.joblib` exists at `ecovision-backend/app/models/`

### Material ID Not Found
- **Error**: "Could not find material"
- **Solution**: Check material ID against `materials_master.csv`

### API Connection Error
- **Error**: "Connection refused at 127.0.0.1:8000"
- **Solution**: Ensure backend is running with `uvicorn app.main:app --reload`

### Frontend Not Displaying Results
- **Solution**: Check browser console for API response and network errors

## Contact & Support

For issues with the ML integration, check:
1. Backend logs for prediction errors
2. Frontend console for API errors
3. test_ml_integration.py for model validation
