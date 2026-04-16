
import { useState, useEffect } from "react";
import "../styles/designWorkspace.css";

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

type MaterialCategory = "wallBase" | "roofBase" | "floorBase" | "insulation" | "window";

const MaterialsAdmin = () => {
  const [materialMapping, setMaterialMapping] = useState<MaterialsMapping | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MaterialCategory>("wallBase");
  const [showAddForm, setShowAddForm] = useState(false);

  // Form states for adding new material
  const [newMaterial, setNewMaterial] = useState({
    name: "",
    category: "",
    roughness: "",
    thickness_m: 0.1,
    conductivity_W_mK: 0.5,
    density_kg_m3: 1000,
    specific_heat_J_kgK: 1000,
    carbon_kgCO2_per_kg: 0.5,
    r_value_m2K_W: 0.2,
    carbon_kgCO2_per_m2: 0.5,
  });

  const [newWindow, setNewWindow] = useState({
    name: "",
    u_value: 2.0,
    shgc: 0.6,
    carbon_kgCO2_per_m2: 15,
  });

  // Load materials data from JSON
  useEffect(() => {
    console.log("Starting to load materials...");
    fetch("/materials-mapping.json")
      .then(res => {
        console.log("Response received:", res.status);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: any) => {
        console.log("Materials mapping loaded:", data);
        // Ensure all properties exist, fill missing ones with defaults
        const mappedData: MaterialsMapping = {
          wallBaseMaterials: (data.wallBaseMaterials || []).map((m: any) => ({
            id: m.id || `mat_${Math.random()}`,
            name: m.name || "Unknown",
            category: m.category || "general",
            roughness: m.roughness || "medium",
            thickness_m: m.thickness_m || 0.1,
            conductivity_W_mK: m.conductivity_W_mK || 0.5,
            density_kg_m3: m.density_kg_m3 || 1000,
            specific_heat_J_kgK: m.specific_heat_J_kgK || 1000,
            carbon_kgCO2_per_kg: m.carbon_kgCO2_per_kg || 0.5,
            r_value_m2K_W: m.r_value_m2K_W || 0.2,
            carbon_kgCO2_per_m2: m.carbon_kgCO2_per_m2 || 10,
          })),
          roofBaseMaterials: (data.roofBaseMaterials || []).map((m: any) => ({
            id: m.id || `mat_${Math.random()}`,
            name: m.name || "Unknown",
            category: m.category || "general",
            roughness: m.roughness || "medium",
            thickness_m: m.thickness_m || 0.1,
            conductivity_W_mK: m.conductivity_W_mK || 0.5,
            density_kg_m3: m.density_kg_m3 || 1000,
            specific_heat_J_kgK: m.specific_heat_J_kgK || 1000,
            carbon_kgCO2_per_kg: m.carbon_kgCO2_per_kg || 0.5,
            r_value_m2K_W: m.r_value_m2K_W || 0.2,
            carbon_kgCO2_per_m2: m.carbon_kgCO2_per_m2 || 10,
          })),
          floorBaseMaterials: (data.floorBaseMaterials || []).map((m: any) => ({
            id: m.id || `mat_${Math.random()}`,
            name: m.name || "Unknown",
            category: m.category || "general",
            roughness: m.roughness || "medium",
            thickness_m: m.thickness_m || 0.1,
            conductivity_W_mK: m.conductivity_W_mK || 0.5,
            density_kg_m3: m.density_kg_m3 || 1000,
            specific_heat_J_kgK: m.specific_heat_J_kgK || 1000,
            carbon_kgCO2_per_kg: m.carbon_kgCO2_per_kg || 0.5,
            r_value_m2K_W: m.r_value_m2K_W || 0.2,
            carbon_kgCO2_per_m2: m.carbon_kgCO2_per_m2 || 10,
          })),
          insulationMaterials: (data.insulationMaterials || []).map((m: any) => ({
            id: m.id || `mat_${Math.random()}`,
            name: m.name || "Unknown",
            category: m.category || "insulation",
            roughness: m.roughness || "medium",
            thickness_m: m.thickness_m || 0.05,
            conductivity_W_mK: m.conductivity_W_mK || 0.05,
            density_kg_m3: m.density_kg_m3 || 50,
            specific_heat_J_kgK: m.specific_heat_J_kgK || 1000,
            carbon_kgCO2_per_kg: m.carbon_kgCO2_per_kg || 0.3,
            r_value_m2K_W: m.r_value_m2K_W || 0.5,
            carbon_kgCO2_per_m2: m.carbon_kgCO2_per_m2 || 5,
          })),
          windowTypes: (data.windowTypes || []).map((w: any) => ({
            id: w.id || `win_${Math.random()}`,
            name: w.name || "Unknown",
            u_value: w.u_value || 2.0,
            shgc: w.shgc || 0.6,
            carbon_kgCO2_per_m2: w.carbon_kgCO2_per_m2 || 15,
          })),
        };
        console.log("Mapped data:", mappedData);
        setMaterialMapping(mappedData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading materials:", err);
        setError(`Failed to load materials: ${err.message}`);
        setLoading(false);
      });
  }, []);

  // Remove material from dataset
  const removeMaterial = (materialId: string, category: MaterialCategory) => {
    if (!materialMapping) return;

    if (window.confirm("Are you sure you want to remove this material?")) {
      const updatedMapping = { ...materialMapping };

      switch (category) {
        case "wallBase":
          updatedMapping.wallBaseMaterials = updatedMapping.wallBaseMaterials.filter(m => m.id !== materialId);
          break;
        case "roofBase":
          updatedMapping.roofBaseMaterials = updatedMapping.roofBaseMaterials.filter(m => m.id !== materialId);
          break;
        case "floorBase":
          updatedMapping.floorBaseMaterials = updatedMapping.floorBaseMaterials.filter(m => m.id !== materialId);
          break;
        case "insulation":
          updatedMapping.insulationMaterials = updatedMapping.insulationMaterials.filter(m => m.id !== materialId);
          break;
        case "window":
          updatedMapping.windowTypes = updatedMapping.windowTypes.filter(w => w.id !== materialId);
          break;
      }

      setMaterialMapping(updatedMapping);
      // In production, would save to backend
      console.log("Material removed:", materialId);
    }
  };

  // Add new material
  const addNewMaterial = () => {
    if (!materialMapping) return;

    if (!newMaterial.name) {
      setError("Material name is required");
      return;
    }

    const updatedMapping = { ...materialMapping };
    const materialId = `mat_${Date.now()}`;

    const materialToAdd: Material = {
      id: materialId,
      name: newMaterial.name,
      category: newMaterial.category,
      roughness: newMaterial.roughness,
      thickness_m: newMaterial.thickness_m,
      conductivity_W_mK: newMaterial.conductivity_W_mK,
      density_kg_m3: newMaterial.density_kg_m3,
      specific_heat_J_kgK: newMaterial.specific_heat_J_kgK,
      carbon_kgCO2_per_kg: newMaterial.carbon_kgCO2_per_kg,
      r_value_m2K_W: newMaterial.r_value_m2K_W,
      carbon_kgCO2_per_m2: newMaterial.carbon_kgCO2_per_m2,
    };

    switch (activeTab) {
      case "wallBase":
        updatedMapping.wallBaseMaterials.push(materialToAdd);
        break;
      case "roofBase":
        updatedMapping.roofBaseMaterials.push(materialToAdd);
        break;
      case "floorBase":
        updatedMapping.floorBaseMaterials.push(materialToAdd);
        break;
      case "insulation":
        updatedMapping.insulationMaterials.push(materialToAdd);
        break;
    }

    setMaterialMapping(updatedMapping);
    setShowAddForm(false);
    setNewMaterial({
      name: "",
      category: "",
      roughness: "",
      thickness_m: 0.1,
      conductivity_W_mK: 0.5,
      density_kg_m3: 1000,
      specific_heat_J_kgK: 1000,
      carbon_kgCO2_per_kg: 0.5,
      r_value_m2K_W: 0.2,
      carbon_kgCO2_per_m2: 0.5,
    });
    console.log("New material added:", materialToAdd);
  };

  // Add new window type
  const addNewWindow = () => {
    if (!materialMapping) return;

    if (!newWindow.name) {
      setError("Window name is required");
      return;
    }

    const updatedMapping = { ...materialMapping };
    const windowId = `win_${Date.now()}`;

    const windowToAdd: WindowType = {
      id: windowId,
      name: newWindow.name,
      u_value: newWindow.u_value,
      shgc: newWindow.shgc,
      carbon_kgCO2_per_m2: newWindow.carbon_kgCO2_per_m2,
    };

    updatedMapping.windowTypes.push(windowToAdd);
    setMaterialMapping(updatedMapping);
    setShowAddForm(false);
    setNewWindow({
      name: "",
      u_value: 2.0,
      shgc: 0.6,
      carbon_kgCO2_per_m2: 15,
    });
    console.log("New window type added:", windowToAdd);
  };

  // Get current materials list based on active tab
  const getCurrentMaterials = (): (Material | WindowType)[] => {
    if (!materialMapping) return [];

    switch (activeTab) {
      case "wallBase":
        return materialMapping.wallBaseMaterials;
      case "roofBase":
        return materialMapping.roofBaseMaterials;
      case "floorBase":
        return materialMapping.floorBaseMaterials;
      case "insulation":
        return materialMapping.insulationMaterials;
      case "window":
        return materialMapping.windowTypes;
      default:
        return [];
    }
  };

  const isWindow = activeTab === "window";
  const currentMaterials = getCurrentMaterials();

  return (
    <div className="workspace-layout">
      <div style={{ padding: "20px", maxHeight: "100vh", overflowY: "auto" }}>
        <h2>🏗️ Materials Admin Dashboard</h2>
        <p style={{ color: "#666" }}>Manage building materials and window types in the dataset</p>

        {loading && (
          <div style={{ 
            backgroundColor: "#e5f5f0", 
            padding: "20px", 
            borderRadius: "8px", 
            textAlign: "center",
            color: "#065f46" 
          }}>
            <p><strong>⏳ Loading materials from database...</strong></p>
          </div>
        )}
        {error && (
          <div style={{ 
            color: "#991b1b", 
            padding: "15px", 
            backgroundColor: "#fee2e2", 
            borderRadius: "6px", 
            marginBottom: "20px",
            border: "1px solid #fca5a5"
          }}>
            <strong>❌ Error:</strong> {error}
            <button 
              onClick={() => window.location.reload()}
              style={{
                marginLeft: "10px",
                padding: "5px 10px",
                borderRadius: "4px",
                border: "none",
                background: "#dc2626",
                color: "#fff",
                cursor: "pointer",
                fontSize: "12px"
              }}
            >
              🔄 Retry
            </button>
          </div>
        )}

        {!loading && materialMapping && (
          <div>
            {/* Navigation Tabs */}
            <div style={{ display: "flex", gap: "10px", marginBottom: "20px", borderBottom: "2px solid #e5e7eb", flexWrap: "wrap" }}>
              <button
                onClick={() => setActiveTab("wallBase")}
                style={{
                  padding: "12px 16px",
                  border: "none",
                  borderBottom: activeTab === "wallBase" ? "3px solid #065f46" : "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  fontWeight: activeTab === "wallBase" ? "600" : "400",
                  color: activeTab === "wallBase" ? "#065f46" : "#666",
                }}
              >
                🧱 Wall Base ({materialMapping.wallBaseMaterials.length})
              </button>
              <button
                onClick={() => setActiveTab("roofBase")}
                style={{
                  padding: "12px 16px",
                  border: "none",
                  borderBottom: activeTab === "roofBase" ? "3px solid #065f46" : "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  fontWeight: activeTab === "roofBase" ? "600" : "400",
                  color: activeTab === "roofBase" ? "#065f46" : "#666",
                }}
              >
                🏠 Roof Base ({materialMapping.roofBaseMaterials.length})
              </button>
              <button
                onClick={() => setActiveTab("floorBase")}
                style={{
                  padding: "12px 16px",
                  border: "none",
                  borderBottom: activeTab === "floorBase" ? "3px solid #065f46" : "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  fontWeight: activeTab === "floorBase" ? "600" : "400",
                  color: activeTab === "floorBase" ? "#065f46" : "#666",
                }}
              >
                ⬇️ Floor Base ({materialMapping.floorBaseMaterials.length})
              </button>
              <button
                onClick={() => setActiveTab("insulation")}
                style={{
                  padding: "12px 16px",
                  border: "none",
                  borderBottom: activeTab === "insulation" ? "3px solid #065f46" : "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  fontWeight: activeTab === "insulation" ? "600" : "400",
                  color: activeTab === "insulation" ? "#065f46" : "#666",
                }}
              >
                🔒 Insulation ({materialMapping.insulationMaterials.length})
              </button>
              <button
                onClick={() => setActiveTab("window")}
                style={{
                  padding: "12px 16px",
                  border: "none",
                  borderBottom: activeTab === "window" ? "3px solid #065f46" : "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                  fontWeight: activeTab === "window" ? "600" : "400",
                  color: activeTab === "window" ? "#065f46" : "#666",
                }}
              >
                🪟 Windows ({materialMapping.windowTypes.length})
              </button>
            </div>

            {/* Add New Button */}
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              style={{
                padding: "10px 16px",
                borderRadius: "8px",
                border: "none",
                background: "#10b981",
                color: "#fff",
                fontWeight: "600",
                cursor: "pointer",
                marginBottom: "20px",
              }}
            >
              {showAddForm ? "✖️ Cancel" : "➕ Add New"}
            </button>

            {/* Add New Material Form */}
            {showAddForm && (
              <div style={{
                backgroundColor: "#f0fdf4",
                padding: "20px",
                borderRadius: "12px",
                border: "2px solid #86efac",
                marginBottom: "20px"
              }}>
                <h4 style={{ marginTop: 0 }}>Add New {isWindow ? "Window Type" : "Material"}</h4>

                {isWindow ? (
                  <div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginBottom: "15px" }}>
                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Window Name *
                        </label>
                        <input
                          type="text"
                          value={newWindow.name}
                          onChange={(e) => setNewWindow({ ...newWindow, name: e.target.value })}
                          placeholder="e.g., Double Glazed Low-E"
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          U-Value (W/m²K)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newWindow.u_value}
                          onChange={(e) => setNewWindow({ ...newWindow, u_value: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          SHGC
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={newWindow.shgc}
                          onChange={(e) => setNewWindow({ ...newWindow, shgc: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Carbon (kg CO₂/m²)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newWindow.carbon_kgCO2_per_m2}
                          onChange={(e) => setNewWindow({ ...newWindow, carbon_kgCO2_per_m2: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>
                    </div>

                    <button
                      onClick={addNewWindow}
                      style={{
                        padding: "10px 16px",
                        borderRadius: "8px",
                        border: "none",
                        background: "#065f46",
                        color: "#fff",
                        fontWeight: "600",
                        cursor: "pointer",
                      }}
                    >
                      ✅ Add Window Type
                    </button>
                  </div>
                ) : (
                  <div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px", marginBottom: "15px" }}>
                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Material Name *
                        </label>
                        <input
                          type="text"
                          value={newMaterial.name}
                          onChange={(e) => setNewMaterial({ ...newMaterial, name: e.target.value })}
                          placeholder="e.g., Concrete"
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Category
                        </label>
                        <input
                          type="text"
                          value={newMaterial.category}
                          onChange={(e) => setNewMaterial({ ...newMaterial, category: e.target.value })}
                          placeholder="e.g., Structural"
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Thickness (m)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newMaterial.thickness_m}
                          onChange={(e) => setNewMaterial({ ...newMaterial, thickness_m: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Conductivity (W/mK)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newMaterial.conductivity_W_mK}
                          onChange={(e) => setNewMaterial({ ...newMaterial, conductivity_W_mK: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          R-Value (m²K/W)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={newMaterial.r_value_m2K_W}
                          onChange={(e) => setNewMaterial({ ...newMaterial, r_value_m2K_W: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Carbon (kg CO₂/m²)
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          value={newMaterial.carbon_kgCO2_per_m2}
                          onChange={(e) => setNewMaterial({ ...newMaterial, carbon_kgCO2_per_m2: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>

                      <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "5px", color: "#000" }}>
                          Density (kg/m³)
                        </label>
                        <input
                          type="number"
                          value={newMaterial.density_kg_m3}
                          onChange={(e) => setNewMaterial({ ...newMaterial, density_kg_m3: parseFloat(e.target.value) })}
                          style={{
                            width: "100%",
                            padding: "8px",
                            borderRadius: "6px",
                            border: "1px solid #ddd",
                            fontSize: "14px",
                            color: "#000",
                          }}
                        />
                      </div>
                    </div>

                    <button
                      onClick={addNewMaterial}
                      style={{
                        padding: "10px 16px",
                        borderRadius: "8px",
                        border: "none",
                        background: "#065f46",
                        color: "#fff",
                        fontWeight: "600",
                        cursor: "pointer",
                      }}
                    >
                      ✅ Add Material
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Materials List */}
            <div>
              <h3>
                {activeTab === "wallBase" && "🧱 Wall Base Materials"}
                {activeTab === "roofBase" && "🏠 Roof Base Materials"}
                {activeTab === "floorBase" && "⬇️ Floor Base Materials"}
                {activeTab === "insulation" && "🔒 Insulation Materials"}
                {activeTab === "window" && "🪟 Window Types"}
              </h3>

              {currentMaterials.length === 0 ? (
                <p style={{ color: "#999" }}>No materials in this category</p>
              ) : (
                <div style={{ display: "grid", gap: "12px" }}>
                  {currentMaterials.map((material, idx) => (
                    <div
                      key={idx}
                      style={{
                        backgroundColor: "#fff",
                        border: "1px solid #e5e7eb",
                        borderRadius: "8px",
                        padding: "15px",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "start",
                      }}
                    >
                      <div>
                        <h5 style={{ margin: "0 0 8px 0", backgroundColor: "#c6f6d5", padding: "8px 12px", borderRadius: "6px", color: "#000" }}>
                          {isWindow ? (material as WindowType).name : (material as Material).name}
                        </h5>
                        <div style={{ fontSize: "13px", color: "#000", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                          {isWindow ? (
                            <>
                              <p style={{ margin: "3px 0" }}>
                                <strong>U-Value:</strong> {(material as WindowType).u_value} W/m²K
                              </p>
                              <p style={{ margin: "3px 0" }}>
                                <strong>SHGC:</strong> {(material as WindowType).shgc}
                              </p>
                              <p style={{ margin: "3px 0" }}>
                                <strong>Carbon:</strong> {(material as WindowType).carbon_kgCO2_per_m2} kg CO₂/m²
                              </p>
                            </>
                          ) : (
                            <>
                              <p style={{ margin: "3px 0" }}>
                                <strong>Conductivity:</strong> {(material as Material).conductivity_W_mK} W/mK
                              </p>
                              <p style={{ margin: "3px 0" }}>
                                <strong>R-Value:</strong> {(material as Material).r_value_m2K_W} m²K/W
                              </p>
                              <p style={{ margin: "3px 0" }}>
                                <strong>Carbon:</strong> {(material as Material).carbon_kgCO2_per_m2} kg CO₂/m²
                              </p>
                              <p style={{ margin: "3px 0" }}>
                                <strong>Density:</strong> {(material as Material).density_kg_m3} kg/m³
                              </p>
                            </>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => removeMaterial(material.id, activeTab)}
                        style={{
                          padding: "8px 12px",
                          borderRadius: "6px",
                          border: "none",
                          background: "#ef4444",
                          color: "#fff",
                          fontWeight: "600",
                          cursor: "pointer",
                          fontSize: "12px",
                        }}
                      >
                        🗑️ Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MaterialsAdmin;
