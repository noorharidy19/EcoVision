import React from "react";
import { useAuth } from "../context/AuthContext";
import "../styles/profile.css";

const Profile: React.FC = () => {
  const { user } = useAuth();
  if (!user) return <div className="profile-loading">Loading...</div>;
  return (
    <div className="profile-container">
      <div className="profile-card">
        <h2 className="profile-title">My Profile</h2>
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
      </div>
    </div>
  );
};

export default Profile;
