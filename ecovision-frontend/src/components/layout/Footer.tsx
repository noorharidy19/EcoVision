import "../../styles/footer.css";
import { useNavigate } from "react-router-dom";
import {useAuth} from "../../context/AuthContext";

const Footer = () => {

 const { user } = useAuth();
 const navigate = useNavigate();

   const handleProtectedClick = (path: string) => {
    if (!user) {
      navigate("/login");
    } else {
      navigate(path);
    }
  };

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-section">
          <h3 className="footer-logo">Eco<span>Vision</span></h3>
          <p className="footer-description">
            Transform your architectural designs with AI-powered sustainable solutions.
          </p>
        </div>

        <div className="footer-section">
          <h4>Quick Links</h4>
          <ul className="footer-links">
            <li>
              <button onClick={() => handleProtectedClick("/")}>
                Dashboard
              </button>
            </li>
            <li>
              <button onClick={() => handleProtectedClick("/myprojects")}>
                My Projects
              </button>
            </li>
            <li>
              <button onClick={() => handleProtectedClick("/createproject")}>
                Create Project
              </button>
            </li>
          </ul>
        </div>

        <div className="footer-section">
          <h4>Support</h4>
          <ul className="footer-links">
             <li>
              <button onClick={() => handleProtectedClick("/profile")}>
                Profile
              </button>
            </li>
            <li><a href="#">Help Center</a></li>
            <li><a href="#">Contact Us</a></li>
          </ul>
        </div>

        <div className="footer-section">
          <h4>Connect</h4>
          <div className="footer-social">
            <a href="#" aria-label="Facebook">Facebook</a>
            <a href="#" aria-label="Twitter">Twitter</a>
            <a href="#" aria-label="LinkedIn">LinkedIn</a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; {new Date().getFullYear()} EcoVision. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;