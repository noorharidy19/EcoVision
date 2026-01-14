import "../../styles/navbar.css";
import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <header className="navbar">
      {/* Logo */}
      <div className="nav-logo">
        Eco<span>Vision</span>
      </div>

      {/* Links */}
      <nav className="nav-links">
        <Link to="/">Dashboard</Link>
        <Link to="/login">Login</Link>
        <Link to="/signup">Sign Up</Link>
        {/* Hidden for now 
        <Link to="/profile" className="hidden-link">My Profile</Link>
        <Link to="/" className="hidden-link">Logout</Link>
        */}
      </nav>
    </header>
  );
};

export default Navbar;
