import pandas as pd
import numpy as np

# Load RAW material data (unchanged)
df = pd.read_csv("materials_dataset_500.csv")

# RAW climate data (real-world values, no normalization)
climates = [
    ("EGY_CAIRO_URBAN", 40, 7.2, 0.30, 2.1),
    ("EGY_CAIRO_DESERT_EDGE", 41, 7.8, 0.18, 2.8),
    ("EGY_UPPER", 43, 8.1, 0.12, 3.2),
    ("EGY_NORTH_COAST", 33, 5.9, 0.65, 4.5)
]

components = ["Wall", "Roof", "Floor", "Window"]

rows = []

for _, mat in df.iterrows():
    for zone, temp, solar_kwh, hum, wind in climates:
        for comp in components:
            rows.append({
                "material_id": mat["material_id"],
                "category": mat["category"],
                "component_type": comp,
                "climate_zone": zone,
                "avg_summer_temp_c": temp,
                "solar_radiation_index": solar_kwh,   # RAW kWh/m²/day
                "humidity_level": hum,                # RAW fraction
                "urban_density": wind,                # RAW wind speed m/s
                "density_kg_m3": mat["density_kg_m3"],
                "thermal_conductivity_w_mk": mat["thermal_conductivity_w_mk"],
                "carbon_kg_per_m2": mat["carbon_kg_per_m2"],

                # Targets / derived values intentionally left empty
                "thermal_mass_index": np.nan,
                "suitability_score": np.nan,
                "recommended_class": None,
                "energy_saving_pct": np.nan
            })

expanded_df = pd.DataFrame(rows)

expanded_df.to_csv("raw_materials_training_dataset.csv", index=False)

print("DONE:", expanded_df.shape)
