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

interface Material {
  id: string;
  name: string;
  category: string;
  roughness: string;
  thickness_m: number;
  conductivity_W_mK: number;
  density_kg_m3: number;
  specific_heat_J_kgK: number;
  carbon_kgCO2_per_kg: number;
  r_value_m2K_W: number;
  carbon_kgCO2_per_m2: number;
}

interface WindowType {
  id: string;
  name: string;
  u_value: number;
  shgc: number;
  carbon_kgCO2_per_m2: number;
}

interface MaterialsMapping {
  wallBaseMaterials: Material[];
  roofBaseMaterials: Material[];
  floorBaseMaterials: Material[];
  insulationMaterials: Material[];
  windowTypes: WindowType[];
}

interface RoomAnalysis {
  room: string;
  area_m2: number;
  your_selection: {
    materials: Record<string, { name: string; carbon_kg: number }>;
    total_carbon_kg: number;
  };
  recommended_solution: {
    materials: Record<string, { name: string; carbon_kg: number }>;
    total_carbon_kg: number;
  };
  carbon_savings: {
    saved_kg: number;
    reduction_percent: number;
  };
}

interface MLAnalysisResult {
  summary: {
    your_total_carbon: number;
    optimized_total_carbon: number;
    total_savings: number;
    reduction_percent: number;
  };
  rooms: RoomAnalysis[];
}

type RecommendationMode = "overview" | "thermal" | "visual" | "sustainability" | "material";

