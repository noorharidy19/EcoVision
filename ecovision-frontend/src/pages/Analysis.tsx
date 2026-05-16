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
  const [mode, setMode] = useState<"overview" | "explanation" | "recommendation" | "rooms">("overview");
  const [showRecommendationEditor, setShowRecommendationEditor] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>("dxf");
  const [exporting, setExporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [roomExplanations, setRoomExplanations] = useState<any[]>([]);
  const [roomExplanationsLoading, setRoomExplanationsLoading] = useState(false);
  const [editedOrientations, setEditedOrientations] = useState<Record<string, string>>({});

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

  const generateRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setRecommendationsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommendations/generate", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const data = await response.json();
      console.log("Recommendations:", data);
      setRecommendations(data);
      setMode("recommendation");
    } catch (err) {
      console.error("Error generating recommendations:", err);
      setError(err instanceof Error ? err.message : "Failed to generate recommendations");
    } finally {
      setRecommendationsLoading(false);
    }
  };

  const generateExplanation = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setExplanationLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommendations/explain", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const data = await response.json();
      console.log("Explanation:", data);
      setExplanation(data.explanation);
      setMode("explanation");
    } catch (err) {
      console.error("Error generating explanation:", err);
      setError(err instanceof Error ? err.message : "Failed to generate explanation");
    } finally {
      setExplanationLoading(false);
    }
  };

  const loadRoomExplanations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setRoomExplanationsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommendations/rooms/explanations", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const data = await response.json();
      const rooms = data.rooms || [];
      setRoomExplanations(rooms);

      const initialOrientations: Record<string, string> = {};
      rooms.forEach((room: any) => {
        initialOrientations[room.room_name] = room.current_orientation || "UNKNOWN";
      });
      setEditedOrientations(initialOrientations);
      setMode("rooms");
    } catch (err) {
      console.error("Error loading room explanations:", err);
      setError(err instanceof Error ? err.message : "Failed to load room explanations");
    } finally {
      setRoomExplanationsLoading(false);
    }
  };

  const saveRoomOrientation = async (roomName: string, orientation: string) => {
    if (!floorplan) {
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    // Helper: reload floorplan from database to get fresh updated data
    const reloadFloorplanData = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/floorplans/project/${id}`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          setFloorplan(data);
          return data;
        }
      } catch (err) {
        console.error("Error reloading floorplan:", err);
      }
      return null;
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/recommendations/rooms/update-orientation", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id,
          room_name: roomName,
          orientation
        })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      setRoomExplanations((prev) =>
        prev.map((room) =>
          room.room_name === roomName
            ? {
                ...room,
                current_orientation: orientation,
                explanation:
                  typeof room.explanation === "string"
                    ? room.explanation.replace(/Current orientation is\s+[^.]+\./i, `Current orientation is ${orientation}.`)
                    : room.explanation,
              }
            : room
        )
      );

      setFloorplan((prev) => {
        if (!prev?.json_data?.rooms) {
          return prev;
        }

        const updatedRooms = prev.json_data.rooms.map((room: any) =>
          room.name === roomName
            ? {
                ...room,
                orientation,
                primary_direction: orientation,
                user_edited_orientation: true,
              }
            : room
        );

        return {
          ...prev,
          json_data: {
            ...prev.json_data,
            rooms: updatedRooms,
          },
        };
      });

      // Clear previous summary so user can regenerate explanation using latest saved orientation.
      setExplanation(null);

      // Reload floorplan from database to get fresh updated data.
      const freshFloorplan = await reloadFloorplanData();
      if (!freshFloorplan) {
        console.warn("Could not reload floorplan data after orientation save");
      }

      // Regenerate summary immediately using fresh floorplan data from database.
      try {
        const explainResponse = await fetch("http://127.0.0.1:8000/recommendations/explain", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            floorplan_id: freshFloorplan?.id || floorplan.id
          })
        });

        if (explainResponse.ok) {
          const explainData = await explainResponse.json();
          setExplanation(explainData.explanation || null);
        }
      } catch (refreshErr) {
        console.error("Could not refresh explanation after orientation update:", refreshErr);
      }
    } catch (err) {
      console.error("Error saving room orientation:", err);
      setError(err instanceof Error ? err.message : "Failed to save room orientation");
    }
  };

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
            <button 
              onClick={generateExplanation}
              disabled={!floorplan || explanationLoading}
              style={{ 
                backgroundColor: mode === "explanation" ? "#4CAF50" : undefined,
                opacity: !floorplan || explanationLoading ? 0.5 : 1, 
                cursor: !floorplan || explanationLoading ? "not-allowed" : "pointer" 
              }}
            >
              {explanationLoading ? "Analyzing..." : "📋 Explanation"}
            </button>
            <button 
              onClick={generateRecommendations}
              disabled={!floorplan || recommendationsLoading}
              style={{ 
                marginLeft: "8px",
                backgroundColor: mode === "recommendation" ? "#2196F3" : undefined,
                opacity: !floorplan || recommendationsLoading ? 0.5 : 1, 
                cursor: !floorplan || recommendationsLoading ? "not-allowed" : "pointer" 
              }}
            >
              {recommendationsLoading ? "Generating..." : "🌿 Recommendations"}
            </button>
            <button 
              onClick={loadRoomExplanations}
              disabled={!floorplan || roomExplanationsLoading}
              style={{ 
                marginLeft: "8px",
                backgroundColor: mode === "rooms" ? "#8B5CF6" : undefined,
                opacity: !floorplan || roomExplanationsLoading ? 0.5 : 1,
                cursor: !floorplan || roomExplanationsLoading ? "not-allowed" : "pointer"
              }}
            >
              {roomExplanationsLoading ? "Loading..." : "📍 Room Analysis"}
            </button>
          </div>

          <div className="design-preview">
            {error && <div style={{ color: "red", padding: "10px" }}>❌ {error}</div>}
            
            {mode === "overview" && (
              <div style={{ padding: "20px" }}>
                <p>Select an analysis type to get started:</p>
                <ul>
                  <li><strong>📋 Explanation</strong> - Get a professional floor plan summary</li>
                  <li><strong>🌿 Recommendations</strong> - View sustainability recommendations</li>
                  <li><strong>📍 Room Analysis</strong> - Llama room explanation + optional orientation update</li>
                </ul>
                {!floorplan && <p style={{ color: "orange" }}>⚠️ Floorplan data not yet loaded</p>}
              </div>
            )}

            {mode === "explanation" && (
              <div style={{ padding: "20px" }}>
                <h4>📋 Floor Plan Summary</h4>
                
                {explanation ? (
                  <div style={{ backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", whiteSpace: "pre-wrap", lineHeight: "1.6", fontFamily: "Georgia, serif", fontSize: "15px", marginBottom: "20px" }}>
                    {explanation}
                  </div>
                ) : (
                  <div>
                    <p>Click "📋 Explanation" to generate a professional analysis of your floor plan.</p>
                  </div>
                )}
              </div>
            )}

            {mode === "rooms" && (
              <div style={{ padding: "20px" }}>
                <h4>📍 Room Analysis</h4>
                <p style={{ color: "#666", marginBottom: "16px" }}>
                  Optional: change room orientation from dropdown. Your selection is saved automatically.
                </p>

                {roomExplanations.length > 0 ? (
                  <div style={{ display: "grid", gap: "12px" }}>
                    {roomExplanations.map((room: any, idx: number) => (
                      <div
                        key={`${room.room_name}-${idx}`}
                        style={{ border: "1px solid #ddd", borderRadius: "8px", padding: "14px", backgroundColor: "#fafafa" }}
                      >
                        <h6 style={{ marginTop: 0, marginBottom: "8px" }}>{room.room_name}</h6>
                        <p style={{ margin: "0 0 8px 0", color: "#333" }}>{room.explanation}</p>
                        <p style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#666" }}>
                          <strong>Area:</strong> {room.area_m2} m2
                        </p>
                        {room.window_directions && room.window_directions.length > 0 && (
                          <p style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#666" }}>
                            <strong>Window Directions:</strong> {room.window_directions.join(", ")}
                          </p>
                        )}

                        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <label style={{ fontWeight: 600 }}>Orientation:</label>
                          <select
                            value={editedOrientations[room.room_name] || "UNKNOWN"}
                            onChange={async (e) => {
                              const selected = e.target.value;
                              setEditedOrientations((prev) => ({
                                ...prev,
                                [room.room_name]: selected,
                              }));
                              await saveRoomOrientation(room.room_name, selected);
                            }}
                          >
                            <option value="UNKNOWN">UNKNOWN</option>
                            <option value="N">N</option>
                            <option value="NE">NE</option>
                            <option value="E">E</option>
                            <option value="SE">SE</option>
                            <option value="S">S</option>
                            <option value="SW">SW</option>
                            <option value="W">W</option>
                            <option value="NW">NW</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No rooms available. Click Room Analysis to load room explanations.</p>
                )}

                <div style={{ marginTop: "16px" }}>
                  <button onClick={() => setMode("overview")}>Back</button>
                </div>
              </div>
            )}

            {mode === "recommendation" && (
              <div style={{ padding: "20px" }}>
                <h4>🌿 Sustainability Recommendations</h4>
                
                {recommendations ? (
                  <div>
                    <div style={{ backgroundColor: "#f0f8f0", padding: "15px", borderRadius: "8px", marginBottom: "20px", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "14px" }}>
                      {recommendations.formatted}
                    </div>
                    
                    {recommendations.recommendations && recommendations.recommendations.length > 0 && (
                      <div style={{ marginTop: "20px" }}>
                        <h5>Detailed Recommendations ({recommendations.total})</h5>
                        <div style={{ display: "grid", gap: "15px" }}>
                          {recommendations.recommendations.map((rec: any, idx: number) => (
                            <div key={idx} style={{ 
                              border: "1px solid #ddd", 
                              padding: "15px", 
                              borderRadius: "8px",
                              backgroundColor: "#fafafa"
                            }}>
                              <h6 style={{ marginTop: 0 }}>{rec.room} - {rec.category}</h6>
                              <p><strong>Impact:</strong> {rec.impact}</p>
                              <p><strong>Issue:</strong> {rec.issue}</p>
                              <p><strong>Recommendation:</strong> {rec.recommendation}</p>
                              {rec.triggers && rec.triggers.length > 0 && (
                                <p><strong>Affects:</strong> {rec.triggers.join(", ")}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                      <button onClick={() => setShowRecommendationEditor(true)}>Edit</button>
                      <button onClick={() => setMode('overview')}>Back</button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p>Click "🌿 Recommendations" to generate sustainability recommendations.</p>
                    <button onClick={() => setMode('overview')}>Back</button>
                  </div>
                )}
              
              {showRecommendationEditor && (
                <div style={{ marginTop: "16px", border: "1px solid #eee", padding: "12px", borderRadius: "8px", background: "#fff" }}>
                  <h5 style={{ marginTop: 0 }}>Recommendation Editor</h5>
                  <p>Edit recommendations here. Changes are local until you save.</p>

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
                    <small>Export recommendations with your floorplan to DXF, DWG, PDF, or PNG format.</small>
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
