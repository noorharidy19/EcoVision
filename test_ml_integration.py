"""
Quick test to verify the ML model can be loaded and used
Run this to test: python test_ml_integration.py
"""

import sys
from pathlib import Path

# Add the backend app to path
backend_path = Path(__file__).parent / "ecovision-backend" / "app"
sys.path.insert(0, str(backend_path.parent))

def test_model_loading():
    """Test that the model can be loaded"""
    print("Testing ML Model Integration...")
    print("-" * 50)
    
    try:
        from app.services.analysis.sustainability_model import load_model
        print("✓ Successfully imported load_model")
        
        model, scaler, feature_columns = load_model()
        print(f"✓ Model loaded successfully")
        print(f"  - Model type: {type(model)}")
        print(f"  - Scaler available: {scaler is not None}")
        print(f"  - Feature columns available: {feature_columns is not None}")
        
        return True
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_materials_loading():
    """Test that materials database can be loaded"""
    print("\nTesting Materials Database...")
    print("-" * 50)
    
    try:
        from app.services.analysis.sustainability_model import load_materials
        print("✓ Successfully imported load_materials")
        
        materials_df = load_materials()
        print(f"✓ Materials loaded successfully")
        print(f"  - Number of materials: {len(materials_df)}")
        print(f"  - Columns: {list(materials_df.columns)}")
        
        # Test getting a material by ID
        sample_material = materials_df.iloc[0]
        print(f"  - Sample material: {sample_material['name']} (ID: {sample_material['material_id']})")
        
        return True
    except Exception as e:
        print(f"✗ Error loading materials: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prediction():
    """Test making a sustainability prediction"""
    print("\nTesting Sustainability Prediction...")
    print("-" * 50)
    
    try:
        from app.services.analysis.sustainability_model import predict_sustainability_score
        print("✓ Successfully imported predict_sustainability_score")
        
        # Create test material selection with valid material IDs
        test_materials = {
            "wall_base": "MAT005",  # Fired clay brick 1920
            "wall_insulation": "MAT037",  # Cellular polyurethane
            "roof_base": "MAT005",  # Same brick
            "roof_insulation": "MAT037",  # Same insulation
            "floor_base": "MAT005",
            "floor_insulation": "MAT037",
            "window": "MAT042"  # Double Glazing
        }
        
        # Test rooms data
        test_rooms = [
            {"name": "Room 1", "area_m2": 20},
            {"name": "Room 2", "area_m2": 25}
        ]
        
        result = predict_sustainability_score(test_materials, test_rooms)
        
        if result.get("status") == "success":
            print(f"✓ Prediction successful")
            print(f"  - Status: {result['status']}")
            print(f"  - Average Sustainability Score: {result['sustainability_scores']['average']:.4f}")
            print(f"  - Total Carbon Footprint: {result['carbon_footprint']['total_kgCO2_per_m2']:.2f} kg CO₂/m²")
            return True
        else:
            print(f"✗ Prediction failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("ML MODEL INTEGRATION TEST")
    print("=" * 50)
    
    results = []
    results.append(("Model Loading", test_model_loading()))
    results.append(("Materials Database", test_materials_loading()))
    results.append(("Sustainability Prediction", test_prediction()))
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✓ All tests passed! ML integration is ready.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
    
    sys.exit(0 if all_passed else 1)
