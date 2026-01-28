import React from "react";
import { Link } from "react-router-dom";
import "../styles/Admin.css";

type AdminCard = {
  title: string;
  description: string;
  action: string;
  path: string;
};

const cards: AdminCard[] = [
  {
    title: "Manage Users",
    description: "Add, edit, delete users and assign admin roles.",
    action: "Open",
    path: "/users",
  },
  {
    title: "Projects",
    description: "View all existing projects and their status.",
    action: "View",
    path: "/admin/projects",
  },
  {
    title: "AI Models",
    description: "Control AI models, versions, and configurations.",
    action: "Edit",
    path: "/ai-models",
  },
  {
    title: "Materials",
    description: "Manage sustainable materials database.",
    action: "Manage",
    path: "/materials",
  },
  {
    title: "System Logs",
    description: "View user activity and system logs.",
    action: "View Logs",
    path: "/logs",
  },
];
const AdminDashboard: React.FC = () => {
  return (
    <div className="admin-page">
      <h2 className="admin-title">Admin Dashboard</h2>

      <div className="admin-cards">
        {cards.map((card, index) => (
          <div className="admin-card" key={index}>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
            <Link to={card.path} className="admin-btn">
              {card.action}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdminDashboard;

