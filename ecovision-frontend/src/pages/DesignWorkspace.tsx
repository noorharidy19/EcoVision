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
                onClick={() => showNotification("AI command confirmed!", "success")}
                style={{ padding: "10px 30px", fontSize: "16px", backgroundColor: "#4CAF50", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
              >
                Confirm
              </button>
            </div>
          </div>
        ) : (
          <p>Loading project...</p>
        )}

      </div>
    </div>
  );
};

export default DesignWorkspace;
