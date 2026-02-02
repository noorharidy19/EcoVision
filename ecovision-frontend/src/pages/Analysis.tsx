import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import "../styles/designWorkspace.css";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
  created_at: string;
}

const Analysis = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [mode, setMode] = useState<"edit" | "sustainability" | "visual" | "thermal">("edit");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id && id !== "new" && id !== "undefined") {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      console.log("Fetching project:", id);
      setLoading(true);
      setError(null);

      fetch(`http://127.0.0.1:8000/projects/${id}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })
        .then(async res => {
          console.log("Response status:", res.status);
          if (!res.ok) {
            const text = await res.text();
            console.error("Error response:", text);
            throw new Error(`HTTP ${res.status}: ${text}`);
          }
          return res.json();
        })
        .then(data => {
          console.log("Project loaded:", data);
          setProject(data);
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching project:", err);
          setError(err.message);
          setLoading(false);
        });
    } else {
      setLoading(false);
      setError(id === "undefined" ? "Invalid project ID in URL" : null);
    }
  }, [id]);

  if (id === "new") {
    return <p>Create a new project here...</p>;
  }

  return (
    <div className="workspace-layout">
      <div className="left-panel">
        {loading ? (
          <p>Loading project...</p>
        ) : error ? (
          <div style={{ color: "red", padding: "20px" }}>
            <p><strong>Error:</strong> {error}</p>
            <p>Check browser console for details</p>
          </div>
        ) : project ? (
          <div className="project-info-section">
            <div className="project-info-card">
              <h3>{project.name}</h3>
              <p><strong>ID:</strong> {project.id}</p>
              <p><strong>Location:</strong> {project.location}</p>
              <p><strong>File:</strong> {project.file_path}</p>
            </div>

           
          </div>
        ) : (
          <p>No project found</p>
        )}

        <div className="design-area">
          <div className="workspace-toolbar">
            <button onClick={() => setMode("sustainability")}>Sustainability</button>
            <button onClick={() => setMode("visual")}>Visual Comfort</button>
            <button onClick={() => setMode("thermal")}>Thermal Comfort</button>
          </div>

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

export default Analysis;
