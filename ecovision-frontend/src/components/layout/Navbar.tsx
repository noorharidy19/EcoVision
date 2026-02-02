import "../../styles/navbar.css";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import navImage from "../../assets/nav.jpeg";

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
        <img 
          src={navImage} 
          alt="EcoVision Logo" 
          style={{ 
            height: "50px", 
            marginRight: "10px",
            
          }} 
        />
        <span style={{ display: "flex" }}><span style={{ color: "#0f172a" }}>Eco</span><span>Vision</span></span>
      </div>

      {/* Links */}
      <nav className="nav-links">
        <Link to={user && user.role && user.role.toLowerCase() === "admin" ? "/admin" : "/"}>Dashboard</Link>
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
