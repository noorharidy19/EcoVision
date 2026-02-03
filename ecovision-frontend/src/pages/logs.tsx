import "../styles/adminService.css";
import { useEffect, useState } from "react";

interface ActivityLog {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  details: string | null;
  ip_address: string | null;
  timestamp: string;
}

export default function Logs() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/logs/", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error("Failed to fetch logs");

      const data = await response.json();
      setLogs(data);
    } catch (err) {
      console.error("Error fetching logs:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => 
    log.user_name.toLowerCase().includes(filter.toLowerCase()) ||
    log.user_email.toLowerCase().includes(filter.toLowerCase()) ||
    log.action.toLowerCase().includes(filter.toLowerCase())
  );

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getActionColor = (action: string) => {
    if (action.includes("create")) return "#4CAF50";
    if (action.includes("delete")) return "#f44336";
    if (action.includes("update")) return "#2196F3";
    if (action.includes("login")) return "#9C27B0";
    if (action.includes("signup")) return "#FF9800";
    return "#666";
  };

  const getActionLabel = (action: string) => {
    const labels: { [key: string]: string } = {
      "login": "Logged In",
      "signup": "Signed Up",
      "create_project": "Created Project",
      "update_project": "Updated Project",
      "delete_project": "Deleted Project",
      "logout": "Logged Out"
    };
    return labels[action] || action;
  };

  const getActivityDescription = (log: ActivityLog) => {
    const time = formatDate(log.timestamp);
    const action = getActionLabel(log.action);
    
    switch(log.action) {
      case "login":
        return `${log.user_name} logged in at ${time}`;
      case "signup":
        return `${log.user_name} created a new account at ${time}`;
      case "create_project":
        return `${log.user_name} created project "${log.details?.replace('Created project: ', '')}" at ${time}`;
      case "update_project":
        return `${log.user_name} updated project "${log.details?.replace('Updated project: ', '')}" at ${time}`;
      case "delete_project":
        return `${log.user_name} deleted project "${log.details?.replace('Deleted project: ', '')}" at ${time}`;
      default:
        return `${log.user_name} performed ${action} at ${time}`;
    }
  };

  return (
    <div className="page">
      <h1 className="title">System Logs - User Activity Timeline</h1>
      
      <div className="card large" style={{ marginBottom: "20px" }}>
        <input 
          type="text"
          placeholder="Search by user name, email, or action..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            width: "100%",
            padding: "12px",
            fontSize: "14px",
            border: "1px solid #ddd",
            borderRadius: "4px",
            boxSizing: "border-box"
          }}
        />
      </div>

      <div className="card large">
        {loading ? (
          <p>Loading activity logs...</p>
        ) : (
          <>
            <div style={{ marginBottom: "20px" }}>
              <h3 style={{ fontSize: "16px", marginBottom: "10px" }}>Activity Summary</h3>
              <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
                <div style={{ padding: "10px 15px", backgroundColor: "#f5f5f5", borderRadius: "4px" }}>
                  <strong>Total Activities:</strong> {filteredLogs.length}
                </div>
                <div style={{ padding: "10px 15px", backgroundColor: "#e8f5e9", borderRadius: "4px" }}>
                  <strong>Logins:</strong> {filteredLogs.filter(l => l.action === "login").length}
                </div>
                <div style={{ padding: "10px 15px", backgroundColor: "#e3f2fd", borderRadius: "4px" }}>
                  <strong>Projects Created:</strong> {filteredLogs.filter(l => l.action === "create_project").length}
                </div>
                <div style={{ padding: "10px 15px", backgroundColor: "#ffebee", borderRadius: "4px" }}>
                  <strong>Projects Deleted:</strong> {filteredLogs.filter(l => l.action === "delete_project").length}
                </div>
              </div>
            </div>

            <h3 style={{ fontSize: "16px", marginBottom: "15px" }}>Recent Activities</h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#f5f5f5", textAlign: "left" }}>
                    <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Time</th>
                    <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>User</th>
                    <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Action</th>
                    <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>Activity Description</th>
                    <th style={{ padding: "12px", borderBottom: "2px solid #ddd" }}>IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ padding: "20px", textAlign: "center", color: "#999" }}>
                        No activity logs found. User actions will appear here.
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map((log) => (
                      <tr key={log.id} style={{ borderBottom: "1px solid #eee" }}>
                        <td style={{ padding: "12px", fontSize: "13px", whiteSpace: "nowrap" }}>
                          {formatDate(log.timestamp)}
                        </td>
                        <td style={{ padding: "12px" }}>
                          <div style={{ fontWeight: "500" }}>{log.user_name}</div>
                          <div style={{ fontSize: "12px", color: "#666" }}>{log.user_email}</div>
                        </td>
                        <td style={{ padding: "12px" }}>
                          <span style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontWeight: "500",
                            backgroundColor: getActionColor(log.action) + "20",
                            color: getActionColor(log.action)
                          }}>
                            {getActionLabel(log.action)}
                          </span>
                        </td>
                        <td style={{ padding: "12px", fontSize: "13px" }}>
                          {getActivityDescription(log)}
                        </td>
                        <td style={{ padding: "12px", fontSize: "13px", color: "#666" }}>
                          {log.ip_address || "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
