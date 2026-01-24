import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import "../styles/profile.css";

const Profile: React.FC = () => {
  const { user, token, refreshUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone_number ?? "");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return <div className="profile-loading">Loading...</div>;

  const startEdit = () => {
    setFullName(user.full_name ?? "");
    setPhone(user.phone_number ?? "");
    setPassword("");
    setError(null);
    setIsEditing(true);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setError(null);
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const body: any = { full_name: fullName, phone_number: phone };
      if (password) body.password = password;

      const res = await fetch(`${base}/auth/me`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setError(err.detail || "Failed to update profile");
        setLoading(false);
        return;
      }

      // refresh user data in context
      await refreshUser();
      setIsEditing(false);
    } catch (e) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2 className="profile-title">My Profile</h2>

        {!isEditing ? (
          <>
            <div className="profile-field">
              <span className="profile-label">Name:</span>
              <span className="profile-value">{user.full_name || "-"}</span>
            </div>
            <div className="profile-field">
              <span className="profile-label">Email:</span>
              <span className="profile-value">{user.email}</span>
            </div>
            <div className="profile-field">
              <span className="profile-label">Phone:</span>
              <span className="profile-value">{user.phone_number || "-"}</span>
            </div>
            <div className="profile-field">
              <span className="profile-label">Role:</span>
              <span className="profile-value">{user.role}</span>
            </div>
            <div style={{ marginTop: 12 }}>
              <button onClick={startEdit} className="btn-primary">
                Edit Profile
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="profile-field">
              <span className="profile-label">Name:</span>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </div>
            <div className="profile-field">
              <span className="profile-label">Email:</span>
              <span className="profile-value">{user.email}</span>
            </div>
            <div className="profile-field">
              <span className="profile-label">Phone:</span>
              <input value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="profile-field">
              <span className="profile-label">New password:</span>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <div className="profile-error">{error}</div>}
            <div style={{ marginTop: 12 }}>
              <button onClick={handleSave} disabled={loading} className="btn-primary">
                {loading ? "Saving..." : "Save"}
              </button>
              <button onClick={cancelEdit} style={{ marginLeft: 8 }} className="btn-secondary">
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Profile;
