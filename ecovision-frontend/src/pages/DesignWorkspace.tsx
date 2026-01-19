import { useState } from "react";
import "../styles/designWorkspace.css";

const DesignWorkspace = () => {
  const [mode, setMode] = useState<
    "edit" | "sustainability" | "visual" | "thermal"
  >("edit");

  return (
    <div className="workspace-layout">

      {/* LEFT SIDE */}
      <div className="left-panel">

        {/* Project Info Card */}
        <div className="project-info-section">
        <div className="project-info-card">
          <h3>Eco Villa Project</h3>
          <p><strong>ID:</strong> PRJ-001</p>
          <p><strong>Location:</strong> Cairo, Egypt</p>
          <p><strong>File:</strong> villa_plan.svg</p>

        </div>
<div > 
    <input type="text" placeholder="Edit Project (optional)" className="edit-input-btn"/>
    <button className="edit-project-btn">
           confirm
          </button></div>
          </div>
        {/* Design Area */}
        <div className="design-area">

          {/* Toolbar */}
          <div className="workspace-toolbar">
            <button onClick={() => setMode("sustainability")}>Sustainability</button>
            <button onClick={() => setMode("visual")}>Visual Comfort</button>
            <button onClick={() => setMode("thermal")}>Thermal Comfort</button>
          </div>

          {/* Preview */}
          <div className="design-preview">
            {mode === "sustainability" && "Sustainability Analysis"}
            {mode === "visual" && "Visual Comfort Analysis"}
            {mode === "thermal" && "Thermal Comfort Analysis"}
          </div>

        </div>
      </div>

    </div>
  );
};
export default DesignWorkspace;
