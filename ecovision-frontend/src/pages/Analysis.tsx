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

interface AnalysisResults {
  [orientation: string]: {
    thermal?: number;
    visual?: number;
  };
}

const Analysis = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [floorplan, setFloorplan] = useState<Floorplan | null>(null);
  const [mode, setMode] = useState<"edit" | "sustainability" | "visual" | "thermal">("edit");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);

  useEffect(() => {
    if (id && id !== "new" && id !== "undefined") {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      console.log("Fetching project:", id);
      setLoading(true);
      setError(null);

      fetch(`http://127.0.0.1:8000/projects/${id}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      })
        .then(async res => {
          console.log("Response status:", res.status);
          if (!res.ok) {
            const text = await res.text();
            console.error("Error response:", text);
            throw new Error(`HTTP ${res.status}: ${text}`);
          }
          return res.json();
        })
        .then(data => {
          console.log("Project loaded:", data);
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
            const text = await res.text();
            console.error("Error fetching floorplan:", text);
            return null;
          }
          return res.json();
        })
        .then(data => {
          if (data) {
            console.log("Floorplan loaded:", data);
            setFloorplan(data);
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching data:", err);
          setError(err.message);
          setLoading(false);
        });
    } else {
      setLoading(false);
      setError(id === "undefined" ? "Invalid project ID in URL" : null);
    }
  }, [id]);

  if (id === "new") {
    return <p>Create a new project here...</p>;
  }

  const runAnalysis = async (type: "thermal" | "visual") => {
    if (!id) return;
    
    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/analysis/project/${id}/comfort?analysis_type=${type}`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const data = await response.json();
      console.log("Analysis results:", data);
      setAnalysisResults(data.results);
      setMode(type);
    } catch (err) {
      console.error("Error running analysis:", err);
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="workspace-layout">
      <div className="left-panel" style={{ display: "grid", gridTemplateColumns: "0.8fr 1.5fr", gap: "20px" }}>
        <div>
          {loading ? (
            <p>Loading project...</p>
          ) : error ? (
            <div style={{ color: "red", padding: "20px" }}>
              <p><strong>Error:</strong> {error}</p>
              <p>Check browser console for details</p>
            </div>
          ) : project ? (
            <div className="project-info-section">
              <div className="project-info-card">
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
             
            </div>
          ) : (
            <p>No project found</p>
          )}
        </div>

        <div className="design-area">
          <div className="workspace-toolbar">
            <button 
              onClick={() => runAnalysis("thermal")}
              disabled={analyzing || !floorplan}
              style={{ opacity: analyzing || !floorplan ? 0.5 : 1, cursor: analyzing || !floorplan ? "not-allowed" : "pointer" }}
            >
              {analyzing ? "Analyzing..." : "Thermal Comfort"}
            </button>
            <button 
              onClick={() => runAnalysis("visual")}
              disabled={analyzing || !floorplan}
              style={{ opacity: analyzing || !floorplan ? 0.5 : 1, cursor: analyzing || !floorplan ? "not-allowed" : "pointer" }}
            >
              {analyzing ? "Analyzing..." : "Visual Comfort"}
            </button>
            <button onClick={() => setMode("sustainability")}>Sustainability</button>
          </div>

          <div className="design-preview">
            {error && <div style={{ color: "red", padding: "10px" }}>❌ {error}</div>}
            
            {mode === "edit" && (
              <div style={{ padding: "20px" }}>
                <p>Select an analysis type to get started</p>
                {!floorplan && <p style={{ color: "orange" }}>Floorplan data not yet loaded</p>}
              </div>
            )}

            {mode === "thermal" && analysisResults && (
              <div style={{ padding: "20px" }}>
                <h4>Thermal Comfort Analysis Results</h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginTop: "15px" }}>
                  {Object.entries(analysisResults).map(([orientation, scores]: [string, any]) => (
                    <div key={orientation} style={{ 
                      border: "1px solid #ddd", 
                      padding: "15px", 
                      borderRadius: "8px",
                      backgroundColor: "#f9f9f9"
                    }}>
                      <h5>{orientation}</h5>
                      <p><strong>Thermal Score:</strong> {(scores.thermal).toFixed(2)}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {mode === "visual" && analysisResults && (
              <div style={{ padding: "20px" }}>
                <h4>Visual Comfort Analysis Results</h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginTop: "15px" }}>
                  {Object.entries(analysisResults).map(([orientation, scores]: [string, any]) => (
                    <div key={orientation} style={{ 
                      border: "1px solid #ddd", 
                      padding: "15px", 
                      borderRadius: "8px",
                      backgroundColor: "#f9f9f9"
                    }}>
                      <h5>{orientation}</h5>
                      <p><strong>Visual Score:</strong> {(scores.visual).toFixed(2)}%</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;
