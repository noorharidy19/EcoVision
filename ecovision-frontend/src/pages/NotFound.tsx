import React from "react";
import { useNavigate } from "react-router-dom";
import "../styles/notfound.css";

const NotFound: React.FC = () => {
  const nav = useNavigate();
  return (
    <div className="nf-simple-root">
      <div className="nf-box">
        <div className="nf-badge">404</div>
        <h3 className="nf-heading">Page Not Found</h3>
        <p className="nf-text">Either the page doesn't exist or you don't have access.</p>

        <div className="nf-loader" aria-hidden>
          <div></div><div></div><div></div>
        </div>

        <div className="nf-actions">
          <button className="nf-btn" onClick={() => nav(-1)}>Go Back</button>
          <button className="nf-btn nf-cta" onClick={() => nav('/')}>Home</button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
