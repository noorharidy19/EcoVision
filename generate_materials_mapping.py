import pandas as pd
import json

# Read the CSV
df = pd.read_csv('materials_master.csv')

# Create the materials mapping by categories
materials_mapping = {
    "wallBaseMaterials": [],
    "roofBaseMaterials": [],
    "floorBaseMaterials": [],
    "insulationMaterials": [],
    "windowTypes": []
}

# Wall base materials: brick, concrete, concrete blocks
wall_categories = ['brick', 'concrete', 'concrete_block']
for _, row in df.iterrows():
    if row.get('category') in wall_categories:
        materials_mapping["wallBaseMaterials"].append({
            "id": row['material_id'],
            "name": row['name'],
            "category": row['category'],
            "r_value_m2K_W": float(row['r_value_m2K_W']),
            "carbon_kgCO2_per_m2": float(row['carbon_kgCO2_per_m2']),
            "u_value_W_m2K": float(row['u_value_W_m2K']) if pd.notna(row.get('u_value_W_m2K')) else round(1.0/float(row['r_value_m2K_W']), 4) if float(row['r_value_m2K_W']) > 0 else None
        })

# Roof base materials: concrete slabs
for _, row in df.iterrows():
    if row.get('category') == 'concrete' and '102mm' in row['name']:
        materials_mapping["roofBaseMaterials"].append({
            "id": row['material_id'],
            "name": row['name'],
            "category": row['category'],
            "r_value_m2K_W": float(row['r_value_m2K_W']),
            "carbon_kgCO2_per_m2": float(row['carbon_kgCO2_per_m2']),
            "u_value_W_m2K": float(row['u_value_W_m2K']) if pd.notna(row.get('u_value_W_m2K')) else round(1.0/float(row['r_value_m2K_W']), 4) if float(row['r_value_m2K_W']) > 0 else None
        })

# Floor base materials: concrete + blocks
for _, row in df.iterrows():
    if row.get('category') in ['concrete', 'concrete_block']:
        if any(x in row['name'] for x in ['102mm', '200mm', '300mm']):
            if not any(m['id'] == row['material_id'] for m in materials_mapping["roofBaseMaterials"]):
                materials_mapping["floorBaseMaterials"].append({
                    "id": row['material_id'],
                    "name": row['name'],
                    "category": row['category'],
                    "r_value_m2K_W": float(row['r_value_m2K_W']),
                    "carbon_kgCO2_per_m2": float(row['carbon_kgCO2_per_m2']),
                    "u_value_W_m2K": float(row['u_value_W_m2K']) if pd.notna(row.get('u_value_W_m2K')) else round(1.0/float(row['r_value_m2K_W']), 4) if float(row['r_value_m2K_W']) > 0 else None
                })

# Insulation materials
insulation_list = []
for _, row in df.iterrows():
    if row.get('category') == 'Insulation':
        insulation_list.append({
            "id": row['material_id'],
            "name": row['name'],
            "category": row['category'],
            "r_value_m2K_W": float(row['r_value_m2K_W']),
            "carbon_kgCO2_per_m2": float(row['carbon_kgCO2_per_m2']),
            "u_value_W_m2K": float(row['u_value_W_m2K']) if pd.notna(row.get('u_value_W_m2K')) else round(1.0/float(row['r_value_m2K_W']), 4) if float(row['r_value_m2K_W']) > 0 else None
        })

# Add "None" option first
materials_mapping["insulationMaterials"] = [
    {
        "id": "NONE",
        "name": "None",
        "category": "none",
        "r_value_m2K_W": 0,
        "carbon_kgCO2_per_m2": 0,
        "u_value_W_m2K": 0
    }
] + insulation_list

# Window types
for _, row in df.iterrows():
    if row.get('category') == 'window':
        materials_mapping["windowTypes"].append({
            "id": row['material_id'],
            "name": row['name'],
            "category": row['category'],
            "r_value_m2K_W": float(row['r_value_m2K_W']),
            "carbon_kgCO2_per_m2": float(row['carbon_kgCO2_per_m2']),
            "u_value_W_m2K": float(row['u_value_W_m2K']),
            "shgc": float(row['shgc']) if pd.notna(row.get('shgc')) else 0.65
        })

# Save to JSON
with open('ecovision-frontend/public/materials-mapping.json', 'w') as f:
    json.dump(materials_mapping, f, indent=2)

print("✓ materials-mapping.json created successfully!")
print(f"  - Wall Base Materials: {len(materials_mapping['wallBaseMaterials'])}")
print(f"  - Roof Base Materials: {len(materials_mapping['roofBaseMaterials'])}")
print(f"  - Floor Base Materials: {len(materials_mapping['floorBaseMaterials'])}")
print(f"  - Insulation Materials: {len(materials_mapping['insulationMaterials'])}")
print(f"  - Window Types: {len(materials_mapping['windowTypes'])}")
