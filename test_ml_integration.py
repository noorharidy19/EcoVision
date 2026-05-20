"""
Quick test to verify the sustainability backend can be loaded and used.
Run this to test: python test_ml_integration.py
"""

import json
import sys
from pathlib import Path

# Add the backend app to path
backend_path = Path(__file__).parent / "ecovision-backend" / "app"
sys.path.insert(0, str(backend_path.parent))


def test_backend_imports():
    """Test that the optimization backend can be imported."""
    print("Testing Sustainability Backend Integration...")
    print("-" * 50)

    try:
        from app.services.analysis.sustainability_model import (
            load_materials_from_csv,
            optimize_room_with_user_selection,
        )
        print("✓ Successfully imported load_materials_from_csv")
        print("✓ Successfully imported optimize_room_with_user_selection")
        return True
    except Exception as e:
        print(f"✗ Error importing backend functions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_materials_loading():
    """Test that materials database can be loaded from CSV."""
    print("\nTesting Materials Database...")
    print("-" * 50)

    try:
        from app.services.analysis.sustainability_model import load_materials_from_csv

        materials_path = Path(__file__).parent / "materials_with_predictions.csv"
        materials_df = load_materials_from_csv(str(materials_path))

        if materials_df is None or materials_df.empty:
            raise ValueError("Materials CSV loaded empty data")

        print("✓ Materials loaded successfully")
        print(f"  - Number of materials: {len(materials_df)}")
        print(f"  - Columns: {list(materials_df.columns)}")

        sample_material = materials_df.iloc[0]
        print(
            f"  - Sample material: {sample_material['name']} "
            f"(ID: {sample_material['material_id']})"
        )

        return True, materials_df
    except Exception as e:
        print(f"✗ Error loading materials: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def load_frontend_material_mapping():
    """Load the same material labels used by the frontend."""
    mapping_path = Path(__file__).parent / "ecovision-frontend" / "public" / "materials-mapping.json"

    try:
        with mapping_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def material_name_from_mapping(mapping, material_id, materials_df=None):
    """Resolve a frontend display name for a material ID."""
    if not mapping or not material_id:
        return material_id or "N/A"

    for section in ("wallBaseMaterials", "roofBaseMaterials", "floorBaseMaterials", "insulationMaterials", "windowTypes"):
        for material in mapping.get(section, []):
            if material.get("id") == material_id:
                return material.get("name", material_id)

    if materials_df is not None:
        match = materials_df[materials_df["material_id"] == material_id]
        if not match.empty:
            return match.iloc[0]["name"]

    return material_id


def test_sustainability_report(materials_df):
    """Print a BEFORE vs AFTER sustainability report."""
    print("\nTesting Sustainability Optimization...")
    print("-" * 50)

    try:
        from app.services.analysis.sustainability_model import optimize_room_with_user_selection

        frontend_mapping = load_frontend_material_mapping()

        room = {"name": "Master Bedroom", "area_m2": 17.9}
        user_selection = {
            "wall": {"base_material_id": "MAT001", "insulation_material_id": None},
            "floor": {"base_material_id": "MAT015", "insulation_material_id": None},
            "ceiling": {"base_material_id": "MAT024", "insulation_material_id": None},
        }

        print("\nFrontend Material Selection")
        print("-" * 50)
        print(f"Wall Base   : {material_name_from_mapping(frontend_mapping, user_selection['wall']['base_material_id'], materials_df)} ({user_selection['wall']['base_material_id']})")
        print(f"Floor Base  : {material_name_from_mapping(frontend_mapping, user_selection['floor']['base_material_id'], materials_df)} ({user_selection['floor']['base_material_id']})")
        print(f"Ceiling Base: {material_name_from_mapping(frontend_mapping, user_selection['ceiling']['base_material_id'], materials_df)} ({user_selection['ceiling']['base_material_id']})")

        result = optimize_room_with_user_selection(
            room=room,
            materials_df=materials_df,
            user_selection=user_selection,
            top_n=3,
            debug=False,
        )

        print("\n" + "=" * 70)
        print("BEFORE VS AFTER OPTIMIZATION RESULTS")
        print("=" * 70)
        print()
        print("=" * 70)
        print(f"ROOM: {result['room']}")
        print("=" * 70)
        print(f"Area: {result['area_m2']} m²")

        before = result["your_selection"]
        summary = result.get("summary", {})
        print("\nSUMMARY")
        print(f"Your Total Carbon : {summary.get('your_total_carbon', before['total_carbon_kg'])} kg CO2")
        print(f"Optimized Carbon  : {summary.get('optimized_total_carbon', result['recommended_solution']['total_carbon_kg'])} kg CO2")
        print(f"Total Savings     : {summary.get('total_savings', result['carbon_savings']['saved_kg'])} kg CO2")
        print(f"Reduction %       : {summary.get('reduction_percent', result['carbon_savings']['reduction_percent'])}%")

        print("\nBEFORE — User Selection")
        print(f"Carbon : {before['total_carbon_kg']} kg CO2")
        print(f"Comfort: {before.get('avg_comfort', 'N/A')} / 1")

        print("\nAFTER — AI Recommendations")
        recommendations = result.get("recommendations", [])

        if not recommendations:
            print("No recommendations were generated.")
            return False

        for index, rec in enumerate(recommendations, start=1):
            after = rec["after"]
            comparison = rec["comparison"]

            print()
            print(f"Recommendation #{index}")
            print("-" * 45)
            print(f"Wall : {after['materials']['wall']['name']}")
            print(f"Floor : {after['materials']['floor']['name']}")
            print(f"Ceiling : {after['materials']['ceiling']['name']}")
            print(f"Carbon : {after['total_carbon']} kg CO2")
            print(f"Comfort : {after['avg_comfort']} / 1")
            print(f"Score : {after['final_score']}")
            print()
            print("Comparison")
            print(f"Carbon Saved : {comparison['carbon_saved_kg']} kg CO2")
            print(f"Carbon Reduction : {comparison['carbon_reduction_pct']}%")
            print(f"Comfort Change : {comparison['comfort_change']}")
            print(f"Comfort Status : {comparison['comfort_status']}")

        return True
    except Exception as e:
        print(f"✗ Error running sustainability optimization: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("ML MODEL INTEGRATION TEST")
    print("=" * 50)

    results = []

    results.append(("Backend Imports", test_backend_imports()))

    materials_ok, materials_df = test_materials_loading()
    results.append(("Materials Database", materials_ok))

    report_ok = False
    if materials_ok and materials_df is not None:
        report_ok = test_sustainability_report(materials_df)
    results.append(("Sustainability Optimization", report_ok))

    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n✓ All tests passed! Sustainability integration is ready.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

    sys.exit(0 if all_passed else 1)
