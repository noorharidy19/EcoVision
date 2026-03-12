import { useState, type ChangeEvent, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/createProject.css";

const EGYPT_LOCATIONS = [
  "Cairo",
  "Alexandria",
  "Giza",
  "Helwan",
  "6th of October City",
  "New Cairo",
  "Zamalek",
  "Maadi",
  "Heliopolis",
  "Nasr City",
  "Shubra",
  "Tanta",
  "Mansoura",
  "Port Said",
  "Ismailia",
  "Suez",
  "Aswan",
  "Luxor",
  "Hurghada",
  "Marsa Alam"
];

const CreateProject: React.FC = () => {
  const [projectName, setProjectName] = useState("");
  const [location, setLocation] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const navigate = useNavigate();

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!projectName || !location || !file) {
      alert("Please fill all fields and upload a file");
      return;
    }

    const formData = new FormData();
    formData.append("name", projectName);
    formData.append("location", location);
    formData.append("file", file);

    const token = localStorage.getItem("token");

    try {
      const response = await fetch("http://127.0.0.1:8000/projects", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      alert("Project created successfully!");
      navigate("/myprojects");

    } catch (error) {
      console.error("Error:", error);
      alert("Error creating project");
    }
  };

  return (
    <div className="create-layout">
      {/* LEFT SIDE */}
      <div className="design-space">
        <h1>Design Workspace</h1>
        <p>Your architectural design & AI visualizations will appear here.</p>

        <div className="design-placeholder">
          <span>Design Preview Area</span>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div className="project-panel">
        <h2>Create Project</h2>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Project Name</label>
            <input
              type="text"
              placeholder="Eco Villa Project"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Location</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{
                padding: "14px 16px",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                fontSize: "15px",
                backgroundColor: "white",
                color: "#000",
                cursor: "pointer",
                appearance: "none",
                backgroundImage: "url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27%23000%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3e%3cpolyline points=%276 9 12 15 18 9%3e%3c/polyline%3e%3c/svg%3e')",
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 10px center",
                backgroundSize: "20px",
                paddingRight: "40px"
              }}
            >
              <option value="" style={{ color: "#666" }}>Select a location in Egypt</option>
              {EGYPT_LOCATIONS.map((loc) => (
                <option key={loc} value={loc} style={{ color: "#000" }}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label>Upload Floor Plan</label>
            <div className="upload-box">
              <input
                type="file"
                accept=".dwg,.dxf"
                onChange={handleFileChange}
              />
              <span>{file ? file.name : "DWG, DXF only"}</span>
            </div>
          </div>

          <button type="submit" className="create-btn">
            Create Project
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreateProject;
