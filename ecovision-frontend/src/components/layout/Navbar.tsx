import "../../styles/navbar.css";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="navbar">
      {/* Logo */}
      <div className="nav-logo">
        Eco<span>Vision</span>
      </div>

      {/* Links */}
      <nav className="nav-links">
        <Link to="/">Dashboard</Link>
        {user ? (
          <>
            <Link to="/profile">{user.full_name ? user.full_name : "Profile"}</Link>
            <button className="nav-logout" onClick={handleLogout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup">Sign Up</Link>
          </>
        )}
      </nav>
    </header>
  );
};

export default Navbar;
