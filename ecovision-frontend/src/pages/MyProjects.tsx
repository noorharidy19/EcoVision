import "../styles/myprojects.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
}

const MyProjects = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
  fetch("http://127.0.0.1:8000/projects/", {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`
    }
  })
    .then(res => {
      if (!res.ok) throw new Error("Unauthorized");
      return res.json();
    })
    .then(data => setProjects(data))
    .catch(err => console.error("Error fetching projects:", err));
}, []);


  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">My Projects</h1>

      <div className="projects-grid">
        {/* New Project Card */}
        <div className="project-card" onClick={() => navigate("/createproject")}>
          <h3>New Project</h3>
          <p>Upload a 2D plan and start your project</p>
          <button>Create</button>
        </div>

        {/* Existing Projects */}
        {projects.map((proj) => (
          <div key={proj.id} className="project-card">
            <h3>{proj.name}</h3>
            <p>{proj.location}</p>
            <p>{proj.file_path}</p>
            <div className="card-buttons">
              <button   onClick={() => navigate("/openplan")}>Open</button>
              <button  onClick={() => navigate(`/designworkspace/${proj.id}`)}>Edit</button>
              <button>Delete</button>
              <button onClick={() => navigate("/analysis")}>Analysis</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyProjects;
