import React from "react";
import NotFound from "../pages/NotFound";
import { useAuth } from "../context/AuthContext";

type Props = {
  children: React.ReactNode;
};

const RequireNonAdmin: React.FC<Props> = ({ children }) => {
  const { user } = useAuth();

  // If user is signed in and is admin, show 404
  if (user && (user.role || "").toLowerCase() === "admin") {
    return <NotFound />;
  }

  // Otherwise allow (including anonymous visitors)
  return <>{children}</>;
};

export default RequireNonAdmin;
