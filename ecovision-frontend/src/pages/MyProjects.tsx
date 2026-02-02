import "../styles/myprojects.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
}

interface Notification {
  message: string;
  type: "success" | "error" | "info";
}

const MyProjects = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [notification, setNotification] = useState<Notification | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [editingProject, setEditingProject] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
  const token = localStorage.getItem("token");
  if (!token) return;

  fetch("http://127.0.0.1:8000/projects/", {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
    .then(res => {
      if (!res.ok) throw new Error("Unauthorized");
      return res.json();
    })
    .then(data => setProjects(data))
    .catch(err => console.error("Error fetching projects:", err));
}, []);

  const showNotification = (message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const deleteProject = async (projectId: number) => {
    setDeleting(projectId);
    try {
      const response = await fetch(`http://127.0.0.1:8000/projects/${projectId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`
        }
      });

      if (!response.ok) {
        throw new Error("Failed to delete project");
      }

      // Remove from local state
      setProjects(projects.filter(p => p.id !== projectId));
      setDeleteConfirm(null);
      showNotification("Project deleted successfully!", "success");
    } catch (err) {
      console.error("Error deleting project:", err);
      showNotification("Failed to delete project", "error");
    } finally {
      setDeleting(null);
    }
  };

  const updateProject = async (projectId: number) => {
    const token = localStorage.getItem("token");
    if (!token || !editName.trim() || !editLocation.trim()) return;

    setUpdating(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/projects/${projectId}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: editName,
          location: editLocation
        })
      });

      if (!response.ok) {
        throw new Error("Failed to update project");
      }

      const updatedProject = await response.json();
      setProjects(projects.map(p => p.id === projectId ? { ...p, name: updatedProject.name, location: updatedProject.location } : p));
      setEditingProject(null);
      showNotification("Project updated successfully!", "success");
    } catch (err) {
      console.error("Error updating project:", err);
      showNotification("Failed to update project", "error");
    } finally {
      setUpdating(false);
    }
  };

  const startEditing = (project: Project) => {
    setEditingProject(project.id);
    setEditName(project.name);
    setEditLocation(project.location);
  };

  const cancelEditing = () => {
    setEditingProject(null);
    setEditName("");
    setEditLocation("");
  };



  return (
    <div className="dashboard-container">
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

      {deleteConfirm && (
        <div 
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 999
          }}
        >
          <div 
            style={{
              backgroundColor: "white",
              padding: "30px",
              borderRadius: "8px",
              textAlign: "center",
              boxShadow: "0 4px 6px rgba(0,0,0,0.2)",
              minWidth: "300px"
            }}
          >
            <h3>Delete Project?</h3>
            <p style={{ color: "#333" }}>Are you sure you want to delete this project? This action cannot be undone.</p>
            <div style={{ marginTop: "20px", display: "flex", gap: "10px", justifyContent: "center" }}>
              <button 
                onClick={() => deleteProject(deleteConfirm)}
                disabled={deleting === deleteConfirm}
                style={{ padding: "10px 20px", backgroundColor: "#f44336", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
              >
                {deleting === deleteConfirm ? "Deleting..." : "Delete"}
              </button>
              <button 
                onClick={() => setDeleteConfirm(null)}
                style={{ padding: "10px 20px", backgroundColor: "#ccc", border: "none", borderRadius: "4px", cursor: "pointer" }}
              >
                Cancel
              </button>
            </div>
          </div>
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

      <h1 className="dashboard-title">My Projects</h1>

      <div className="projects-grid">
        {/* New Project Card */}
        <div className="project-card" onClick={() => {
          navigate("/createproject");
          showNotification("Creating new project...", "info");
        }}>
          <h3>New Project</h3>
          <p>Upload a 2D plan and start your project</p>
          <button>Create</button>
        </div>

        {/* Existing Projects */}
        {projects.map((proj) => (
          <div key={proj.id} className="project-card">
            {editingProject === proj.id ? (
              <>
                <input 
                  type="text" 
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  style={{ width: "90%", padding: "8px", marginBottom: "10px", fontSize: "16px" }}
                />
                <input 
                  type="text" 
                  value={editLocation}
                  onChange={(e) => setEditLocation(e.target.value)}
                  style={{ width: "90%", padding: "8px", marginBottom: "10px", fontSize: "14px" }}
                />
                <div style={{ marginBottom: "10px" }}>
                  <button 
                    onClick={() => updateProject(proj.id)}
                    disabled={updating}
                    style={{ marginRight: "10px", opacity: updating ? 0.5 : 1, cursor: updating ? "not-allowed" : "pointer" }}
                  >
                    {updating ? "Saving..." : "Save"}
                  </button>
                  <button onClick={cancelEditing}>Cancel</button>
                </div>
              </>
            ) : (
              <>
                <h3>{proj.name}</h3>
                <p><strong>Location:</strong> {proj.location}</p>
                <button onClick={() => startEditing(proj)} style={{ marginBottom: "10px" }}>Edit</button>
              </>
            )}

            <div className="card-buttons">
              <button onClick={() => navigate("/openplan")}>Open</button>
              <button onClick={() => navigate(`/designworkspace/${proj.id}`)}>Design</button>
              <button 
                onClick={() => setDeleteConfirm(proj.id)}
                style={{ opacity: deleting === proj.id ? 0.5 : 1, cursor: deleting === proj.id ? "not-allowed" : "pointer" }}
              >
                Delete
              </button>
              <button onClick={() => navigate(`/analysis/${proj.id}`)}>Analysis</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyProjects;
