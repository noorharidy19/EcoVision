import pandas as pd

df = pd.read_csv("raw_materials_training_dataset.csv")

print(df.shape)
df.head()

EXPECTED_COLUMNS = [
    "material_id", "category", "component_type", "climate_zone",
    "avg_summer_temp_c", "solar_radiation_index", "humidity_level",
    "urban_density", "density_kg_m3", "thermal_conductivity_w_mk",
    "carbon_kg_per_m2"
]

assert set(EXPECTED_COLUMNS).issubset(df.columns)

NUMERIC_COLS = [
    "avg_summer_temp_c", "solar_radiation_index", "humidity_level",
    "urban_density", "density_kg_m3", "thermal_conductivity_w_mk",
    "carbon_kg_per_m2"
]

df[NUMERIC_COLS] = df[NUMERIC_COLS].apply(
    lambda x: pd.to_numeric(x, errors="coerce")
)
df = df.dropna(subset=NUMERIC_COLS)

assert df["avg_summer_temp_c"].between(20, 55).all()
assert df["solar_radiation_index"].between(4, 9).all()
assert df["humidity_level"].between(0, 1).all()
assert df["urban_density"].between(0.5, 5).all()

assert (df["density_kg_m3"] > 0).all()
assert (df["thermal_conductivity_w_mk"] > 0).all()
assert (df["carbon_kg_per_m2"] >= 0).all()

df["thermal_mass_index"] = (
    df["density_kg_m3"] / df["density_kg_m3"].max()
)

df["suitability_score"] = (
    0.35 * df["thermal_mass_index"] +
    0.30 * (1 / df["thermal_conductivity_w_mk"]) +
    0.20 * df["solar_radiation_index"] +
    0.15 * (1 - df["humidity_level"])
)

df["suitability_score"] = (
    df["suitability_score"] / df["suitability_score"].max()
)

def classify_material(score):
    if score >= 0.7:
        return "ThermalMass"
    elif score >= 0.45:
        return "Hybrid"
    else:
        return "Lightweight"

df["recommended_class"] = df["suitability_score"].apply(classify_material)
df["energy_saving_pct"] = df["suitability_score"] * 30

df.to_csv("materials_dataset_trainable.csv", index=False)