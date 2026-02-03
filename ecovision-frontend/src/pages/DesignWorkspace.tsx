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

interface Notification {
  message: string;
  type: "success" | "error" | "info";
}

const DesignWorkspace = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [floorplan, setFloorplan] = useState<Floorplan | null>(null);
  const [aiInput, setAiInput] = useState("");
  const [notification, setNotification] = useState<Notification | null>(null);
  const [delta, setDelta] = useState<any | null>(null);
  const [editedFileUrl, setEditedFileUrl] = useState<string | null>(null);
  const [oldVersionInfo, setOldVersionInfo] = useState<any | null>(null);
  const [newVersionInfo, setNewVersionInfo] = useState<any | null>(null);
  const [selectedVersionForAnalysis, setSelectedVersionForAnalysis] = useState<number | null>(null);

 useEffect(() => {
  if (id !== "new") {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No token found");
      return;
    }

    fetch(`http://127.0.0.1:8000/projects/${id}`, {
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch project: " + res.status);
        return res.json();
      })
      .then(data => {
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
          console.error("Error fetching floorplan");
          return null;
        }
        return res.json();
      })
      .then(data => {
        if (data) {
          setFloorplan(data);
        }
      })
      .catch(err => console.error(err));
  }
}, [id]);

  const showNotification = (message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };



  if (id === "new") {
    return <p>Create a new project here...</p>;
  }

  return (
    <div className="workspace-layout" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      {notification && (
        <div 
          style={{
            position: "fixed",
            top: "20px",
            right: "20px",
            padding: "15px 20px",
            borderRadius: "8px",
            color: "white",
            fontSize: "14px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            zIndex: 1000,
            backgroundColor: 
              notification.type === "success" ? "#4CAF50" :
              notification.type === "error" ? "#f44336" :
              "#2196F3",
            animation: "slideIn 0.3s ease-in"
          }}
        >
          {notification.message}
        </div>
      )}
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
      <div className="left-panel" style={{ maxWidth: "600px", width: "100%", padding: "20px" }}>
        {project ? (
          <div className="project-info-section" style={{ textAlign: "center" }}>
            <div className="project-info-card" style={{ margin: "0 auto", padding: "20px", border: "1px solid #ddd", borderRadius: "8px" }}>
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

            <div style={{ textAlign: "center", marginTop: "30px" }}>
              <input 
                type="text" 
                placeholder="Enter AI command" 
                className="edit-input-btn" 
                value={aiInput}
                onChange={(e) => setAiInput(e.target.value)}
                style={{ marginBottom: "15px", width: "100%", padding: "12px", fontSize: "16px", borderRadius: "4px", border: "1px solid #ccc", boxSizing: "border-box" }}
              />
              <button
                className="confirm-btn"
                onClick={async () => {
                  const token = localStorage.getItem("token");
                  if (!floorplan) return showNotification("No floorplan available", "error");
                  if (!aiInput.trim()) return showNotification("Command cannot be empty", "error");
                  try {
                    showNotification("Processing command...", "info");
                    const res = await fetch(`http://127.0.0.1:8000/floorplans/${floorplan.id}/ai_edit`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        "Authorization": token ? `Bearer ${token}` : ""
                      },
                      body: JSON.stringify({ command: aiInput })
                    });
                    if (!res.ok) throw new Error("AI request failed: " + res.status);
                    const data = await res.json();
                    if (!data.success) {
                      showNotification(data.error || "AI error", "error");
                      return;
                    }
                    setEditedFileUrl(data.edited_file || null);
                    setOldVersionInfo(null);
                    setNewVersionInfo(null);
                    showNotification("Ready to visualize", "success");
                  } catch (e: any) {
                    console.error(e);
                    showNotification(e.message || "Failed to call AI", "error");
                  }
                }}
                style={{ padding: "10px 30px", fontSize: "16px", backgroundColor: "#4CAF50", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
              >
                Enter
              </button>
            </div>
          </div>
        ) : (
          <p>Loading project...</p>
        )}

      </div>
      <div style={{ maxWidth: "600px", width: "100%", padding: "20px" }}>
        <div className="project-info-section" style={{ textAlign: "center" }}>
          <div className="project-info-card" style={{ margin: "0 auto", padding: "20px", border: "1px solid #ddd", borderRadius: "8px" }}>
            <h4>Changes Preview</h4>
            {editedFileUrl ? (
              <div style={{ textAlign: "center" }}>
                <div style={{ marginBottom: "15px", display: "flex", gap: "10px", justifyContent: "center" }}>
                  <a 
                    href={editedFileUrl.startsWith("http") ? editedFileUrl : `http://127.0.0.1:8000${editedFileUrl}`} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{ padding: "10px 20px", fontSize: "14px", backgroundColor: "#2196F3", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", textDecoration: "none" }}
                  >
                    Open
                  </a>
                </div>
                <div style={{ marginTop: "15px", display: "flex", gap: "10px", justifyContent: "center" }}>
                  <button
                    onClick={async () => {
                      const token = localStorage.getItem("token");
                      if (!floorplan) return showNotification("No floorplan available", "error");
                      try {
                        showNotification("Saving new version...", "info");
                        const res = await fetch(`http://127.0.0.1:8000/floorplans/${floorplan.id}/ai_edit`, {
                          method: "POST",
                          headers: {
                            "Content-Type": "application/json",
                            "Authorization": token ? `Bearer ${token}` : ""
                          },
                          body: JSON.stringify({ command: aiInput, confirm: true })
                        });
                        if (!res.ok) throw new Error("Save failed: " + res.status);
                        const data = await res.json();
                        if (!data.success) {
                          showNotification(data.error || "Save error", "error");
                          return;
                        }
                        // Refresh floorplan data from server to get updated version
                        const token = localStorage.getItem("token");
                        const refreshRes = await fetch(`http://127.0.0.1:8000/floorplans/project/${id}`, {
                          headers: { "Authorization": token ? `Bearer ${token}` : "" }
                        });
                        if (refreshRes.ok) {
                          const refreshData = await refreshRes.json();
                          setFloorplan(refreshData);
                        }
                        setEditedFileUrl(null);
                        setAiInput("");
                        setSelectedVersionForAnalysis(data.new_version);
                        showNotification(`Saved Version ${data.new_version}`, "success");
                      } catch (e: any) {
                        console.error(e);
                        showNotification(e.message || "Save failed", "error");
                      }
                    }}
                    style={{ padding: "8px 20px", fontSize: "14px", backgroundColor: "#4CAF50", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
                  >
                    Save Version {(floorplan?.version || 1) + 1}
                  </button>
                  <button
                    onClick={() => {
                      setEditedFileUrl(null);
                      setAiInput("");
                      showNotification("Changes discarded", "info");
                    }}
                    style={{ padding: "8px 20px", fontSize: "14px", backgroundColor: "#f44336", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
                  >
                    Undo
                  </button>
                </div>
              </div>
            ) : (
              <p style={{ color: "#777" }}>No changes yet</p>
            )}
            {selectedVersionForAnalysis && (
              <div style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid #eee" }}>
                <p style={{ marginBottom: "10px" }}><strong>Continue analysis on:</strong></p>
                <select
                  value={selectedVersionForAnalysis}
                  onChange={(e) => setSelectedVersionForAnalysis(parseInt(e.target.value))}
                  style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc", width: "100%", marginBottom: "10px" }}
                >
                  {floorplan && <option value={floorplan.version}>Version {floorplan.version}</option>}
                  {floorplan && floorplan.version > 1 && <option value={floorplan.version - 1}>Version {floorplan.version - 1}</option>}
                </select>
                <button
                  onClick={() => {
                    showNotification(`Ready to analyze Version ${selectedVersionForAnalysis}`, "info");
                    setSelectedVersionForAnalysis(null);
                  }}
                  style={{ padding: "8px 20px", fontSize: "14px", backgroundColor: "#2196F3", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", width: "100%" }}
                >
                  Analyze Version {selectedVersionForAnalysis}
                </button>
              </div>
            )}
          </div>
        </div>
        {editedFileUrl && (
          <div style={{ marginTop: "10px" }}>
            {(() => {
              const backendBase = "http://127.0.0.1:8000";
              const fullUrl = editedFileUrl.startsWith("http") ? editedFileUrl : `${backendBase}${editedFileUrl}`;
              const fileName = fullUrl.split("/").pop() || "edited.dxf";

              return (
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <a href={fullUrl} download={fileName} target="_blank" rel="noreferrer" style={{ color: "#1976d2" }}>
                    Download edited DXF
                  </a>
                  <button
                    onClick={async () => {
                      try {
                        showNotification("Preparing download...", "info");
                        const resp = await fetch(fullUrl, { headers: { Authorization: localStorage.getItem("token") ? `Bearer ${localStorage.getItem("token")}` : "" } });
                        if (!resp.ok) throw new Error("Failed to fetch file");
                        const blob = await resp.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = fileName;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                        showNotification("Download started", "success");
                      } catch (err: any) {
                        console.error(err);
                        showNotification(err.message || "Download failed", "error");
                      }
                    }}
                    style={{ padding: "6px 12px", borderRadius: "4px", border: "1px solid #1976d2", background: "white", color: "#1976d2", cursor: "pointer" }}
                  >
                    Quick Download
                  </button>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignWorkspace;
