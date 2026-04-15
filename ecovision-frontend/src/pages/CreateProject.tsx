import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/createProject.css";

type Room = {
  name: string;
  area: number;
};

const CITIES = [
  "Cairo",
  "Aswan",
  "Alexandria",
  "Port Said",
  "Dahab",
  "Hurghada"
];

const CreateProject = () => {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [northArrow, setNorthArrow] = useState("N");
  const [file, setFile] = useState<File | null>(null);

  const [rooms, setRooms] = useState<Room[]>([
    { name: "", area: 0 }
  ]);

  // ➕ Add room
  const addRoom = () => {
    setRooms([...rooms, { name: "", area: 0 }]);
  };

  // ✏️ Update room
  const updateRoom = (
    index: number,
    field: keyof Room,
    value: string
  ) => {
    const updated = [...rooms];

    if (field === "area") {
      const num = parseFloat(value);
      updated[index].area = isNaN(num) ? 0 : num;
    } else {
      updated[index].name = value;
    }

    setRooms(updated);
  };

  const submit = async (e: any) => {
    e.preventDefault();

    const form = new FormData();
    form.append("name", name);
    form.append("location", location);
    form.append("north_arrow_direction", northArrow);
    form.append("rooms_json", JSON.stringify(rooms));

    if (file) form.append("file", file);

    const token = localStorage.getItem("token");

    const res = await fetch("http://127.0.0.1:8000/projects/", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: form,
    });

    const data = await res.json();

    if (res.ok) {
      alert("Project Created Successfully");
      navigate("/myprojects");
    } else {
      alert(data.detail || "Error");
    }
  };

  return (
    <div className="create-layout">

      {/* LEFT */}
      <div className="design-space">
        <h1>Create Your Project</h1>
        <p>
          Upload your floorplan, define rooms with area, and let EcoVision analyze your building intelligently.
        </p>

        <div className="design-placeholder">
          EcoVision AI Preview
        </div>
      </div>

      {/* RIGHT */}
      <form className="project-panel" onSubmit={submit}>
        <h2>New Project</h2>

        {/* Name */}
        <div className="input-group">
          <label>Project Name</label>
          <input onChange={(e) => setName(e.target.value)} />
        </div>

        {/* Location */}
        <div className="input-group">
          <label>Location</label>
          <select 
            value={location} 
            onChange={(e) => setLocation(e.target.value)}
            required
          >
            <option value="">Select a city...</option>
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>

        {/* Direction */}
        <div className="input-group">
          <label>North Direction</label>
          <select
            value={northArrow}
            onChange={(e) => setNorthArrow(e.target.value)}
            style={{ color: northArrow === "man" ? "#000" : "inherit" }}
          >
            <option value="N">North</option>
            <option value="S">South</option>
            <option value="E">East</option>
            <option value="W">West</option>
            <option value="man" style={{ color: "#000" }}>Manual</option>
          </select>
        </div>

        {/* Rooms */}
        <div className="input-group">
          <label>Rooms</label>

          {rooms.map((room, i) => (
            <div key={i} className="room-row">

              <input
                placeholder="Room name"
                value={room.name}
                onChange={(e) =>
                  updateRoom(i, "name", e.target.value)
                }
              />

              <input
                type="number"
                step="0.01"
                placeholder="Area (m²)"
                value={room.area === 0 ? "" : room.area}
                onChange={(e) =>
                  updateRoom(i, "area", e.target.value)
                }
              />

            </div>
          ))}

          <button
            type="button"
            onClick={addRoom}
            className="add-room-btn"
          >
            + Add Room
          </button>
        </div>

        {/* File Upload */}
        <div className="input-group">
          <label>Upload Floorplan</label>

          <label className="upload-box">
            <span>
              {file ? file.name : "Click to upload DXF/DWG"}
            </span>

            <input
              type="file"
              accept=".dxf,.dwg"
              hidden
              onChange={(e) =>
                setFile(e.target.files?.[0] || null)
              }
            />
          </label>
        </div>

        {/* Submit */}
        <button className="create-btn">
          Create Project
        </button>
      </form>
    </div>
  );
};

export default CreateProject;