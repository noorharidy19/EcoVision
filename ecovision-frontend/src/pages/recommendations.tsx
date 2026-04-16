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

type RecommendationMode = "overview" | "thermal" | "visual" | "sustainability" | "material";

const Recommendations = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [floorplan, setFloorplan] = useState<Floorplan | null>(null);
  const [mode, setMode] = useState<RecommendationMode>("overview");
  const [showEditor, setShowEditor] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>("dxf");
  const [exporting, setExporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Recommendation states
  const [thermalData, setThermalData] = useState<any>(null);
  const [thermalLoading, setThermalLoading] = useState(false);
  
  const [visualData, setVisualData] = useState<any>(null);
  const [visualLoading, setVisualLoading] = useState(false);
  
  const [sustainabilityData, setSustainabilityData] = useState<any>(null);
  const [sustainabilityLoading, setSustainabilityLoading] = useState(false);
  
  const [materialData, setMaterialData] = useState<any>(null);
  const [materialLoading, setMaterialLoading] = useState(false);

  // Load project and floorplan data
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

  // Generate Thermal Comfort recommendations
  const generateThermalRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setThermalLoading(true);
    setError(null);

    try {
      // TODO: Backend endpoint /recommendations/thermal not yet implemented
      setError("Thermal recommendations endpoint is under development");
      setMode("thermal");
    } finally {
      setThermalLoading(false);
    }
  };

  // Generate Visual Comfort recommendations
  const generateVisualRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setVisualLoading(true);
    setError(null);

    try {
      // TODO: Backend endpoint /recommendations/visual not yet implemented
      setError("Visual recommendations endpoint is under development");
      setMode("visual");
    } finally {
      setVisualLoading(false);
    }
  };

  // Generate Sustainability recommendations
  const generateSustainabilityRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setSustainabilityLoading(true);
    setError(null);

    try {
      // TODO: Backend endpoint /recommendations/sustainability not yet implemented
      setError("Sustainability recommendations endpoint is under development");
      setMode("sustainability");
    } finally {
      setSustainabilityLoading(false);
    }
  };

  // Generate Material Selection recommendations
  const generateMaterialRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setMaterialLoading(true);
    setError(null);

    try {
      // TODO: Backend endpoint /recommendations/material not yet implemented
      setError("Material recommendations endpoint is under development");
      setMode("material");
    } finally {
      setMaterialLoading(false);
    }
  };

  // Export file
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

  // Helper function to render recommendation data
  const renderRecommendationContent = (data: any, title: string, icon: string) => {
    return (
      <div style={{ padding: "20px" }}>
        <h4>{icon} {title}</h4>
        
        {data ? (
          <div>
            {data.formatted && (
              <div style={{ backgroundColor: "#f0f8f0", padding: "15px", borderRadius: "8px", marginBottom: "20px", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "14px" }}>
                {data.formatted}
              </div>
            )}
            
            {data.recommendations && data.recommendations.length > 0 && (
              <div style={{ marginTop: "20px" }}>
                <h5>Detailed Recommendations ({data.total || data.recommendations.length})</h5>
                <div style={{ display: "grid", gap: "15px" }}>
                  {data.recommendations.map((rec: any, idx: number) => (
                    <div key={idx} style={{ 
                      border: "1px solid #ddd", 
                      padding: "15px", 
                      borderRadius: "8px",
                      backgroundColor: "#fafafa"
                    }}>
                      <h6 style={{ marginTop: 0 }}>{rec.room} - {rec.category}</h6>
                      {rec.impact && <p><strong>Impact:</strong> {rec.impact}</p>}
                      {rec.issue && <p><strong>Issue:</strong> {rec.issue}</p>}
                      {rec.recommendation && <p><strong>Recommendation:</strong> {rec.recommendation}</p>}
                      {rec.priority && <p><strong>Priority:</strong> {rec.priority}</p>}
                      {rec.triggers && rec.triggers.length > 0 && (
                        <p><strong>Affects:</strong> {rec.triggers.join(", ")}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button onClick={() => setShowEditor(true)} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Edit</button>
              <button onClick={() => setMode('overview')} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Back</button>
            </div>
          </div>
        ) : (
          <div>
            <p>Click the button to generate {title.toLowerCase()}.</p>
            <button onClick={() => setMode('overview')} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Back</button>
          </div>
        )}
      </div>
    );
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
            <button 
              onClick={generateThermalRecommendations}
              disabled={!floorplan || thermalLoading}
              style={{ 
                backgroundColor: mode === "thermal" ? "#FF6B6B" : undefined,
                opacity: !floorplan || thermalLoading ? 0.5 : 1, 
                cursor: !floorplan || thermalLoading ? "not-allowed" : "pointer" 
              }}
            >
              {thermalLoading ? "Analyzing..." : "🌡️ Thermal Comfort"}
            </button>
            <button 
              onClick={generateVisualRecommendations}
              disabled={!floorplan || visualLoading}
              style={{ 
                backgroundColor: mode === "visual" ? "#4ECDC4" : undefined,
                opacity: !floorplan || visualLoading ? 0.5 : 1, 
                cursor: !floorplan || visualLoading ? "not-allowed" : "pointer" 
              }}
            >
              {visualLoading ? "Analyzing..." : "✨ Visual Comfort"}
            </button>
            <button 
              onClick={generateSustainabilityRecommendations}
              disabled={!floorplan || sustainabilityLoading}
              style={{ 
                backgroundColor: mode === "sustainability" ? "#95E77D" : undefined,
                opacity: !floorplan || sustainabilityLoading ? 0.5 : 1, 
                cursor: !floorplan || sustainabilityLoading ? "not-allowed" : "pointer" 
              }}
            >
              {sustainabilityLoading ? "Analyzing..." : "🌿 Sustainability"}
            </button>
            <button 
              onClick={generateMaterialRecommendations}
              disabled={!floorplan || materialLoading}
              style={{ 
                backgroundColor: mode === "material" ? "#FFB84D" : undefined,
                opacity: !floorplan || materialLoading ? 0.5 : 1, 
                cursor: !floorplan || materialLoading ? "not-allowed" : "pointer" 
              }}
            >
              {materialLoading ? "Analyzing..." : "🏗️ Material Selection"}
            </button>
          </div>

          <div className="design-preview">
            {error && <div style={{ color: "red", padding: "10px" }}>❌ {error}</div>}
            
            {mode === "overview" && (
              <div style={{ padding: "20px" }}>
                <h4>Recommendations & Analysis</h4>
                <p>Select a category to view detailed recommendations:</p>
                <ul>
                  <li><strong>🌡️ Thermal Comfort</strong> - Temperature, insulation, and HVAC recommendations</li>
                  <li><strong>✨ Visual Comfort</strong> - Lighting, daylight, and visual quality recommendations</li>
                  <li><strong>🌿 Sustainability</strong> - Environmental and energy efficiency recommendations</li>
                  <li><strong>🏗️ Material Selection</strong> - Material and construction recommendations</li>
                </ul>
                {!floorplan && <p style={{ color: "orange" }}>⚠️ Floorplan data not yet loaded</p>}
              </div>
            )}

            {mode === "thermal" && renderRecommendationContent(thermalData, "Thermal Comfort Recommendations", "🌡️")}
            {mode === "visual" && renderRecommendationContent(visualData, "Visual Comfort Recommendations", "✨")}
            {mode === "sustainability" && renderRecommendationContent(sustainabilityData, "Sustainability Recommendations", "🌿")}
            {mode === "material" && renderRecommendationContent(materialData, "Material Selection Recommendations", "🏗️")}

            {showEditor && (
              <div style={{ marginTop: "16px", border: "1px solid #eee", padding: "12px", borderRadius: "8px", background: "#fff", position: "absolute", bottom: 0, right: 0, width: "300px", zIndex: 1000 }}>
                <h5 style={{ marginTop: 0 }}>Recommendation Editor</h5>
                <p style={{ fontSize: "12px" }}>Edit recommendations here. Changes are local until you save.</p>

                <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "12px" }}>
                  <label style={{ fontWeight: 600, fontSize: "12px" }}>Save as:</label>
                  <select value={exportFormat} onChange={e => setExportFormat(e.target.value)} style={{ fontSize: "12px", padding: "5px" }}>
                    <option value="dxf">DXF</option>
                    <option value="dwg">DWG</option>
                    <option value="pdf">PDF</option>
                    <option value="png">Image (PNG)</option>
                  </select>
                  <button onClick={() => exportFile(exportFormat)} disabled={!floorplan || exporting} style={{ marginLeft: "8px", padding: "5px 10px", fontSize: "12px" }}>
                    {exporting ? "Exporting..." : "Save"}
                  </button>
                  <button onClick={() => setShowEditor(false)} style={{ padding: "5px 10px", fontSize: "12px" }}>Close</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;
