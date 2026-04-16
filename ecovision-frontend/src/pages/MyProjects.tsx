import "../styles/myprojects.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
  role: "OWNER";
  user_id: number;
}

interface OtherProject {
  id: number;
  name: string;
  location: string;
  owner: string;
  user_id: number;
  access_status?: "PENDING" | "ACCEPTED" | "DECLINED" | null;
}

interface ApprovedProject {
  id: number;
  name: string;
  location: string;
  owner: string;
  user_id: number;
  role: string;
}

interface Collaborator {
  id: number;
  requester_id: number;
  requester_name: string;
  project_id: number;
  project_name: string;
  status: "PENDING" | "ACCEPTED" | "DECLINED";
  created_at: string;
}

interface Notification {
  message: string;
  type: "success" | "error" | "info";
}

const MyProjects = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [projects, setProjects] = useState<Project[]>([]);
  const [otherProjects, setOtherProjects] = useState<OtherProject[]>([]);
  const [approvedProjects, setApprovedProjects] = useState<ApprovedProject[]>([]);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);

  const [notification, setNotification] = useState<Notification | null>(null);

  const showNotification = (
    message: string,
    type: "success" | "error" | "info" = "info"
  ) => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    // my projects
    fetch("http://127.0.0.1:8000/projects/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => setProjects(data))
      .catch((err) => console.error(err));

    // other projects
    fetch("http://127.0.0.1:8000/projects/all", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {
        // Filter out user's own projects
        const filtered = data.filter((p: OtherProject) => p.user_id !== user?.id);
        setOtherProjects(filtered);
      })
      .catch((err) => console.error(err));

    // Fetch collaborators for my projects
    if (user?.id) {
      fetch("http://127.0.0.1:8000/projects/access-requests/my-approvals", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => setCollaborators(data))
        .catch((err) => console.error("Failed to fetch collaborators:", err));

      // Fetch approved projects (where user is a collaborator)
      fetch("http://127.0.0.1:8000/projects/collaborations/my-approved", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => res.json())
        .then((data) => setApprovedProjects(data))
        .catch((err) => console.error("Failed to fetch approved projects:", err));
    }
  }, [user?.id]);

  const requestAccess = async (projectId: number) => {
    const token = localStorage.getItem("token");

    const res = await fetch(
      `http://127.0.0.1:8000/projects/${projectId}/request-access`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (res.ok) {
      setOtherProjects((prev) =>
        prev.map((p) =>
          p.id === projectId ? { ...p, access_status: "PENDING" } : p
        )
      );

      showNotification("Access request sent", "success");
    } else {
      showNotification("Failed to send request", "error");
    }
  };

  return (
    <div className="dashboard-container">
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      <h1 className="dashboard-title">My Projects</h1>

      <div className="projects-grid">
        <div
          className="project-card"
          onClick={() => navigate("/createproject")}
        >
          <h3>New Project</h3>
          <p>Upload a 2D plan and start your project</p>
          <button>Create</button>
        </div>

        {projects.map((proj) => (
          <div key={proj.id} className="project-card">
            <h3>{proj.name}</h3>

            <p>
              <strong>Location:</strong> {proj.location}
            </p>

            <p>
              <strong>Role:</strong> {proj.role}
            </p>

            <div className="card-buttons">
              <button onClick={() => navigate(`/designworkspace/${proj.id}`)}>
                Open
              </button>

              <button onClick={() => navigate(`/analysis/${proj.id}`)}>
                Analysis
              </button>
              <button onClick={() => navigate(`/sustainability/${proj.id}`)}>
                Sustainability
              </button>
              <button onClick={() => navigate(`/project/${proj.id}/requests`)}>
                Requests
              </button>
            </div>
          </div>
        ))}
      </div>

      {collaborators.length > 0 && (
        <>
          <h1 className="dashboard-title" style={{ marginTop: "40px" }}>
            Collaborators & Access Requests
          </h1>

          <div className="collaborators-section">
            <table className="collaborators-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Collaborator</th>
                  <th>Status</th>
                  <th>Requested Date</th>
                </tr>
              </thead>
              <tbody>
                {collaborators.map((collab) => (
                  <tr key={collab.id} className={`status-${collab.status.toLowerCase()}`}>
                    <td className="project-name">{collab.project_name}</td>
                    <td className="collaborator-name">{collab.requester_name}</td>
                    <td>
                      <span className={`status-badge ${collab.status.toLowerCase()}`}>
                        {collab.status}
                      </span>
                    </td>
                    <td className="date">
                      {new Date(collab.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {approvedProjects.length > 0 && (
        <>
          <h1 className="dashboard-title" style={{ marginTop: "40px" }}>
            Approved Collaborations
          </h1>

          <div className="projects-grid">
            {approvedProjects.map((proj) => (
              <div key={proj.id} className="project-card">
                <h3>{proj.name}</h3>

                <p>
                  <strong>Location:</strong> {proj.location}
                  <br />
                  <strong>Owner:</strong> {proj.owner}
                  <br />
                  <strong>Role:</strong> {proj.role}
                </p>

                <div className="card-buttons">
                  <button onClick={() => navigate(`/designworkspace/${proj.id}`)}>
                    Open
                  </button>

                  <button onClick={() => navigate(`/analysis/${proj.id}`)}>
                    Analysis
                  </button>
                  <button onClick={() => navigate(`/sustainability/${proj.id}`)}>
                    Sustainability
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <h1 className="dashboard-title" style={{ marginTop: "40px" }}>
        Other Projects
      </h1>

      <div className="projects-grid">
        {otherProjects.filter(
          (proj) => !approvedProjects.some((approved) => approved.id === proj.id)
        ).length === 0 ? (
          <div className="no-projects">
            <p>No other projects available</p>
          </div>
        ) : (
          otherProjects
            .filter(
              (proj) => !approvedProjects.some((approved) => approved.id === proj.id)
            )
            .map((proj) => (
            <div key={proj.id} className="project-card">
              <h3>{proj.name}</h3>

              <p>
                <strong>Location:</strong> {proj.location}
                <br />
                <strong>Owner:</strong> {proj.owner}
              </p>

              {proj.access_status === "PENDING" ? (
                <button disabled>Pending</button>
              ) : proj.access_status === "ACCEPTED" ? (
                <button onClick={() => navigate(`/designworkspace/${proj.id}`)}>
                  Open
                </button>
              ) : (
                <button onClick={() => requestAccess(proj.id)}>
                  Request Access
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default MyProjects;