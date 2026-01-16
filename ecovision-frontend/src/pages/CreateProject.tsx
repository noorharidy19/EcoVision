import { useState, type ChangeEvent } from "react";
import "../styles/createProject.css";

const CreateProject: React.FC = () => {
  const [projectName, setProjectName] = useState("");
  const [location, setLocation] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <div className="create-layout">
      {/* LEFT SIDE – Design Space */}
      <div className="design-space">
        <h1>Design Workspace</h1>
        <p>
          Your architectural design & AI visualizations will appear here.
        </p>

        <div className="design-placeholder">
          <span>Design Preview Area</span>
        </div>
      </div>

      {/* RIGHT SIDE – Create Project Card */}
      <div className="project-panel">
        <h2>Create Project</h2>

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
          <input
            type="text"
            placeholder="Cairo, Egypt"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label>Upload Floor Plan</label>
          <div className="upload-box">
            <input
              type="file"
              accept=".svg,.dwg,.dxf"
              onChange={handleFileChange}
            />
            <span>
              {file ? file.name : "SVG, DWG, DXF only"}
            </span>
          </div>
        </div>

        <button className="create-btn">
          Create Project
        </button>
      </div>
    </div>
  );
};

export default CreateProject;
