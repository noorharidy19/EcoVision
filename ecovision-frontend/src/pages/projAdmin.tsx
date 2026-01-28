import { useEffect, useState } from "react";
import "../styles/adminService.css";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
  created_at: string;
  user_id: number;
}

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
  const token = localStorage.getItem("token"); // get token from login
  if (!token) {
    console.error("No token found");
    return;
  }

  fetch("http://127.0.0.1:8000/projects/", {
    headers: {
      "Authorization": `Bearer ${token}`, // send token
    },
  })
    .then(res => {
      if (!res.ok) throw new Error("Failed to fetch projects: " + res.status);
      return res.json();
    })
    .then(data => {
      console.log("Projects from backend:", data); // debug
      setProjects(data);
    })
    .catch(err => console.error("Error fetching projects:", err));
}, []);


  return (
    <div className="page">
      <h1 className="title">All Projects (Admin View)</h1>

      <div className="card large">
        {projects.length === 0 ? (
          <p>No projects found.</p>
        ) : (
          <table border={1} width="100%">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Location</th>
                <th>File</th>
                <th>Created At</th>
                <th>User ID</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>{project.id}</td>
                  <td>{project.name}</td>
                  <td>{project.location}</td>
                  <td>{project.file_path}</td>
                  <td>{new Date(project.created_at).toLocaleString()}</td>
                  <td>{project.user_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
