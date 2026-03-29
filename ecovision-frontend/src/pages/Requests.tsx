import "../styles/requests.css";
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

interface AccessRequest {
  id: number;
  requester_id: number;
  requester_name: string;
  status: "PENDING" | "ACCEPTED" | "DECLINED";
  created_at: string;
  responded_at: string | null;
}

interface Notification {
  message: string;
  type: "success" | "error" | "info";
  details?: string;
}

interface CollaboratorInfo {
  name: string;
  role: string;
  status: string;
}

const ProjectRequests = () => {
  const { id } = useParams<{ id: string }>();
  const projectId = id ? parseInt(id, 10) : null;
  const navigate = useNavigate();
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
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
    if (!token) {
      navigate("/login");
      return;
    }

    if (!projectId) {
      showNotification("Invalid project ID", "error");
      navigate("/myprojects");
      return;
    }

    setLoading(true);
    fetch(`http://127.0.0.1:8000/projects/${projectId}/requests`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch requests");
        return res.json();
      })
      .then((data) => setRequests(data))
      .catch((err) => {
        console.error(err);
        showNotification("Failed to load requests", "error");
      })
      .finally(() => setLoading(false));
  }, [projectId, navigate]);

  const handleRequest = async (
    requestId: number,
    action: "approve" | "decline"
  ) => {
    if (!projectId) {
      showNotification("Invalid project ID", "error");
      return;
    }

    const token = localStorage.getItem("token");

    try {
      const url = `http://127.0.0.1:8000/projects/${projectId}/requests/${requestId}/${action}`;
      console.log(`Calling: ${url}`);
      
      const res = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      console.log(`Response status: ${res.status}`);
      const responseData = await res.json();
      console.log(`Response data:`, responseData);

      if (res.ok) {
        const updatedRequest = requests.find((r) => r.id === requestId);
        setRequests((prev) =>
          prev.map((r) =>
            r.id === requestId
              ? {
                  ...r,
                  status: action === "approve" ? "ACCEPTED" : "DECLINED",
                  responded_at: new Date().toISOString(),
                }
              : r
          )
        );
        
        if (action === "approve" && updatedRequest) {
          showNotification(
            `${updatedRequest.requester_name} is now a collaborator!`,
            "success"
          );
        } else {
          showNotification(
            `Request ${action === "approve" ? "approved" : "declined"} successfully`,
            "success"
          );
        }
      } else {
        showNotification(
          `Failed to ${action} request: ${responseData.detail || res.statusText}`,
          "error"
        );
        console.error(`Error ${action}ing request:`, responseData);
      }
    } catch (err) {
      console.error("Error processing request:", err);
      showNotification("Error processing request", "error");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const pendingRequests = requests.filter((r) => r.status === "PENDING");
  const respondedRequests = requests.filter((r) => r.status !== "PENDING");

  return (
    <div className="requests-container">
      {notification && (
        <div className={`notification ${notification.type}`}>
          <div className="notification-message">{notification.message}</div>
          {notification.details && (
            <div className="notification-details">{notification.details}</div>
          )}
        </div>
      )}

      <div className="requests-header">
        <h1>Project Access Requests</h1>
        <button className="back-btn" onClick={() => navigate("/myprojects")}>
          ← Back
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading requests...</div>
      ) : requests.length === 0 ? (
        <div className="no-requests">
          <p>No access requests yet</p>
        </div>
      ) : (
        <>
          {pendingRequests.length > 0 && (
            <div className="requests-section">
              <h2 className="section-title">Pending Requests</h2>
              <div className="requests-list">
                {pendingRequests.map((req) => (
                  <div key={req.id} className="request-card pending">
                    <div className="request-info">
                      <h3>{req.requester_name}</h3>
                      <p className="request-date">
                        Requested: {formatDate(req.created_at)}
                      </p>
                    </div>
                    <div className="request-actions">
                      <button
                        className="btn-approve"
                        onClick={() => handleRequest(req.id, "approve")}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn-decline"
                        onClick={() => handleRequest(req.id, "decline")}
                      >
                        ✕ Decline
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {respondedRequests.length > 0 && (
            <div className="requests-section">
              <h2 className="section-title">Response History</h2>
              <div className="requests-list">
                {respondedRequests.map((req) => (
                  <div key={req.id} className={`request-card ${req.status.toLowerCase()}`}>
                    <div className="request-info">
                      <h3>{req.requester_name}</h3>
                      <p className="request-date">
                        Responded: {formatDate(req.responded_at || req.created_at)}
                      </p>
                      {req.status === "ACCEPTED" && (
                        <div className="collaborator-info">
                          <p className="collaborator-label">✓ Collaborator - COLLABORATOR Role</p>
                          <p className="collaborator-note">Can open & view project designs and run analysis</p>
                        </div>
                      )}
                    </div>
                    <div className="request-status">
                      <span className={`status-badge ${req.status.toLowerCase()}`}>
                        {req.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ProjectRequests;