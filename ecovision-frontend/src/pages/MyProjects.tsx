import "../styles/myprojects.css";
import { useNavigate } from "react-router-dom";

const MyProjects = () => {
  const navigate = useNavigate();

  const projects = [
    { id: 1, name: "Project 1" },
    { id: 2, name: "Project 2" },
    { id: 3, name: "Project 3" }
  ];

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">My Projects</h1>

      <div className="projects-grid">
        {/* New Project Card */}
        <div className="project-card" onClick={() => navigate("/project/new")}>
          <h3>New Project</h3>
          <p>Upload a 2D plan and start your project</p>
          <button>Create</button>
        </div>

        {/* Existing Projects */}
        {projects.map((proj) => (
          <div
            className="project-card"
            key={proj.id}
            onClick={() => navigate(`/project/${proj.id}`)}
          >
            <h3>{proj.name}</h3>
            <p>Your saved project</p>
            <div className="card-buttons">
              <button onClick={() => navigate(`/project/${proj.id}`)}>View</button>
              <button onClick={() => navigate(`/project/${proj.id}/edit`)}>Edit</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyProjects;
