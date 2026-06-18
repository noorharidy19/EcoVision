import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/createProject.css";

type Room = {
  name: string;
  area: number;
};

const CITIES = ["Cairo", "Aswan", "Alexandria", "Port Said", "Dahab", "Hurghada"];

// ─── DXF Preview Component ───────────────────────────────────────────────────
const DxfPreview = ({ file }: { file: File }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let destroyed = false;

    const loadDxf = async () => {
      if (!containerRef.current) return;
      setLoading(true);
      setError(null);

      try {
        const { DxfViewer } = await import("dxf-viewer");
        const { Color, Vector3 } = await import("three");

        if (destroyed) return;

        if (viewerRef.current) {
          try { viewerRef.current.Destroy(); } catch {}
          viewerRef.current = null;
        }

        const container = containerRef.current;
        const W = container.clientWidth;
        const H = container.clientHeight;

        const viewer = new DxfViewer(container, {
          canvasWidth: W,
          canvasHeight: H,
          autoResize: true,
          colorCorrection: true,
          blackWhiteInversion: false,
          clearColor: new Color("#f1fdf8"),
          pointSize: 2,
        });

        viewerRef.current = viewer;

        const url = URL.createObjectURL(file);
        await viewer.Load({
          url,
          fonts: [
            "https://fonts.gstatic.com/s/roboto/v30/KFOmCnqEu92Fr1Mu4mxP.ttf",
            "https://fonts.gstatic.com/s/opensans/v36/memSYaGs126MiZpBA-UvWbX2vVnXBbObj2OVZyOOSr4dVJWUgsiH0C4n.ttf",
          ]
        });
        URL.revokeObjectURL(url);

        if (!destroyed) {
          // Use SetView: center on bounds, set width to span the whole drawing
          const bounds = viewer.GetBounds();
          if (bounds) {
            const cx = (bounds.minX + bounds.maxX) / 2;
            const cy = (bounds.minY + bounds.maxY) / 2;
            const drawingWidth  = bounds.maxX - bounds.minX;
            const drawingHeight = bounds.maxY - bounds.minY;
            const aspect = W / H;
            // Pick whichever dimension needs more space, add 10% padding
            const viewWidth = Math.max(drawingWidth, drawingHeight * aspect) * 1.1;
            viewer.SetView(new Vector3(cx, cy, 0), viewWidth);
          }
          setLoading(false);
        }

      } catch (err: any) {
        console.error("DXF load error:", err);
        if (!destroyed) {
          setError("Could not render DXF preview");
          setLoading(false);
        }
      }
    };

    loadDxf();

    return () => {
      destroyed = true;
      if (viewerRef.current) {
        try { viewerRef.current.Destroy(); } catch {}
        viewerRef.current = null;
      }
    };
  }, [file]);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: "100%",
          borderRadius: "8px",
          overflow: "hidden",
          opacity: loading ? 0 : 1,
          transition: "opacity 0.4s ease",
        }}
      />

      {loading && !error && (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          background: "#f1fdf8", borderRadius: "8px", gap: "14px",
          color: "#2e7d5e",
        }}>
          <div style={{
            width: "40px", height: "40px",
            border: "3px solid #c8e6c9",
            borderTop: "3px solid #2e7d5e",
            borderRadius: "50%",
            animation: "spin 0.9s linear infinite",
          }} />
          <p style={{ margin: 0, fontSize: "13px", fontWeight: 500 }}>Rendering floorplan…</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {error && (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          background: "#f1fdf8", borderRadius: "8px", gap: "8px",
          color: "#2e7d5e",
        }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <p style={{ margin: 0, fontSize: "14px", fontWeight: 600 }}>{file.name}</p>
          <p style={{ margin: 0, fontSize: "12px", opacity: 0.6 }}>Preview unavailable for this file</p>
        </div>
      )}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
