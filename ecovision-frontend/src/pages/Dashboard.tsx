import "../styles/dashboard.css";

const Dashboard = () => {
  return (
    <div className="arch-page">

      {/* HERO */}
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
            <button className="primary-btn">Start New Project</button>
            <button className="secondary-btn">View My Projects</button>
          </div>
        </div>

        <div className="hero-image">
          <div className="mockup-card"></div>
          <div className="mockup-card second"></div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="features">
        <div className="feature-card">
          <h4>2D Plan Analysis</h4>
          <p>Upload floor plans and extract spatial intelligence.</p>
        </div>

         <div className="feature-card">
          <h4>2D Plan Modification</h4>
          <p>Modify floor plans with intelligent editing tools.</p>
        </div>

        <div className="feature-card">
          <h4>AI Optimization</h4>
          <p>Improve comfort, energy, and material efficiency.</p>
        </div>

        <div className="feature-card">
          <h4>Sustainability Reports</h4>
          <p>Generate data-driven environmental reports.</p>
        </div>
      </section>

    </div>
  );
};

export default Dashboard;
