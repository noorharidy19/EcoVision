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

interface OptimizationOption {
  after: {
    materials: Record<string, { name: string; carbon_kg: number; comfort: number }>;
    total_carbon: number;
    avg_comfort: number;
    final_score: number;
  };
  comparison: {
    carbon_saved_kg: number;
    carbon_reduction_pct: number;
    comfort_change: number;
    comfort_status: string;
  };
}

interface RoomAnalysis {
  room: string;
  area_m2: number;
  your_selection: {
    materials: Record<string, { name: string; carbon_kg: number }>;
    total_carbon_kg: number;
    avg_comfort?: number;
  };
  recommendations: OptimizationOption[];
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

interface SustainabilityApiResponse {
  status?: "success" | "error";
  summary?: MLAnalysisResult["summary"];
  rooms?: RoomAnalysis[];
  error?: string;
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
  const [mlSustainabilityScore, setMlSustainabilityScore] = useState<SustainabilityApiResponse | null>(null);
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

  const [visualRecs, setVisualRecs] = useState<any>(null);
  const [visualRecsLoading, setVisualRecsLoading] = useState(false);
  const [showVisualRecs, setShowVisualRecs] = useState(false);

  const [thermalScenarios, setThermalScenarios] = useState<any>(null);
  const [thermalScenariosLoading, setThermalScenariosLoading] = useState(false);
  const [showThermalScenarios, setShowThermalScenarios] = useState(false);

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