const CreateProject = () => {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [northArrow, setNorthArrow] = useState("N");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [rooms, setRooms] = useState<Room[]>([{ name: "", area: 0 }]);

  useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl); };
  }, [previewUrl]);

  const addRoom = () => setRooms([...rooms, { name: "", area: 0 }]);

  const updateRoom = (index: number, field: keyof Room, value: string) => {
    const updated = [...rooms];
    if (field === "area") {
      const num = parseFloat(value);
      updated[index].area = isNaN(num) ? 0 : num;
    } else {
      updated[index].name = value;
    }
    setRooms(updated);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null;
    if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null); }
    setFile(selected);
    if (selected) {
      const ext = selected.name.split(".").pop()?.toLowerCase() || "";
      if (["png", "jpg", "jpeg", "webp"].includes(ext)) {
        setPreviewUrl(URL.createObjectURL(selected));
      }
    }
  };

  const submit = async (e: React.FormEvent) => {
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
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const data = await res.json();
    if (res.ok) {
      alert("Project Created Successfully");
      navigate("/myprojects");
    } else {
      alert(data.detail || "Error creating project");
    }
  };

  const fileExt = file?.name.split(".").pop()?.toLowerCase() || "";
  const isDxf = file && ["dxf", "dwg"].includes(fileExt);
  const isImage = file && ["png", "jpg", "jpeg", "webp"].includes(fileExt);

  return (
    <div className="create-layout">
      <div className="design-space">
        <h1>Create Your Project</h1>
        <p>Upload your floorplan, define rooms with area, and let EcoVision analyze your building intelligently.</p>

        <div className="design-placeholder">
          {isImage && previewUrl ? (
            <img src={previewUrl} alt="Floorplan Preview"
              style={{ width: "100%", height: "100%", objectFit: "contain", borderRadius: "8px" }} />
          ) : isDxf ? (
            <DxfPreview file={file!} />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", gap: "10px", height: "100%", color: "#2e7d5e", opacity: 0.5 }}>
              <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>EcoVision AI Preview</p>
              <p style={{ margin: 0, fontSize: "12px" }}>Upload a floorplan to see it here</p>
            </div>
          )}
        </div>
      </div>

      <form className="project-panel" onSubmit={submit}>
        <h2>New Project</h2>

        <div className="input-group">
          <label>Project Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Green Villa" required />
        </div>

        <div className="input-group">
          <label>Location</label>
          <select value={location} onChange={(e) => setLocation(e.target.value)} required>
            <option value="">Select a city…</option>
            {CITIES.map((city) => <option key={city} value={city}>{city}</option>)}
          </select>
        </div>

        <div className="input-group">
          <label>North Direction</label>
          <select value={northArrow} onChange={(e) => setNorthArrow(e.target.value)}>
            <option value="N">North</option>
            <option value="S">South</option>
            <option value="E">East</option>
            <option value="W">West</option>
            <option value="man">Manual</option>
          </select>
        </div>

        <div className="input-group">
          <label>Rooms</label>
          {rooms.map((room, i) => (
            <div key={i} className="room-row">
              <input placeholder="Room name" value={room.name}
                onChange={(e) => updateRoom(i, "name", e.target.value)} />
              <input type="number" step="0.01" placeholder="Area (m²)"
                value={room.area === 0 ? "" : room.area}
                onChange={(e) => updateRoom(i, "area", e.target.value)} />
            </div>
          ))}
          <button type="button" onClick={addRoom} className="add-room-btn">+ Add Room</button>
        </div>

        <div className="input-group">
          <label>Upload Floorplan</label>
          <label className="upload-box">
            <span>{file ? file.name : "Click to upload DXF / DWG / PNG"}</span>
            <input type="file" accept=".dxf,.dwg,.png,.jpg,.jpeg" hidden onChange={handleFileChange} />
          </label>
        </div>

        <button type="submit" className="create-btn">Create Project</button>
      </form>
    </div>
  );
};

export default CreateProject;
