import { useEffect, useState } from "react";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
  created_at: string;
}

const ProjectsList = () => {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/projects")
      .then((res) => res.json())
      .then((data) => setProjects(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>My Projects</h2>

      {projects.map((project) => (
        <div key={project.id} style={{ border: "1px solid #ccc", marginBottom: "10px", padding: "10px" }}>
          <p><strong>Name:</strong> {project.name}</p>
          <p><strong>Location:</strong> {project.location}</p>
          <p><strong>File:</strong> {project.file_path}</p>
        </div>
      ))}
    </div>
  );
};

export default ProjectsList;
