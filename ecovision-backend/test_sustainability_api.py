import requests
import json

url = 'http://127.0.0.1:8000/analysis/sustainability'
payload = {
    "floorplan_id": 1,
    "materials": {
        "wall_base": "MAT001",
        "wall_insulation": None,
        "roof_base": "MAT001",
        "roof_insulation": None,
        "floor_base": "MAT001",
        "floor_insulation": None
    },
    "rooms": [
        {"name": "Test Room", "area_m2": 20}
    ]
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response JSON (first 500 chars):")
        print(json.dumps(data, indent=2)[:500])
    except ValueError:
        print("Response is not JSON")
        print(response.text[:500])
except Exception as e:
    print(f"An error occurred: {e}")
