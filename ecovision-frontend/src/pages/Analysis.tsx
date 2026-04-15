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

interface Floorplan {
  id: number;
  project_id: number;
  file_path: string;
  file_type: string;
  json_data?: any;
  version?: number;
}

const Analysis = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [floorplan, setFloorplan] = useState<Floorplan | null>(null);
  const [mode, setMode] = useState<"edit" | "sustainability" | "visual" | "thermal" | "recommendation">("edit");
  const [showRecommendationEditor, setShowRecommendationEditor] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>("dxf");
  const [exporting, setExporting] = useState(false);
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
          
          // Fetch floorplan data
          return fetch(`http://127.0.0.1:8000/floorplans/project/${id}`, {
            headers: {
              "Authorization": `Bearer ${token}`
            }
          });
        })
        .then(async res => {
          if (!res.ok) {
            const text = await res.text();
            console.error("Error fetching floorplan:", text);
            return null;
          }
          return res.json();
        })
        .then(data => {
          if (data) {
            console.log("Floorplan loaded:", data);
            setFloorplan(data);
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching data:", err);
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

  // TODO: Thermal & Visual models disabled - building new model
  // const runAnalysis = async (type: "thermal" | "visual") => { ... }

  const exportFile = async (format: string) => {
    if (!floorplan) {
      setError("No floorplan available to export");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setExporting(true);
    setError(null);

    try {
      const res = await fetch(`http://127.0.0.1:8000/floorplans/${floorplan.id}/export?format=${format}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Export failed: ${text}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const ext = format === "png" ? "png" : format;
      a.href = url;
      a.download = `${project?.name || "floorplan"}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="workspace-layout">
      <div className="left-panel" style={{ display: "grid", gridTemplateColumns: "0.8fr 1.5fr", gap: "20px" }}>
        <div>
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
                <p><strong>Project ID:</strong> {project.id}</p>
                <p><strong>Location:</strong> {project.location}</p>

                {floorplan && (
                  <>
                    <hr style={{ margin: "15px 0", borderColor: "#ddd" }} />
                    <h4 style={{ marginTop: "10px", marginBottom: "10px" }}>Floorplan Info</h4>
                    <p><strong>Floorplan ID:</strong> {floorplan.id}</p>
                    <p><strong>File Type:</strong> {floorplan.file_type}</p>
                    <p><strong>File Path:</strong> {floorplan.file_path}</p>
                  </>
                )}
              </div>
             
            </div>
          ) : (
            <p>No project found</p>
          )}
        </div>

        <div className="design-area">
          <div className="workspace-toolbar">
            {/* Thermal & Visual analysis disabled - building new model */}
            <button onClick={() => setMode("sustainability")}>Sustainability</button>
            <button 
              onClick={() => setMode("recommendation")}
              disabled={!floorplan}
              style={{ marginLeft: "8px", opacity: !floorplan ? 0.5 : 1, cursor: !floorplan ? "not-allowed" : "pointer" }}
            >
              Recommendations
            </button>
          </div>

          <div className="design-preview">
            {error && <div style={{ color: "red", padding: "10px" }}>❌ {error}</div>}
            
            {mode === "edit" && (
              <div style={{ padding: "20px" }}>
                <p>Select an analysis type to get started</p>
                {!floorplan && <p style={{ color: "orange" }}>Floorplan data not yet loaded</p>}
              </div>
            )}

            {mode === "sustainability" && (
              <div style={{ padding: "20px" }}>
                <h4>Sustainability Analysis</h4>
                <p>Sustainability analysis coming soon...</p>
              </div>
            )}

            {mode === "recommendation" && (
              <div style={{ padding: "20px" }}>
                <h4>Edit Recommendation Mode</h4>
                <p>Here you can edit recommendations for this project.</p>
                <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                  <button onClick={() => setShowRecommendationEditor(true)}>Open Editor</button>
                  <button onClick={() => setMode('edit')}>Close</button>
                </div>
              
              {showRecommendationEditor && (
                <div style={{ marginTop: "16px", border: "1px solid #eee", padding: "12px", borderRadius: "8px", background: "#fff" }}>
                  <h5 style={{ marginTop: 0 }}>Recommendation Editor</h5>
                  <p>Edit recommendations for this project here. Changes are local until you save.</p>

                  <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "12px" }}>
                    <label style={{ fontWeight: 600 }}>Save as:</label>
                    <select value={exportFormat} onChange={e => setExportFormat(e.target.value)}>
                      <option value="dxf">DXF</option>
                      <option value="dwg">DWG</option>
                      <option value="pdf">PDF</option>
                      <option value="png">Image (PNG)</option>
                    </select>
                    <button onClick={() => exportFile(exportFormat)} disabled={!floorplan || exporting} style={{ marginLeft: "8px" }}>
                      {exporting ? "Exporting..." : "Save/Export"}
                    </button>
                    <button onClick={() => setShowRecommendationEditor(false)}>Close Editor</button>
                  </div>

                  <div style={{ marginTop: "12px", color: "#666" }}>
                    <small>If your backend exposes a floorplan export endpoint this will request a converted file from the server. If not available, you'll see an error message.</small>
                  </div>
                </div>
              )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;
