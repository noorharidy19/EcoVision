import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

interface Project {
  id: number;
  name: string;
  location: string;
  file_path: string;
  user_id: number;
  created_at: string;
}

const ProjectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://127.0.0.1:8000/projects/${id}`);
        if (!response.ok) throw new Error('Failed to fetch project');
        const data = await response.json();
        setProject(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProject();
    }
  }, [id]);

  if (loading) return <div className="p-4">Loading...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!project) return <div className="p-4">Project not found</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">{project.name}</h1>
      <div className="bg-gray-100 p-4 rounded-lg">
        <p className="mb-2"><strong>Location:</strong> {project.location}</p>
        <p className="mb-2"><strong>File:</strong> {project.file_path}</p>
        <p className="mb-2"><strong>Created:</strong> {new Date(project.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  );
};

export default ProjectPage;
