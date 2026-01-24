import React from "react";
import NotFound from "../pages/NotFound";
import { useAuth } from "../context/AuthContext";
import "../styles/requireRole.css";

type Props = {
  roles: string[]; // allowed roles
  children: React.ReactNode;
};

const RequireRole: React.FC<Props> = ({ roles, children }) => {
  const { user } = useAuth();

  // If no user or role is not allowed, show 404 inside wrapper
  if (!user) return <div className="role-wrapper"><NotFound /></div>;
  const role = (user.role || "").toLowerCase();
  const allowed = roles.map((r) => r.toLowerCase());
  if (!allowed.includes(role)) return <div className="role-wrapper"><NotFound /></div>;

  return <div className="role-wrapper">{children}</div>;
};

export default RequireRole;
