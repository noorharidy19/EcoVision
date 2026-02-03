import React from "react";
import "../styles/dashboard.css";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logoImg from "../assets/eco.jpeg"; // تأكدي من حفظ اللوجو المعدل بهذا الاسم

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const goCreate = () => {
    if (user) navigate("/createproject");
    else navigate("/login");
  };

  const goMyProjects = () => {
    if (user) navigate("/myprojects");
    else navigate("/login");
  };

  return (
    <div className="arch-page">
      {/* HERO SECTION */}
      <section className="hero">
        <div className="hero-text">
          <h1>
            EcoVision <span>AI Architecture</span>
          </h1>
          <h3>Sustainable Architecture Platform</h3>
          <p>
            Design smarter buildings using AI-powered 2D analysis,
            sustainability insights, and intelligent material selection.
          </p>

          <div className="hero-buttons">
            <button className="primary-btn" onClick={goCreate}>Start New Project</button>
            <button className="secondary-btn" onClick={goMyProjects}>View My Projects</button>
          </div>
        </div>

        {/* الحاوية الجديدة للوجو المعدل */}
        <div className="hero-image-logo">
          <img 
            src={logoImg} 
            alt="EcoVision AI" 
            className="main-dashboard-logo" 
            
          />
        </div>
      </section>

      {/* FEATURES SECTION */}
     <section className="features">
  {/* كارت 1 */}
  <div className="feature-card">
    <div className="card-inner">
      <div className="card-front">
        <h4>2D Plan Analysis</h4>
        <p>AI intelligent floor-plan explaination.</p>
      </div>
      <div className="card-back">
        <h4>How it works?</h4>
        <p>Our AI parses DWG/DXF files to identify rooms, walls, and structural elements.</p>
      </div>
    </div>
  </div>

  {/* كارت 2 */}
  <div className="feature-card">
    <div className="card-inner">
      <div className="card-front">
        <h4>2D Modification</h4>
        <p>Intelligent editing tools.</p>
      </div>
      <div className="card-back">
        <h4>Design Freedom</h4>
        <p>Edit floor-plan based on Architect NLP commands.</p>
      </div>
    </div>
  </div>
  <div className="feature-card">
    <div className="card-inner">
      <div className="card-front">
         <h4>Sustainability Reports</h4>
          <p>Generate data-driven environmental reports.</p>
      </div>
      <div className="card-back">
        
        <p>Get insights on energy use, material impact, and eco-friendly design suggestions.</p>
      </div>
    </div>
  </div>
  <div className="feature-card">
    <div className="card-inner">
      <div className="card-front">
        <h4>AI Optimization</h4>
          <p>Improve comfort, energy, and material efficiency.</p>
      </div>
      <div className="card-back">
        
        <p>Leverage AI to optimize designs for sustainability and performance.</p>
      </div>
    </div>
  </div>
  

</section>
    </div>
  );
};

export default Dashboard;