const Sustainability = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [floorplan, setFloorplan] = useState<Floorplan | null>(null);
  const [mode, setMode] = useState<RecommendationMode>("overview");
  const [showEditor, setShowEditor] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>("dxf");
  const [exporting, setExporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Recommendation states
  const [visualLoading, setVisualLoading] = useState(false);
  const [sustainabilityLoading, setSustainabilityLoading] = useState(false);
  
  // ML Model analysis states
  const [mlSustainabilityScore, setMlSustainabilityScore] = useState<any>(null);
  const [mlAnalysisLoading, setMlAnalysisLoading] = useState(false);
  const [roomByRoomAnalysis, setRoomByRoomAnalysis] = useState<MLAnalysisResult | null>(null);
  
  // Material mapping states
  const [materialMapping, setMaterialMapping] = useState<MaterialsMapping | null>(null);
  const [thermalScore, setThermalScore] = useState<any>(null);
  const [thermalScoreLoading, setThermalScoreLoading] = useState(false);
  
  // Building element selections
  const [wallBase, setWallBase] = useState<Material | null>(null);
  const [wallInsulation, setWallInsulation] = useState<Material | null>(null);
  
  const [roofBase, setRoofBase] = useState<Material | null>(null);
  const [roofInsulation, setRoofInsulation] = useState<Material | null>(null);
  
  const [floorBase, setFloorBase] = useState<Material | null>(null);
  const [floorInsulation, setFloorInsulation] = useState<Material | null>(null);
  
  const [windowType, setWindowType] = useState<WindowType | null>(null);

  const [visualScore, setVisualScore] = useState<any>(null);

  // Load project and floorplan data
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

  // Load materials data from JSON
  useEffect(() => {
    fetch("/materials-mapping.json")
      .then(res => res.json())
      .then((data: MaterialsMapping) => {
        console.log("Materials mapping loaded:", data);
        setMaterialMapping(data);
      })
      .catch(err => {
        console.error("Error loading materials:", err);
        setError("Failed to load materials database");
      });
  }, []);

  if (id === "new") {
    return <p>Create a new project here...</p>;
  }

  // Generate Thermal Comfort recommendations
  const generateThermalRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setError(null);
    setMode("thermal");
    // Thermal analysis can be triggered from the thermal mode view
  };

  // Generate Visual Comfort recommendations
  const generateVisualRecommendations = async () => {
  if (!floorplan) {
    setError("No floorplan available");
    return;
  }

  setVisualLoading(true);
  setError(null);

  try {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("Not authenticated");

    // Use the floorplan's json_data if available, otherwise fetch it
    const floorplanData = floorplan.json_data || {};

    const response = await fetch("http://127.0.0.1:8000/analysis/visual", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        floorplan_id: floorplan.id,
        floorplan_json: floorplanData
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Visual analysis failed: ${errorText}`);
    }

    const data = await response.json();
    setVisualScore(data);
    setMode("visual");
  } catch (err) {
    setError(err instanceof Error ? err.message : "Visual analysis failed");
  } finally {
    setVisualLoading(false);
  }
}; 

  // Generate Sustainability recommendations
  const generateSustainabilityRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setSustainabilityLoading(true);
    setError(null);

    try {
      setMode("sustainability");
    } finally {
      setSustainabilityLoading(false);
    }
  };

  // Generate Material Selection recommendations
  const generateMaterialRecommendations = async () => {
    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setMode("material");
  };

  const calculateTotalCarbonFromSelection = () => {
    let total = 0;
    if (wallBase) total += wallBase.carbon_kgCO2_per_m2;
    if (wallInsulation) total += wallInsulation.carbon_kgCO2_per_m2;
    if (roofBase) total += roofBase.carbon_kgCO2_per_m2;
    if (roofInsulation) total += roofInsulation.carbon_kgCO2_per_m2;
    if (floorBase) total += floorBase.carbon_kgCO2_per_m2;
    if (floorInsulation) total += floorInsulation.carbon_kgCO2_per_m2;
    if (windowType) total += windowType.carbon_kgCO2_per_m2;
    return total;
  };

  // Calculate thermal comfort score from material selection
  const calculateThermalScore = async () => {
    if (!wallBase || !roofBase || !floorBase || !windowType) {
      setError("Please complete all material selections");
      return;
    }

    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setThermalScoreLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Not authenticated");
        return;
      }

      const materialSelection = {
        wall_base: wallBase.name,
        wall_insulation: wallInsulation?.name || "None",
        roof_base: roofBase.name,
        roof_insulation: roofInsulation?.name || "None",
        floor_base: floorBase.name,
        floor_insulation: floorInsulation?.name || "None",
        window_type: windowType.name
      };

      const response = await fetch("http://127.0.0.1:8000/analysis/thermal", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id,
          materials: materialSelection
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Thermal analysis failed: ${errorText}`);
      }

      const thermalData = await response.json();
      console.log("Thermal score received:", thermalData);
      
      // Calculate carbon footprint from materials
      const carbon = {
        wall: {
          base: wallBase?.carbon_kgCO2_per_m2 || 0,
          insulation: wallInsulation?.carbon_kgCO2_per_m2 || 0,
          total: (wallBase?.carbon_kgCO2_per_m2 || 0) + (wallInsulation?.carbon_kgCO2_per_m2 || 0)
        },
        roof: {
          base: roofBase?.carbon_kgCO2_per_m2 || 0,
          insulation: roofInsulation?.carbon_kgCO2_per_m2 || 0,
          total: (roofBase?.carbon_kgCO2_per_m2 || 0) + (roofInsulation?.carbon_kgCO2_per_m2 || 0)
        },
        floor: {
          base: floorBase?.carbon_kgCO2_per_m2 || 0,
          insulation: floorInsulation?.carbon_kgCO2_per_m2 || 0,
          total: (floorBase?.carbon_kgCO2_per_m2 || 0) + (floorInsulation?.carbon_kgCO2_per_m2 || 0)
        },
        window: windowType?.carbon_kgCO2_per_m2 || 0
      };
      
      const totalCarbon = carbon.wall.total + carbon.roof.total + carbon.floor.total + carbon.window;
      const carbonData = {
        breakdown: carbon,
        total: totalCarbon
      };
      
      console.log("Carbon footprint calculated:", carbonData);
      
      setThermalScore(thermalData);
      setMode("thermal");
    } catch (err) {
      console.error("Error calculating thermal score:", err);
      setError(err instanceof Error ? err.message : "Failed to calculate thermal score");
    } finally {
      setThermalScoreLoading(false);
    }
  };

  // Analyze sustainability using ML model
  const analyzeWithMLModel = async () => {
    if (!wallBase || !roofBase || !floorBase || !windowType) {
      setError("Please complete all material selections");
      return;
    }

    if (!floorplan) {
      setError("No floorplan available");
      return;
    }

    setMlAnalysisLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Not authenticated");
        return;
      }

      // Get rooms from floorplan JSON data
      const rooms = floorplan.json_data?.rooms || [];

      // Build material ID map - need to match material names to IDs
      const materialIdMap: { [key: string]: string } = {
        [wallBase.name]: wallBase.id,
        [roofBase.name]: roofBase.id,
        [floorBase.name]: floorBase.id,
        [windowType.name]: windowType.id,
      };

      // Add optional materials
      if (wallInsulation) materialIdMap[wallInsulation.name] = wallInsulation.id;
      if (roofInsulation) materialIdMap[roofInsulation.name] = roofInsulation.id;
      if (floorInsulation) materialIdMap[floorInsulation.name] = floorInsulation.id;

      const materials = {
        wall_base: wallBase.id,
        wall_insulation: wallInsulation?.id,
        roof_base: roofBase.id,
        roof_insulation: roofInsulation?.id,
        floor_base: floorBase.id,
        floor_insulation: floorInsulation?.id,
        window: windowType.id
      };

      const response = await fetch("http://127.0.0.1:8000/analysis/sustainability", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          floorplan_id: floorplan.id,
          materials: materials,
          rooms: rooms
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Sustainability analysis failed: ${errorText}`);
      }

      const sustainabilityData = await response.json();
      console.log("ML Sustainability analysis received:", sustainabilityData);
      setMlSustainabilityScore(sustainabilityData);
      
      // Extract room-by-room analysis if available
      if (sustainabilityData && sustainabilityData.summary) {
        setRoomByRoomAnalysis(sustainabilityData);
      }
    } catch (err) {
      console.error("Error in ML sustainability analysis:", err);
      setError(err instanceof Error ? err.message : "Failed to analyze sustainability");
    } finally {
      setMlAnalysisLoading(false);
    }
  };

  // Export file
  const exportFile = async (format: string) => {
    if (!floorplan) {
      setError("No floorplan available to export");
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Not authenticated");
      return;
    }

    setExporting(true);
    setError(null);

    try {
      const res = await fetch(`http://127.0.0.1:8000/floorplans/${floorplan.id}/export?format=${format}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Export failed: ${text}`);
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const ext = format === "png" ? "png" : format;
      a.href = url;
      a.download = `${project?.name || "floorplan"}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  // Helper function to render recommendation data
  const renderRecommendationContent = (data: any, title: string, icon: string) => {
    return (
      <div style={{ padding: "20px" }}>
        <h4>{icon} {title}</h4>
        
        {data ? (
          <div>
            {data.formatted && (
              <div style={{ backgroundColor: "#f0f8f0", padding: "15px", borderRadius: "8px", marginBottom: "20px", whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "14px" }}>
                {data.formatted}
              </div>
            )}
            
            {data.recommendations && data.recommendations.length > 0 && (
              <div style={{ marginTop: "20px" }}>
                <h5>Detailed Recommendations ({data.total || data.recommendations.length})</h5>
                <div style={{ display: "grid", gap: "15px" }}>
                  {data.recommendations.map((rec: any, idx: number) => (
                    <div key={idx} style={{ 
                      border: "1px solid #ddd", 
                      padding: "15px", 
                      borderRadius: "8px",
                      backgroundColor: "#fafafa"
                    }}>
                      <h6 style={{ marginTop: 0 }}>{rec.room} - {rec.category}</h6>
                      {rec.impact && <p><strong>Impact:</strong> {rec.impact}</p>}
                      {rec.issue && <p><strong>Issue:</strong> {rec.issue}</p>}
                      {rec.recommendation && <p><strong>Recommendation:</strong> {rec.recommendation}</p>}
                      {rec.priority && <p><strong>Priority:</strong> {rec.priority}</p>}
                      {rec.triggers && rec.triggers.length > 0 && (
                        <p><strong>Affects:</strong> {rec.triggers.join(", ")}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button onClick={() => setShowEditor(true)} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Edit</button>
              <button onClick={() => setMode('overview')} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Back</button>
            </div>
          </div>
        ) : (
          <div>
            <p>Click the button to generate {title.toLowerCase()}.</p>
            <button onClick={() => setMode('overview')} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer" }}>Back</button>
          </div>
        )}
      </div>
    );
  };

  // Render thermal analysis UI
  const renderThermalContent = () => {
    const getThermalColor = (score: number) => {
      if (score >= 70) return "#10b981"; // Green
      if (score >= 50) return "#f59e0b"; // Orange
      return "#ef4444"; // Red
    };

    return (
      <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
        <h4>🌡️ Thermal Comfort Analysis</h4>

        {thermalScore ? (
          <div>
            <div style={{
              backgroundColor: "#f0f8f0",
              padding: "25px",
              borderRadius: "12px",
              border: `3px solid ${getThermalColor(thermalScore.comfort_score)}`,
              marginBottom: "20px",
              textAlign: "center"
            }}>
              <div style={{
                fontSize: "48px",
                fontWeight: "bold",
                color: getThermalColor(thermalScore.comfort_score),
                marginBottom: "15px"
              }}>
                {thermalScore.comfort_score.toFixed(1)}%
              </div>
              <div style={{ fontSize: "18px", fontWeight: "600", color: "#065f46", marginBottom: "10px" }}>
                Comfort Class: <span style={{ color: getThermalColor(thermalScore.comfort_score) }}>{thermalScore.comfort_class}</span>
              </div>
              <p style={{ margin: "8px 0", color: "#666", fontSize: "14px" }}>
                {thermalScore.comfort_class === "Cool" && "Indoor conditions are cooler than optimal. Consider reducing insulation or increasing solar gains."}
                {thermalScore.comfort_class === "Neutral" && "Indoor conditions are within the comfort zone. Excellent thermal performance."}
                {thermalScore.comfort_class === "Warm" && "Indoor conditions are warmer than optimal. Consider increasing insulation or reducing solar gains."}
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginBottom: "20px" }}>
              <div style={{
                backgroundColor: "#e5f5f0",
                padding: "15px",
                borderRadius: "8px",
                border: "1px solid #a7f3d0"
              }}>
                <h5 style={{ marginTop: 0, color: "#065f46" }}>Comfort Metrics</h5>
                <p style={{ margin: "8px 0" }}>
                  <strong>PMV:</strong> {thermalScore.pmv}<br/>
                  <span style={{ fontSize: "12px", color: "#666" }}>
                    (Predicted Mean Vote: -3 to +3)
                  </span>
                </p>
                <p style={{ margin: "8px 0" }}>
                  <strong>PPD:</strong> {thermalScore.ppd}%<br/>
                  <span style={{ fontSize: "12px", color: "#666" }}>
                    (Predicted Percentage Dissatisfied)
                  </span>
                </p>
              </div>

              <div style={{
                backgroundColor: "#e5f5f0",
                padding: "15px",
                borderRadius: "8px",
                border: "1px solid #a7f3d0"
              }}>
                <h5 style={{ marginTop: 0, color: "#065f46" }}>Temperature Estimates</h5>
                <p style={{ margin: "8px 0" }}>
                  <strong>Dry Bulb:</strong> {thermalScore.tdb_est}°C<br/>
                  <span style={{ fontSize: "12px", color: "#666" }}>
                    (Indoor air temperature)
                  </span>
                </p>
                <p style={{ margin: "8px 0" }}>
                  <strong>Radiant:</strong> {thermalScore.tr_est}°C<br/>
                  <span style={{ fontSize: "12px", color: "#666" }}>
                    (Mean radiant temperature)
                  </span>
                </p>
              </div>
            </div>

            <div style={{
              backgroundColor: "#ecfdf5",
              padding: "15px",
              borderRadius: "8px",
              border: "2px solid #a7f3d0",
              marginBottom: "20px"
            }}>
              <h5 style={{ marginTop: 0, color: "#065f46" }}>🏗️ Material U-Values</h5>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px" }}>
                <div>
                  <p style={{ margin: "5px 0" }}>
                    <strong>Wall:</strong> {thermalScore.u_wall} W/m²K
                  </p>
                  <p style={{ margin: "5px 0" }}>
                    <strong>Roof:</strong> {thermalScore.u_roof} W/m²K
                  </p>
                </div>
                <div>
                  <p style={{ margin: "5px 0" }}>
                    <strong>Floor:</strong> {thermalScore.u_floor} W/m²K
                  </p>
                  <p style={{ margin: "5px 0" }}>
                    <strong>Window:</strong> {thermalScore.u_window} W/m²K
                  </p>
                </div>
              </div>
              <p style={{ fontSize: "12px", color: "#666", marginTop: "10px", marginBottom: 0 }}>
                <strong>SHGC:</strong> {thermalScore.shgc} (Solar Heat Gain Coefficient)
              </p>
            </div>


            <div style={{ display: "flex", gap: "10px" }}>
              <button 
                onClick={() => {
                  setThermalScore(null);
                  setMode('overview');
                }} 
                style={{ 
                  padding: "10px 18px", 
                  borderRadius: "12px", 
                  border: "none", 
                  background: "#d1fae5", 
                  color: "#065f46", 
                  fontWeight: "600", 
                  cursor: "pointer" 
                }}
              >
                ← Back
              </button>
              <button 
                onClick={() => setMode('material')} 
                style={{ 
                  padding: "10px 18px", 
                  borderRadius: "12px", 
                  border: "none", 
                  background: "#FFB84D", 
                  color: "#000", 
                  fontWeight: "600", 
                  cursor: "pointer" 
                }}
              >
                🏗️ Modify Materials
              </button>
            </div>
          </div>
        ) : (
          <div style={{
            backgroundColor: "#f0f8f0",
            padding: "25px",
            borderRadius: "12px",
            border: "1px solid #d1fae5",
            textAlign: "center"
          }}>
            <h5 style={{ marginTop: 0, color: "#065f46" }}>Select Materials & Calculate</h5>
            <p style={{ color: "#666", marginBottom: "20px" }}>
              Go to the Material Selection mode to choose building materials. Once you've selected materials, thermal comfort will be automatically calculated.
            </p>
            <button 
              onClick={() => setMode('material')} 
              style={{ 
                padding: "12px 24px", 
                borderRadius: "12px", 
                border: "none", 
                background: "#065f46", 
                color: "#fff", 
                fontWeight: "600", 
                cursor: "pointer",
                fontSize: "16px"
              }}
            >
              🏗️ Go to Material Selection
            </button>
            <button 
              onClick={() => setMode('overview')} 
              style={{ 
                marginLeft: "10px",
                padding: "12px 24px", 
                borderRadius: "12px", 
                border: "none", 
                background: "#d1fae5", 
                color: "#065f46", 
                fontWeight: "600", 
                cursor: "pointer",
                fontSize: "16px"
              }}
            >
              ← Back
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderVisualContent = () => {
  const getVisualColor = (score: number) => {
    if (score >= 67) return "#4ECDC4";
    if (score >= 34) return "#f59e0b";
    return "#ef4444";
  };

  if (!visualScore) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <p>Click "✨ Visual Comfort" to run the analysis.</p>
        <button onClick={() => setMode("overview")}
          style={{ padding: "10px 18px", borderRadius: "12px",
            border: "none", background: "#d1fae5",
            color: "#065f46", fontWeight: "600", cursor: "pointer" }}>
          ← Back
        </button>
      </div>
    );
  }

  const pct = visualScore.comfort_percentage;
  const cls = visualScore.comfort_class;

  return (
    <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
      <h4>✨ Visual Comfort Analysis</h4>

      {/* ── MAIN SCORE ── */}
      <div style={{
        backgroundColor: "#f0fbfa", padding: "25px", borderRadius: "12px",
        border: `3px solid ${getVisualColor(pct)}`,
        marginBottom: "20px", textAlign: "center"
      }}>
        <div style={{
          fontSize: "48px", fontWeight: "bold",
          color: getVisualColor(pct), marginBottom: "10px"
        }}>
          {pct.toFixed(1)}%
        </div>
        <div style={{ fontSize: "18px", fontWeight: "600",
          color: "#065f46", marginBottom: "8px" }}>
          Comfort Class: <span style={{ color: getVisualColor(pct) }}>{cls}</span>
        </div>
        <p style={{ margin: 0, color: "#666", fontSize: "14px" }}>
          {visualScore.analysis?.[0]}
        </p>
      </div>

      {/* ── METRICS ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr",
        gap: "15px", marginBottom: "20px" }}>
        {Object.values(visualScore.metrics as Record<string, any>).map(
          (m: any, i: number) => (
          <div key={i} style={{
            backgroundColor: "#e5f5f0", padding: "15px",
            borderRadius: "8px", border: "1px solid #a7f3d0"
          }}>
            <h5 style={{ marginTop: 0, color: "#065f46", fontSize: "13px" }}>
              {m.label}
            </h5>
            <p style={{ margin: "5px 0", fontSize: "18px", fontWeight: "bold" }}>
              {typeof m.value === "number" ? m.value.toFixed(1) : m.value}
              {m.unit ? ` ${m.unit}` : ""}
            </p>
            <p style={{ margin: "3px 0", fontSize: "11px", color: "#666" }}>
              Target: {m.target}
            </p>
            <p style={{ margin: "3px 0", fontSize: "12px",
              color: m.status.includes("Optimal") || 
                     m.status.includes("Imperceptible") ||
                     m.status.includes("Comfortable") ||
                     m.status.includes("Excellent") ? "#065f46" : "#b45309"
            }}>
              {m.status}
            </p>
          </div>
        ))}
      </div>

      {/* ── GEOMETRY ── */}
      <div style={{
        backgroundColor: "#ecfdf5", padding: "15px", borderRadius: "8px",
        border: "2px solid #a7f3d0", marginBottom: "20px"
      }}>
        <h5 style={{ marginTop: 0, color: "#065f46" }}>🏠 Floor Plan Geometry</h5>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: "8px", fontSize: "13px" }}>
          <p style={{ margin: "4px 0" }}>
            <strong>Floor Area:</strong> {visualScore.geometry.total_area_m2} m²
          </p>
          <p style={{ margin: "4px 0" }}>
            <strong>Window Area:</strong> {visualScore.geometry.total_window_area_m2} m²
          </p>
          <p style={{ margin: "4px 0" }}>
            <strong>WWR:</strong> {visualScore.geometry.wwr_percent}%
          </p>
          <p style={{ margin: "4px 0" }}>
            <strong>Windows / Rooms:</strong> {visualScore.geometry.num_windows} / {visualScore.geometry.num_rooms}
          </p>
          <p style={{ margin: "4px 0" }}>
            <strong>Avg Window Size:</strong> {visualScore.geometry.avg_window_area_m2} m²
          </p>
          <p style={{ margin: "4px 0" }}>
            <strong>Windows per Room:</strong> {visualScore.geometry.windows_per_room}
          </p>
        </div>
      </div>

      {/* ── ANALYSIS REPORT ── */}
      <div style={{
        backgroundColor: "#f8fafc", padding: "15px", borderRadius: "8px",
        border: "1px solid #cbd5e1", marginBottom: "20px"
      }}>
        <h5 style={{ marginTop: 0, color: "#1e293b" }}>📋 Analysis Report</h5>
        {visualScore.analysis?.slice(1).map((line: string, i: number) => (
          <div key={i} style={{
            padding: "10px", marginBottom: "8px", borderRadius: "6px",
            backgroundColor: "#fff", border: "1px solid #e2e8f0",
            fontSize: "13px", color: "#374151"
          }}>
            {line}
          </div>
        ))}
      </div>

      <button onClick={() => setMode("overview")}
        style={{ padding: "10px 18px", borderRadius: "12px",
          border: "none", background: "#d1fae5",
          color: "#065f46", fontWeight: "600", cursor: "pointer" }}>
        ← Back
      </button>
    </div>
  );
};

  // Render room-by-room analysis with visual comparisons
  const renderRoomByRoomAnalysis = () => {
    if (!roomByRoomAnalysis) return null;

    const { summary, rooms } = roomByRoomAnalysis;

    return (
      <div style={{
        backgroundColor: "#f8fafc",
        padding: "20px",
        borderRadius: "12px",
        border: "2px solid #e2e8f0",
        marginTop: "20px"
      }}>
        <h5 style={{ marginTop: 0, color: "#1e293b", display: "flex", alignItems: "center", gap: "8px" }}>
          🏗️ Room-by-Room Carbon Analysis
        </h5>

        {/* Summary Stats */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "12px",
          marginBottom: "20px"
        }}>
          <div style={{
            backgroundColor: "#dcfce7",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #86efac"
          }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#166534", fontWeight: "500" }}>
              Your Total Carbon
            </p>
            <p style={{ margin: "0", fontSize: "24px", fontWeight: "bold", color: "#15803d" }}>
              {summary.your_total_carbon.toFixed(0)} kg CO₂
            </p>
          </div>

          <div style={{
            backgroundColor: "#dbeafe",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #93c5fd"
          }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#0c4a6e", fontWeight: "500" }}>
              Optimized Carbon
            </p>
            <p style={{ margin: "0", fontSize: "24px", fontWeight: "bold", color: "#0369a1" }}>
              {summary.optimized_total_carbon.toFixed(0)} kg CO₂
            </p>
          </div>

          <div style={{
            backgroundColor: "#fef3c7",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #fcd34d"
          }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#78350f", fontWeight: "500" }}>
              Total Savings
            </p>
            <p style={{ margin: "0", fontSize: "24px", fontWeight: "bold", color: "#d97706" }}>
              {summary.total_savings.toFixed(0)} kg CO₂
            </p>
          </div>

          <div style={{
            backgroundColor: "#fecdd3",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #fca5a5"
          }}>
            <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#7f1d1d", fontWeight: "500" }}>
              Reduction
            </p>
            <p style={{ margin: "0", fontSize: "24px", fontWeight: "bold", color: "#991b1b" }}>
              {summary.reduction_percent.toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Room Cards */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "15px"
        }}>
          {rooms.map((room, idx) => (
            <div key={idx} style={{
              backgroundColor: "#fff",
              padding: "15px",
              borderRadius: "8px",
              border: "1px solid #e2e8f0",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
            }}>
              <h6 style={{ margin: "0 0 12px 0", color: "#1e293b", fontSize: "16px", fontWeight: "600" }}>
                📍 {room.room}
              </h6>

              <p style={{ margin: "0 0 12px 0", fontSize: "13px", color: "#64748b" }}>
                <strong>Area:</strong> {room.area_m2} m²
              </p>

              {/* Carbon Comparison Bar */}
              <div style={{ marginBottom: "15px" }}>
                <p style={{ margin: "0 0 6px 0", fontSize: "12px", color: "#475569", fontWeight: "500" }}>
                  Carbon Comparison
                </p>

                {/* Your Selection */}
                <div style={{ marginBottom: "8px" }}>
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "4px"
                  }}>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>Your Selection</span>
                    <span style={{ fontSize: "12px", fontWeight: "600", color: "#d97706" }}>
                      {room.your_selection.total_carbon_kg.toFixed(1)} kg CO₂
                    </span>
                  </div>
                  <div style={{
                    backgroundColor: "#fed7aa",
                    height: "24px",
                    borderRadius: "4px",
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    padding: "0 6px",
                    fontSize: "11px",
                    fontWeight: "600",
                    color: "#92400e"
                  }}>
                    {(room.your_selection.total_carbon_kg > 0 ? 
                      ((room.your_selection.total_carbon_kg / Math.max(room.your_selection.total_carbon_kg, room.recommended_solution.total_carbon_kg)) * 100) 
                      : 0).toFixed(0)}%
                  </div>
                </div>

                {/* Recommended Solution */}
                <div>
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "4px"
                  }}>
                    <span style={{ fontSize: "12px", color: "#64748b" }}>Recommended</span>
                    <span style={{ fontSize: "12px", fontWeight: "600", color: "#059669" }}>
                      {room.recommended_solution.total_carbon_kg.toFixed(1)} kg CO₂
                    </span>
                  </div>
                  <div style={{
                    backgroundColor: "#a7f3d0",
                    height: "24px",
                    borderRadius: "4px",
                    width: ((room.recommended_solution.total_carbon_kg / Math.max(room.your_selection.total_carbon_kg, room.recommended_solution.total_carbon_kg)) * 100) + "%",
                    display: "flex",
                    alignItems: "center",
                    padding: "0 6px",
                    fontSize: "11px",
                    fontWeight: "600",
                    color: "#065f46"
                  }}>
                    {(room.recommended_solution.total_carbon_kg > 0 ?
                      ((room.recommended_solution.total_carbon_kg / Math.max(room.your_selection.total_carbon_kg, room.recommended_solution.total_carbon_kg)) * 100)
                      : 0).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Savings Info */}
              <div style={{
                backgroundColor: "#fef3c7",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #fcd34d"
              }}>
                <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#78350f", fontWeight: "600" }}>
                  💚 Carbon Savings
                </p>
                <p style={{ margin: "0", fontSize: "16px", fontWeight: "bold", color: "#d97706" }}>
                  {room.carbon_savings.saved_kg.toFixed(1)} kg CO₂
                </p>
                <p style={{ margin: "4px 0 0 0", fontSize: "11px", color: "#78350f" }}>
                  {room.carbon_savings.reduction_percent.toFixed(1)}% reduction
                </p>
              </div>

              {/* Material Details */}
              <div style={{ marginTop: "12px" }}>
                <p style={{ margin: "0 0 6px 0", fontSize: "12px", color: "#475569", fontWeight: "500" }}>
                  Material Changes
                </p>

                <div style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "8px",
                  fontSize: "11px"
                }}>
                  {Object.entries(room.your_selection.materials).map(([surface, material]: any) => (
                    <div key={surface}>
                      <div style={{ color: "#64748b", marginBottom: "2px" }}>
                        <strong>{surface}:</strong>
                      </div>
                      <div style={{ color: "#94a3b8", fontSize: "10px", marginBottom: "4px" }}>
                        ❌ {material.name}
                      </div>
                      <div style={{ color: "#10b981", fontSize: "10px" }}>
                        ✅ {room.recommended_solution.materials[surface]?.name || "N/A"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render sustainability content with carbon analysis
  const renderSustainabilityContent = () => {
    const hasCurrentSelection = wallBase && roofBase && floorBase && windowType;

    if (!hasCurrentSelection) {
      return (
        <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
          <h4>🌿 Sustainability & Carbon Analysis</h4>
          
          <div style={{
            backgroundColor: "#f0fdf4",
            padding: "25px",
            borderRadius: "12px",
            border: "1px solid #bbf7d0",
            textAlign: "center"
          }}>
            <h5 style={{ marginTop: 0, color: "#166534" }}>Material Selection Required</h5>
            <p style={{ color: "#666", marginBottom: "20px" }}>
              To analyze sustainability and carbon impact, please select building materials first.
            </p>
            <button 
              onClick={() => setMode('material')} 
              style={{ 
                padding: "12px 24px", 
                borderRadius: "12px", 
                border: "none", 
                background: "#10b981", 
                color: "#fff", 
                fontWeight: "600", 
                cursor: "pointer",
                fontSize: "16px"
              }}
            >
              🏗️ Go to Material Selection
            </button>
            <button 
              onClick={() => setMode('overview')} 
              style={{ 
                marginLeft: "10px",
                padding: "12px 24px", 
                borderRadius: "12px", 
                border: "none", 
                background: "#d1fae5", 
                color: "#065f46", 
                fontWeight: "600", 
                cursor: "pointer",
                fontSize: "16px"
              }}
            >
              ← Back
            </button>
          </div>
        </div>
      );
    }

    const currentCarbon = calculateTotalCarbonFromSelection();

    return (
      <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
        <h4>🌿 Sustainability & Carbon Analysis</h4>

        {/* PART 1: CURRENT MATERIALS CARBON */}
        <div style={{
          backgroundColor: "#f0fdf4",
          padding: "20px",
          borderRadius: "12px",
          border: "2px solid #86efac",
          marginBottom: "25px"
        }}>
          <h5 style={{ marginTop: 0, color: "#166534", display: "flex", alignItems: "center", gap: "8px" }}>
            📊 Part 1: Current Material Selection
          </h5>

          <div style={{
            backgroundColor: "#fff7ed",
            padding: "20px",
            borderRadius: "8px",
            marginBottom: "15px",
            textAlign: "center"
          }}>
            <div style={{
              fontSize: "40px",
              fontWeight: "bold",
              color: "#ea580c",
              marginBottom: "8px"
            }}>
              {currentCarbon.toFixed(2)} kg CO₂/m²
            </div>
            <p style={{ margin: "5px 0", fontSize: "13px", color: "#78350f" }}>
              Total Embodied Carbon from Manufacturing & Transport
            </p>
            <p style={{ margin: "0", fontSize: "11px", color: "#999", fontStyle: "italic" }}>
              This represents lifecycle emissions from material production
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "12px" }}>
            {wallBase && (
              <div style={{ backgroundColor: "#f1f5fe", padding: "12px", borderRadius: "6px", border: "1px solid #bfdbfe" }}>
                <p style={{ margin: "0 0 6px 0", fontWeight: "600", color: "#1e40af" }}>🧱 Wall Assembly</p>
                <p style={{ margin: "2px 0", fontSize: "11px" }}>
                  {wallBase.name}
                  {wallInsulation ? ` + ${wallInsulation.name}` : ""}
                </p>
                <p style={{ margin: "5px 0 0 0", color: "#ea580c", fontWeight: "600", fontSize: "13px" }}>
                  {(wallBase.carbon_kgCO2_per_m2 + (wallInsulation?.carbon_kgCO2_per_m2 || 0)).toFixed(2)} kg CO₂/m²
                </p>
              </div>
            )}

            {roofBase && (
              <div style={{ backgroundColor: "#fef3c7", padding: "12px", borderRadius: "6px", border: "1px solid #fcd34d" }}>
                <p style={{ margin: "0 0 6px 0", fontWeight: "600", color: "#92400e" }}>🏠 Roof Assembly</p>
                <p style={{ margin: "2px 0", fontSize: "11px" }}>
                  {roofBase.name}
                  {roofInsulation ? ` + ${roofInsulation.name}` : ""}
                </p>
                <p style={{ margin: "5px 0 0 0", color: "#ea580c", fontWeight: "600", fontSize: "13px" }}>
                  {(roofBase.carbon_kgCO2_per_m2 + (roofInsulation?.carbon_kgCO2_per_m2 || 0)).toFixed(2)} kg CO₂/m²
                </p>
              </div>
            )}

            {floorBase && (
              <div style={{ backgroundColor: "#dbeafe", padding: "12px", borderRadius: "6px", border: "1px solid #7dd3fc" }}>
                <p style={{ margin: "0 0 6px 0", fontWeight: "600", color: "#0c4a6e" }}>⬇️ Floor Assembly</p>
                <p style={{ margin: "2px 0", fontSize: "11px" }}>
                  {floorBase.name}
                  {floorInsulation ? ` + ${floorInsulation.name}` : ""}
                </p>
                <p style={{ margin: "5px 0 0 0", color: "#ea580c", fontWeight: "600", fontSize: "13px" }}>
                  {(floorBase.carbon_kgCO2_per_m2 + (floorInsulation?.carbon_kgCO2_per_m2 || 0)).toFixed(2)} kg CO₂/m²
                </p>
              </div>
            )}

            {windowType && (
              <div style={{ backgroundColor: "#ede9fe", padding: "12px", borderRadius: "6px", border: "1px solid #ddd6fe" }}>
                <p style={{ margin: "0 0 6px 0", fontWeight: "600", color: "#5b21b6" }}>🪟 Window Glazing</p>
                <p style={{ margin: "2px 0", fontSize: "11px" }}>
                  {windowType.name}
                </p>
                <p style={{ margin: "5px 0 0 0", color: "#ea580c", fontWeight: "600", fontSize: "13px" }}>
                  {windowType.carbon_kgCO2_per_m2.toFixed(2)} kg CO₂/m²
                </p>
              </div>
            )}
          </div>
        </div>

        {/* PART 2: ML MODEL ANALYSIS */}
        <div style={{
          backgroundColor: "#f0f4f8",
          padding: "20px",
          borderRadius: "12px",
          border: "2px solid #93c5fd",
          marginBottom: "25px"
        }}>
          <h5 style={{ marginTop: 0, color: "#1e40af", display: "flex", alignItems: "center", gap: "8px" }}>
            🤖 Part 2: AI Sustainability Prediction
          </h5>
          <p style={{ color: "#666", fontSize: "13px", marginBottom: "15px" }}>
            Use machine learning to predict material sustainability scores based on your selections and room data.
          </p>

          {mlSustainabilityScore ? (
            <div>
              {mlSustainabilityScore.summary ? (
                <div>
                  {/* Room-by-room analysis section is rendered separately below */}
                  <div style={{
                    backgroundColor: "#dcfce7",
                    padding: "15px",
                    borderRadius: "8px",
                    marginBottom: "15px",
                    border: "1px solid #86efac",
                    textAlign: "center"
                  }}>
                    <p style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#166534", fontWeight: "600" }}>
                      ✅ Room-by-Room Analysis Complete
                    </p>
                    <p style={{ margin: "0", fontSize: "11px", color: "#166534" }}>
                      See detailed recommendations below
                    </p>
                  </div>
                </div>
              ) : (
                <div style={{ color: "red", padding: "10px", backgroundColor: "#fee2e2", borderRadius: "6px" }}>
                  Error: {mlSustainabilityScore.error || "Unknown error occurred"}
                </div>
              )}

              <div style={{ display: "flex", gap: "10px", marginTop: "15px" }}>
                <button
                  onClick={() => {
                    setMlSustainabilityScore(null);
                  }}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    border: "none",
                    background: "#e5e7eb",
                    color: "#374151",
                    fontWeight: "600",
                    cursor: "pointer",
                    fontSize: "13px"
                  }}
                >
                  Clear Results
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={analyzeWithMLModel}
              disabled={mlAnalysisLoading}
              style={{
                padding: "12px 20px",
                borderRadius: "8px",
                border: "none",
                background: mlAnalysisLoading ? "#d1d5db" : "#3b82f6",
                color: "#fff",
                fontWeight: "600",
                cursor: mlAnalysisLoading ? "not-allowed" : "pointer",
                fontSize: "14px",
                width: "100%"
              }}
            >
              {mlAnalysisLoading ? "⏳ Analyzing with AI..." : "🔍 Analyze Sustainability with ML Model"}
            </button>
          )}
        </div>

        {/* Room-by-room analysis */}
        {renderRoomByRoomAnalysis()}

        <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
          <button 
            onClick={() => setMode('overview')} 
            style={{ 
              padding: "12px 20px", 
              borderRadius: "12px", 
              border: "none", 
              background: "#d1fae5", 
              color: "#065f46", 
              fontWeight: "600", 
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            ← Back
          </button>
          <button 
            onClick={() => setMode('material')} 
            style={{ 
              padding: "12px 20px", 
              borderRadius: "12px", 
              border: "none", 
              background: "#FFB84D", 
              color: "#000", 
              fontWeight: "600", 
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            🏗️ Edit Materials
          </button>
          {wallBase && roofBase && floorBase && windowType && (
            <button 
              onClick={calculateThermalScore}
              disabled={thermalScoreLoading}
              style={{ 
                padding: "12px 20px", 
                borderRadius: "12px", 
                border: "none", 
                background: thermalScoreLoading ? "#ccc" : "#065f46", 
                color: "#fff", 
                fontWeight: "600", 
                cursor: thermalScoreLoading ? "not-allowed" : "pointer",
                fontSize: "14px",
                marginLeft: "auto"
              }}
            >
              {thermalScoreLoading ? "⏳ Analyzing..." : "🌡️ Analyze Thermal Comfort"}
            </button>
          )}
        </div>
      </div>
    );
  };

  // Render material selection interface with building elements
  const renderMaterialSelection = () => {
    const calculateRValue = (base: Material | null, insulation: Material | null) => {
      let total = 0;
      if (base) total += base.r_value_m2K_W;
      if (insulation) total += insulation.r_value_m2K_W;
      return total;
    };

    const calculateCarbon = (base: Material | null, insulation: Material | null) => {
      let total = 0;
      if (base) total += base.carbon_kgCO2_per_m2;
      if (insulation) total += insulation.carbon_kgCO2_per_m2;
      return total;
    };

    const isComplete = wallBase && roofBase && floorBase && windowType;

    return (
      <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
        <h4>🏗️ Building Element Material Selection</h4>
        <p style={{ color: "#666", fontSize: "14px" }}>Select base material and insulation for each building element</p>

        {/* WALL SECTION */}
        <div style={{ marginBottom: "30px", backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", border: "2px solid #e5e7eb" }}>
          <h5 style={{ marginTop: 0, color: "#1f2937" }}>🧱 Wall Assembly</h5>
          
          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Base Material *
            </label>
            <select 
              value={wallBase?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.wallBaseMaterials.find(m => m.id === e.target.value);
                setWallBase(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select wall base material --</option>
              {materialMapping?.wallBaseMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Insulation Layer
            </label>
            <select 
              value={wallInsulation?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.insulationMaterials.find(m => m.id === e.target.value);
                setWallInsulation(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select insulation --</option>
              {materialMapping?.insulationMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          {wallBase && (
            <div style={{ backgroundColor: "#e5f5f0", padding: "12px", borderRadius: "6px", fontSize: "13px" }}>
              <p style={{ margin: "5px 0" }}>
                <strong>R-Value:</strong> {calculateRValue(wallBase, wallInsulation).toFixed(4)} m²K/W
              </p>
              <p style={{ margin: "5px 0" }}>
                <strong>Carbon:</strong> {calculateCarbon(wallBase, wallInsulation).toFixed(2)} kg CO₂/m²
              </p>
            </div>
          )}
        </div>

        {/* ROOF SECTION */}
        <div style={{ marginBottom: "30px", backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", border: "2px solid #e5e7eb" }}>
          <h5 style={{ marginTop: 0, color: "#1f2937" }}>🏠 Roof Assembly</h5>
          
          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Base Material *
            </label>
            <select 
              value={roofBase?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.roofBaseMaterials.find(m => m.id === e.target.value);
                setRoofBase(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select roof base material --</option>
              {materialMapping?.roofBaseMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Insulation Layer
            </label>
            <select 
              value={roofInsulation?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.insulationMaterials.find(m => m.id === e.target.value);
                setRoofInsulation(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select insulation --</option>
              {materialMapping?.insulationMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          {roofBase && (
            <div style={{ backgroundColor: "#e5f5f0", padding: "12px", borderRadius: "6px", fontSize: "13px" }}>
              <p style={{ margin: "5px 0" }}>
                <strong>R-Value:</strong> {calculateRValue(roofBase, roofInsulation).toFixed(4)} m²K/W
              </p>
              <p style={{ margin: "5px 0" }}>
                <strong>Carbon:</strong> {calculateCarbon(roofBase, roofInsulation).toFixed(2)} kg CO₂/m²
              </p>
            </div>
          )}
        </div>

        {/* FLOOR SECTION */}
        <div style={{ marginBottom: "30px", backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", border: "2px solid #e5e7eb" }}>
          <h5 style={{ marginTop: 0, color: "#1f2937" }}>⬇️ Floor Assembly</h5>
          
          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Base Material *
            </label>
            <select 
              value={floorBase?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.floorBaseMaterials.find(m => m.id === e.target.value);
                setFloorBase(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select floor base material --</option>
              {materialMapping?.floorBaseMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "15px" }}>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Insulation Layer
            </label>
            <select 
              value={floorInsulation?.id || ""}
              onChange={(e) => {
                const material = materialMapping?.insulationMaterials.find(m => m.id === e.target.value);
                setFloorInsulation(material || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select insulation --</option>
              {materialMapping?.insulationMaterials.map(material => (
                <option key={material.id} value={material.id}>{material.name}</option>
              ))}
            </select>
          </div>

          {floorBase && (
            <div style={{ backgroundColor: "#e5f5f0", padding: "12px", borderRadius: "6px", fontSize: "13px" }}>
              <p style={{ margin: "5px 0" }}>
                <strong>R-Value:</strong> {calculateRValue(floorBase, floorInsulation).toFixed(4)} m²K/W
              </p>
              <p style={{ margin: "5px 0" }}>
                <strong>Carbon:</strong> {calculateCarbon(floorBase, floorInsulation).toFixed(2)} kg CO₂/m²
              </p>
            </div>
          )}
        </div>

        {/* WINDOW SECTION */}
        <div style={{ marginBottom: "30px", backgroundColor: "#f9f9f9", padding: "20px", borderRadius: "8px", border: "2px solid #e5e7eb" }}>
          <h5 style={{ marginTop: 0, color: "#1f2937" }}>🪟 Window Type</h5>
          
          <div>
            <label style={{ fontWeight: "600", display: "block", marginBottom: "8px", fontSize: "14px" }}>
              Window Glazing *
            </label>
            <select 
              value={windowType?.id || ""}
              onChange={(e) => {
                const window = materialMapping?.windowTypes.find(w => w.id === e.target.value);
                setWindowType(window || null);
              }}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #ddd",
                fontSize: "14px",
                cursor: "pointer"
              }}
            >
              <option value="">-- Select window type --</option>
              {materialMapping?.windowTypes.map(window => (
                <option key={window.id} value={window.id}>{window.name}</option>
              ))}
            </select>
          </div>

          {windowType && (
            <div style={{ backgroundColor: "#e5f5f0", padding: "12px", borderRadius: "6px", fontSize: "13px", marginTop: "15px" }}>
              <p style={{ margin: "5px 0" }}>
                <strong>U-Value:</strong> {windowType.u_value} W/m²K
              </p>
              <p style={{ margin: "5px 0" }}>
                <strong>SHGC:</strong> {windowType.shgc}
              </p>
              <p style={{ margin: "5px 0" }}>
                <strong>Carbon:</strong> {windowType.carbon_kgCO2_per_m2} kg CO₂/m²
              </p>
            </div>
          )}
        </div>

        {/* ACTIONS */}
        <div style={{ display: "flex", gap: "10px", position: "sticky", bottom: "0", backgroundColor: "white", paddingTop: "15px" }}>
          <button 
            onClick={() => setMode('overview')} 
            style={{ 
              padding: "12px 20px", 
              borderRadius: "12px", 
              border: "none", 
              background: "#d1fae5", 
              color: "#065f46", 
              fontWeight: "600", 
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            ← Back
          </button>
          {isComplete && (
            <button 
              onClick={calculateThermalScore}
              disabled={thermalScoreLoading}
              style={{ 
                padding: "12px 20px", 
                borderRadius: "12px", 
                border: "none", 
                background: thermalScoreLoading ? "#ccc" : "#065f46", 
                color: "#fff", 
                fontWeight: "600", 
                cursor: thermalScoreLoading ? "not-allowed" : "pointer",
                fontSize: "14px"
              }}
            >
              {thermalScoreLoading ? "⏳ Calculating..." : "✅ Save & Analyze (Thermal + Carbon)"}
            </button>
          )}
          {!isComplete && (
            <div style={{ fontSize: "12px", color: "#f59e0b", display: "flex", alignItems: "center" }}>
              ⚠️ Complete all required fields (marked with *)
            </div>
          )}
        </div>


      </div>
    );
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
              onClick={generateThermalRecommendations}
              disabled={!floorplan}
              style={{ 
                backgroundColor: mode === "thermal" ? "#FF6B6B" : undefined,
                opacity: !floorplan ? 0.5 : 1, 
                cursor: !floorplan ? "not-allowed" : "pointer" 
              }}
            >
              🌡️ Thermal Comfort
            </button>
            <button 
              onClick={generateVisualRecommendations}
              disabled={!floorplan || visualLoading}
              style={{ 
                backgroundColor: mode === "visual" ? "#4ECDC4" : undefined,
                opacity: !floorplan || visualLoading ? 0.5 : 1, 
                cursor: !floorplan || visualLoading ? "not-allowed" : "pointer" 
              }}
            >
              {visualLoading ? "Analyzing..." : "✨ Visual Comfort"}
            </button>
            <button 
              onClick={generateSustainabilityRecommendations}
              disabled={!floorplan || sustainabilityLoading}
              style={{ 
                backgroundColor: mode === "sustainability" ? "#95E77D" : undefined,
                opacity: !floorplan || sustainabilityLoading ? 0.5 : 1, 
                cursor: !floorplan || sustainabilityLoading ? "not-allowed" : "pointer" 
              }}
            >
              {sustainabilityLoading ? "Analyzing..." : "🌿 Sustainability"}
            </button>
            <button 
              onClick={generateMaterialRecommendations}
              disabled={!floorplan}
              style={{ 
                backgroundColor: mode === "material" ? "#FFB84D" : undefined,
                opacity: !floorplan ? 0.5 : 1, 
                cursor: !floorplan ? "not-allowed" : "pointer" 
              }}
            >
              🏗️ Material Selection
            </button>
          </div>

          <div className="design-preview">
            {error && <div style={{ color: "red", padding: "10px" }}>❌ {error}</div>}
            
            {mode === "overview" && (
              <div style={{ padding: "20px" }}>
                <h4>Recommendations & Analysis</h4>
                <p>Select a category to view detailed recommendations:</p>
                <ul>
                  <li><strong>🌡️ Thermal Comfort</strong> - Temperature, insulation, and HVAC recommendations</li>
                  <li><strong>✨ Visual Comfort</strong> - Lighting, daylight, and visual quality recommendations</li>
                  <li><strong>🌿 Sustainability</strong> - Carbon emissions analysis and low-carbon material alternatives</li>
                  <li><strong>🏗️ Material Selection</strong> - Material and construction recommendations</li>
                </ul>
                {!floorplan && <p style={{ color: "orange" }}>⚠️ Floorplan data not yet loaded</p>}
              </div>
            )}

            {mode === "thermal" && renderThermalContent()}
            {mode === "visual" && renderVisualContent()}
            {mode === "sustainability" && renderSustainabilityContent()}
            {mode === "material" && renderMaterialSelection()}

            {showEditor && (
              <div style={{ marginTop: "16px", border: "1px solid #eee", padding: "12px", borderRadius: "8px", background: "#fff", position: "absolute", bottom: 0, right: 0, width: "300px", zIndex: 1000 }}>
                <h5 style={{ marginTop: 0 }}>Recommendation Editor</h5>
                <p style={{ fontSize: "12px" }}>Edit recommendations here. Changes are local until you save.</p>

                <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "12px" }}>
                  <label style={{ fontWeight: 600, fontSize: "12px" }}>Save as:</label>
                  <select value={exportFormat} onChange={e => setExportFormat(e.target.value)} style={{ fontSize: "12px", padding: "5px" }}>
                    <option value="dxf">DXF</option>
                    <option value="dwg">DWG</option>
                    <option value="pdf">PDF</option>
                    <option value="png">Image (PNG)</option>
                  </select>
                  <button onClick={() => exportFile(exportFormat)} disabled={!floorplan || exporting} style={{ marginLeft: "8px", padding: "5px 10px", fontSize: "12px" }}>
                    {exporting ? "Exporting..." : "Save"}
                  </button>
                  <button onClick={() => setShowEditor(false)} style={{ padding: "5px 10px", fontSize: "12px" }}>Close</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sustainability;