  const fetchVisualRecommendations = async () => {
    if (!visualScore || !floorplan) return;

    setVisualRecsLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        "http://127.0.0.1:8000/analysis/visual/recommendations",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            analysis_result: visualScore,
            floorplan_json: floorplan.json_data || {}
          })
        }
      );
      const data = await response.json();
      setVisualRecs(data);
      setShowVisualRecs(true);
    } catch (err) {
      setError("Failed to load recommendations");
    } finally {
      setVisualRecsLoading(false);
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
      
      setThermalScore(thermalData);
      setMode("thermal");
    } catch (err) {
      console.error("Error calculating thermal score:", err);
      setError(err instanceof Error ? err.message : "Failed to calculate thermal score");
    } finally {
      setThermalScoreLoading(false);
    }
  };

  const fetchThermalRecommendations = async () => {
    if (!thermalScore || !floorplan) return;

    setThermalScenariosLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        "http://127.0.0.1:8000/analysis/thermal/recommendations",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            analysis_result: thermalScore,
            floorplan_json: floorplan.json_data || {}
          })
        }
      );
      const data = await response.json();
      setThermalScenarios(data);
      setShowThermalScenarios(true);
    } catch (err) {
      setError("Failed to load thermal recommendations");
    } finally {
      setThermalScenariosLoading(false);
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

      const rooms = floorplan.json_data?.rooms || [];

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

      const sustainabilityData: SustainabilityApiResponse = await response.json();
      console.log("ML Sustainability analysis received:", sustainabilityData);
      setMlSustainabilityScore(sustainabilityData);
      
      if (
        sustainabilityData?.status === "success"
        && sustainabilityData.summary
        && sustainabilityData.rooms
      ) {
        setRoomByRoomAnalysis({
          summary: sustainabilityData.summary,
          rooms: sustainabilityData.rooms,
        });
      } else {
        setRoomByRoomAnalysis(null);
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

            {/* Show recommendations or the view recommendations button */}
            {showThermalScenarios ? (
              renderThermalRecommendations()
            ) : (
              <div style={{ display: "flex", gap: "10px" }}>
                <button 
                  onClick={() => {
                    setThermalScore(null);
                    setShowThermalScenarios(false);
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
                  onClick={fetchThermalRecommendations}
                  disabled={thermalScenariosLoading}
                  style={{ 
                    padding: "10px 24px", 
                    borderRadius: "12px", 
                    border: "none",
                    background: thermalScenariosLoading ? "#ccc" : "#065f46",
                    color: "#fff", 
                    fontWeight: "600", 
                    cursor: thermalScenariosLoading ? "not-allowed" : "pointer"
                  }}
                >
                  {thermalScenariosLoading ? "Loading..." : "🌡️ View Improvement Scenarios"}
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
                    cursor: "pointer",
                    marginLeft: "auto"
                  }}
                >
                  🏗️ Modify Materials
                </button>
              </div>
            )}
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

  const renderThermalRecommendations = () => {
    if (!thermalScenarios) return null;

    const getScoreColor = (score: number) => {
      if (score >= 70) return "#10b981";
      if (score >= 50) return "#f59e0b";
      return "#ef4444";
    };

    return (
      <div style={{ marginTop: "20px" }}>
        <h4>🌡️ Thermal Improvement Scenarios</h4>

        {/* Main issue box */}
        {thermalScenarios.has_recommendations && (
          <div style={{
            backgroundColor: "#fef9c3",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #fcd34d",
            marginBottom: "16px"
          }}>
            <p style={{ margin: 0, fontWeight: "600", color: "#78350f" }}>
              Main Issue: {thermalScenarios.main_issue}
            </p>
          </div>
        )}

        {/* No recommendations case */}
        {!thermalScenarios.has_recommendations && (
          <div style={{
            backgroundColor: "#fce7e7",
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #fca5a5",
            marginBottom: "16px"
          }}>
            <p style={{ margin: 0, color: "#7f1d1d" }}>
              {thermalScenarios.message}
            </p>
          </div>
        )}

        {/* Scenarios */}
        {thermalScenarios.scenarios?.map((scenario: any, i: number) => (
          <div key={i} style={{
            backgroundColor: "#f0fdf4",
            padding: "18px",
            borderRadius: "10px",
            border: "2px solid #86efac",
            marginBottom: "14px"
          }}>
            <h5 style={{ marginTop: 0, color: "#166534" }}>
              {i + 1}. {scenario.design_action}
            </h5>
            <p style={{ color: "#374151", fontSize: "13px", marginBottom: "14px" }}>
              {scenario.description}
            </p>
            <p style={{ color: "#666", fontSize: "12px", marginBottom: "14px", fontStyle: "italic" }}>
              {scenario.why_it_helps}
            </p>

            {/* Score comparison */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "12px",
              marginBottom: "12px"
            }}>
              <div style={{
                backgroundColor: "#fff",
                padding: "12px",
                borderRadius: "8px",
                textAlign: "center",
                border: "1px solid #d1d5db"
              }}>
                <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#6b7280" }}>
                  Current Score
                </p>
                <p style={{
                  margin: 0,
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: getScoreColor(thermalScore?.comfort_score || 0)
                }}>
                  {(thermalScore?.comfort_score || 0).toFixed(1)}%
                </p>
                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#6b7280" }}>
                  {thermalScore?.comfort_class}
                </p>
              </div>

              <div style={{
                backgroundColor: "#fff",
                padding: "12px",
                borderRadius: "8px",
                textAlign: "center",
                border: "2px solid #10b981"
              }}>
                <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#6b7280" }}>
                  Projected Score
                </p>
                <p style={{
                  margin: 0,
                  fontSize: "24px",
                  fontWeight: "bold",
                  color: getScoreColor(scenario.projected_score)
                }}>
                  {scenario.projected_score.toFixed(1)}%
                </p>
                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#059669" }}>
                  +{(scenario.projected_score - (thermalScore?.comfort_score || 0)).toFixed(1)}% improvement
                </p>
              </div>
            </div>

            {/* Projected metrics */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "8px",
              fontSize: "11px"
            }}>
              {[
                { label: "PMV", value: scenario.projected_pmv },
                { label: "PPD", value: `${scenario.projected_ppd}%` },
                { label: "Tdb", value: `${scenario.projected_tdb}°C` },
                { label: "Tr", value: `${scenario.projected_tr}°C` }
              ].map((m, j) => (
                <div key={j} style={{
                  backgroundColor: "#ecfdf5",
                  padding: "8px",
                  borderRadius: "6px",
                  textAlign: "center"
                }}>
                  <p style={{ margin: "0 0 2px 0", color: "#6b7280" }}>{m.label}</p>
                  <p style={{ margin: 0, fontWeight: "600", color: "#065f46" }}>
                    {m.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}

        <button
          onClick={() => setShowThermalScenarios(false)}
          style={{
            padding: "10px 18px",
            borderRadius: "12px",
            border: "none",
            background: "#d1fae5",
            color: "#065f46",
            fontWeight: "600",
            cursor: "pointer",
            marginTop: "8px"
          }}
        >
          ← Back to Analysis
        </button>
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

        {/* Show recommendations or the view recommendations button */}
        {showVisualRecs ? (
          renderVisualRecommendations()
        ) : (
          <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
            <button onClick={() => setMode("overview")}
              style={{
                padding: "10px 18px", borderRadius: "12px",
                border: "none", background: "#d1fae5",
                color: "#065f46", fontWeight: "600", cursor: "pointer"
              }}>
              ← Back
            </button>
            <button
              onClick={fetchVisualRecommendations}
              disabled={visualRecsLoading}
              style={{
                padding: "10px 24px", borderRadius: "12px",
                border: "none",
                background: visualRecsLoading ? "#ccc" : "#065f46",
                color: "#fff", fontWeight: "600",
                cursor: visualRecsLoading ? "not-allowed" : "pointer"
              }}>
              {visualRecsLoading ? "Loading..." : "✨ View Recommendations"}
            </button>
          </div>
        )}
      </div>
    );
  };

  // إرجاع ميثود الـ Visual الفولدر المفقود لحل إيرور الـ الـ Compile
  const renderVisualRecommendations = () => {
    if (!visualRecs) return null;

    const getScoreColor = (score: number) => {
      if (score >= 67) return "#4ECDC4";
      if (score >= 34) return "#f59e0b";
      return "#ef4444";
    };

    return (
      <div style={{ marginTop: "20px" }}>
        <h4>✨ Visual Improvement Scenarios</h4>

        {visualRecs.has_recommendations && (
          <div style={{ backgroundColor: "#fef9c3", padding: "15px", borderRadius: "8px", border: "1px solid #fcd34d", marginBottom: "16px" }}>
            <p style={{ margin: 0, fontWeight: "600", color: "#78350f" }}>Main Issue: {visualRecs.main_issue}</p>
          </div>
        )}

        {!visualRecs.has_recommendations && (
          <div style={{ backgroundColor: "#fce7e7", padding: "15px", borderRadius: "8px", border: "1px solid #fca5a5", marginBottom: "16px" }}>
            <p style={{ margin: 0, color: "#7f1d1d" }}>{visualRecs.message}</p>
          </div>
        )}

        {visualRecs.scenarios?.map((scenario: any, i: number) => (
          <div key={i} style={{ backgroundColor: "#f0fdf4", padding: "18px", borderRadius: "10px", border: "2px solid #86efac", marginBottom: "14px" }}>
            <h5 style={{ marginTop: 0, color: "#166534" }}>{i + 1}. {scenario.fix}</h5>
            <p style={{ color: "#374151", fontSize: "13px", marginBottom: "14px" }}>{scenario.description}</p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
              <div style={{ backgroundColor: "#fff", padding: "12px", borderRadius: "8px", textAlign: "center", border: "1px solid #d1d5db" }}>
                <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#6b7280" }}>Current Score</p>
                <p style={{ margin: 0, fontSize: "24px", fontWeight: "bold", color: getScoreColor(visualRecs.current_score) }}>{visualRecs.current_score.toFixed(1)}%</p>
                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#6b7280" }}>{visualRecs.current_class}</p>
              </div>

              <div style={{ backgroundColor: "#fff", padding: "12px", borderRadius: "8px", textAlign: "center", border: "2px solid #4ECDC4" }}>
                <p style={{ margin: "0 0 4px 0", fontSize: "12px", color: "#6b7280" }}>Projected Score</p>
                <p style={{ margin: 0, fontSize: "24px", fontWeight: "bold", color: getScoreColor(scenario.projected_score) }}>{scenario.projected_score.toFixed(1)}%</p>
                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#059669" }}>+{scenario.score_change}% improvement</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", fontSize: "11px" }}>
              {[
                { label: "Lux", value: `${scenario.projected_lux} lux` },
                { label: "DGI", value: scenario.projected_dgi },
                { label: "CCT", value: `${scenario.projected_cct}K` },
                { label: "View", value: `${scenario.projected_view}/100` }
              ].map((m, j) => (
                <div key={j} style={{ backgroundColor: "#ecfdf5", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                  <p style={{ margin: "0 0 2px 0", color: "#6b7280" }}>{m.label}</p>
                  <p style={{ margin: 0, fontWeight: "600", color: "#065f46" }}>{m.value}</p>
                </div>
              ))}
            </div>
          </div>
        ))}

        <button onClick={() => setShowVisualRecs(false)} style={{ padding: "10px 18px", borderRadius: "12px", border: "none", background: "#d1fae5", color: "#065f46", fontWeight: "600", cursor: "pointer", marginTop: "8px" }}>← Back to Analysis</button>
      </div>
    );
  };

  // ── تفريغ الـ 3 البدائل التنافسية لكل غرفة منفصلة تماماً بدون أي هارد كود للـ Total Carbon ──
  const renderRoomByRoomAnalysis = () => {
    if (!roomByRoomAnalysis) return null;

    const { rooms } = roomByRoomAnalysis;

    return (
      <div style={{
        backgroundColor: "#f8fafc",
        padding: "20px",
        borderRadius: "12px",
        border: "2px solid #cbd5e1",
        marginTop: "20px"
      }}>
        <h5 style={{ marginTop: 0, color: "#0f172a", fontSize: "18px", fontWeight: "700", borderBottom: "2px solid #e2e8f0", paddingBottom: "10px", marginBottom: "20px" }}>
          🏗️ Room-by-Room Carbon Analysis
        </h5>

        {/* Room List Loop - كل غرفة تظهر كـ زون منفصل كامل وبداخله الـ 3 بدائل التنافسية للغرفة دي بس */}
        <div style={{ display: "flex", flexDirection: "column", gap: "30px" }}>
          {rooms.map((room, idx) => (
            <div key={idx} style={{
              backgroundColor: "#fff",
              padding: "25px",
              borderRadius: "12px",
              border: "1px solid #cbd5e1",
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)"
            }}>
              <h4 style={{ margin: "0 0 6px 0", color: "#1e3a8a", fontSize: "18px", fontWeight: "800" }}>
                ROOM: {room.room}
              </h4>
              <p style={{ margin: "0 0 20px 0", fontSize: "14px", color: "#475569", borderBottom: "1px dashed #e2e8f0", paddingBottom: "10px" }}>
                <strong>Area:</strong> {room.area_m2} m²
              </p>

              {/* BEFORE PANEL — User Selection Baseline */}
              <div style={{ backgroundColor: "#f8fafc", padding: "15px 20px", borderRadius: "8px", border: "1px solid #e2e8f0", marginBottom: "20px" }}>
                <span style={{ fontWeight: "700", color: "#334155", fontSize: "13px", display: "block", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  BEFORE — User Selection
                </span>
                <div style={{ display: "flex", gap: "25px", fontSize: "13px", color: "#1e293b", fontWeight: "600", marginBottom: "4px" }}>
                  <span>Carbon : <span style={{ color: "#b91c1c" }}>{room.your_selection.total_carbon_kg.toFixed(2)} kg CO2</span></span>
                  {room.your_selection.avg_comfort !== undefined && (
                    <span>Comfort: <span style={{ color: "#2563eb" }}>{room.your_selection.avg_comfort.toFixed(3)} / 1</span></span>
                  )}
                </div>
              </div>

              {/* AFTER PANEL — AI Recommendations #1, #2, #3 Breakdown */}
              <div style={{ paddingLeft: "15px", borderLeft: "4px solid #2563eb" }}>
                <span style={{ fontWeight: "700", color: "#1e3a8a", fontSize: "13px", display: "block", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  AFTER — AI Recommendations
                </span>

                {room.recommendations && room.recommendations.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                    {room.recommendations.map((rec, rIdx) => (
                      <div key={rIdx} style={{
                        backgroundColor: "#fff",
                        padding: "16px 20px",
                        borderRadius: "8px",
                        border: "1px solid #e2e8f0",
                        boxShadow: "0 1px 2px rgba(0,0,0,0.02)"
                      }}>
                        <span style={{ fontWeight: "700", color: "#2563eb", fontSize: "13px", display: "block", marginBottom: "8px" }}>
                          Recommendation #{rIdx + 1}
                        </span>
                        <div style={{ borderTop: "1px dashed #cbd5e1", marginBottom: "12px" }} />
                        
                        {/* Assembly Layer Specs */}
                        <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "13px", color: "#334155", marginBottom: "12px" }}>
                          <div><strong style={{ color: "#475569" }}>Wall :</strong> {rec.after.materials.wall?.name || "N/A"}</div>
                          <div><strong style={{ color: "#475569" }}>Floor :</strong> {rec.after.materials.floor?.name || "N/A"}</div>
                          <div><strong style={{ color: "#475569" }}>Ceiling :</strong> {rec.after.materials.ceiling?.name || "N/A"}</div>
                        </div>

                        {/* Exact Values Readout */}
                        <div style={{ display: "flex", gap: "25px", fontSize: "13px", color: "#0f172a", fontWeight: "600", backgroundColor: "#f8fafc", padding: "10px 15px", borderRadius: "6px", border: "1px solid #f1f5f9", marginBottom: "12px" }}>
                          <span>Carbon : {rec.after.total_carbon.toFixed(2)} kg CO2</span>
                          <span>Comfort : {rec.after.avg_comfort.toFixed(3)} / 1</span>
                          <span>Score : {rec.after.final_score.toFixed(3)}</span>
                        </div>

                        {/* Comparative Vectors Block */}
                        <div style={{ paddingLeft: "10px", borderLeft: "2px solid #cbd5e1", fontSize: "12px", color: "#475569" }}>
                          <span style={{ fontWeight: "700", color: "#64748b", display: "block", marginBottom: "4px" }}>Comparison:</span>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "6px" }}>
                            <div>Carbon Saved : <span style={{ color: "#16a34a", fontWeight: "700" }}>{rec.comparison.carbon_saved_kg.toFixed(2)} kg CO2</span></div>
                            <div>Carbon Reduction : <span style={{ color: "#16a34a", fontWeight: "700" }}>{rec.comparison.carbon_reduction_pct.toFixed(2)}%</span></div>
                            <div>Comfort Change : <span style={{ color: rec.comparison.comfort_change >= 0 ? "#16a34a" : "#dc2626", fontWeight: "600" }}>{rec.comparison.comfort_change.toFixed(3)}</span></div>
                            <div>Comfort Status : <span style={{ color: rec.comparison.comfort_status === "reduced" ? "#dc2626" : "#16a34a", fontWeight: "700", textTransform: "capitalize" }}>{rec.comparison.comfort_status}</span></div>
                          </div>
                        </div>

                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: "13px", color: "#94a3b8", fontStyle: "italic" }}>No configurations passed structural Pareto optimization checks.</p>
                )}
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

    return (
      <div style={{ padding: "20px", maxHeight: "90vh", overflowY: "auto" }}>
        <h4>🌿 Sustainability & Carbon Analysis</h4>

        {/* PART 2: ML MODEL ANALYSIS */}
        <div style={{
          backgroundColor: "#f0f4f8",
          padding: "20px",
          borderRadius: "12px",
          border: "2px solid #93c5fd",
          marginBottom: "25px"
        }}>
          <h5 style={{ marginTop: 0, color: "#1e40af", display: "flex", alignItems: "center", gap: "8px" }}>
            🤖 Sustainability Model Output
          </h5>
          <p style={{ color: "#666", fontSize: "13px", marginBottom: "15px" }}>
            Results below are rendered directly from the backend sustainability function without frontend carbon calculations.
          </p>

          {mlSustainabilityScore ? (
            <div>
              {mlSustainabilityScore.summary ? (
                <div>
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
                      See detailed backend output below
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