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

const DesignWorkspace = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);

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
      .then(data => setProject(data))
      .catch(err => console.error(err));
  }
}, [id]);


  if (id === "new") {
    return <p>Create a new project here...</p>;
  }

  return (
    <div className="workspace-layout">
      <div className="left-panel">
        {project ? (
          <div className="project-info-section">
            <div className="project-info-card">
              <h3>{project.name}</h3>
              <p><strong>ID:</strong> {project.id}</p>
              <p><strong>Location:</strong> {project.location}</p>
              <p><strong>File:</strong> {project.file_path}</p>
            </div>

            <div>
              <input type="text" placeholder="Edit Project (optional)" className="edit-input-btn" />
              <button className="edit-project-btn">Confirm</button>
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
