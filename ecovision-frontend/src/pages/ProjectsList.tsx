import { useEffect, useState } from "react";
import { fetchProjects } from "../services/projectService";

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
}

const ProjectsList = () => {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(console.error);
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h1>Your Projects</h1>

      {projects.map((project) => (
        <div
          key={project.id}
          style={{
            padding: 20,
            marginBottom: 12,
            borderRadius: 12,
            background: "#f1fdf8",
            cursor: "pointer",
          }}
        >
          <h3>{project.name}</h3>
          <p>{project.location}</p>
        </div>
      ))}
    </div>
  );
};

export default ProjectsList;
