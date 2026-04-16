import pandas as pd

MATERIALS_CSV = r"D:\\Gradproj\\EcoVision\\materials_master.csv"


def load_materials():
    return pd.read_csv(MATERIALS_CSV)


def get_material_row(df, material_name):
    row = df[df["name"] == material_name]
    if row.empty:
        raise ValueError(f"Material not found: {material_name}")
    return row.iloc[0]


def compute_u_from_layers(layers):
    r_total = sum(layer["r_value_m2K_W"] for layer in layers)
    if r_total <= 0:
        raise ValueError("Invalid total resistance")
    return 1.0 / r_total


def map_user_materials_to_values(user_selection: dict) -> dict:
    df = load_materials()

    wall_layers = [get_material_row(df, user_selection["wall_base"])]
    if user_selection.get("wall_insulation") and user_selection["wall_insulation"] != "None":
        wall_layers.append(get_material_row(df, user_selection["wall_insulation"]))

    roof_layers = [get_material_row(df, user_selection["roof_base"])]
    if user_selection.get("roof_insulation") and user_selection["roof_insulation"] != "None":
        roof_layers.append(get_material_row(df, user_selection["roof_insulation"]))

    floor_layers = [get_material_row(df, user_selection["floor_base"])]
    if user_selection.get("floor_insulation") and user_selection["floor_insulation"] != "None":
        floor_layers.append(get_material_row(df, user_selection["floor_insulation"]))

    u_wall = compute_u_from_layers(wall_layers)
    u_roof = compute_u_from_layers(roof_layers)
    u_floor = compute_u_from_layers(floor_layers)

    # Get window from dataset
    window_row = get_material_row(df, user_selection["window_type"])
    u_window = float(window_row["u_value_W_m2K"])
    shgc = float(window_row["shgc"]) if pd.notna(window_row.get("shgc")) else 0.65

    return {
        "u_wall": round(u_wall, 4),
        "u_roof": round(u_roof, 4),
        "u_floor": round(u_floor, 4),
        "u_window": round(u_window, 4),
        "shgc": round(shgc, 3),
    }