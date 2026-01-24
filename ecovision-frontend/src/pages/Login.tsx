import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "../styles/login.css";

const Login = () => {
  const navigate = useNavigate();
  const auth = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    let valid = true;

    setEmailError("");
    setPasswordError("");

    // Email validation
    if (!email) {
      setEmailError("Email is required");
      valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError("Invalid email format");
      valid = false;
    }

    // Password validation
    if (!password) {
      setPasswordError("Password is required");
      valid = false;
    }

    if (valid) {
      try {
        // login via auth context
        const pwBytes = new TextEncoder().encode(password);
        let sendPassword = password;
        if (pwBytes.length > 72) {
          const truncated = pwBytes.slice(0, 72);
          sendPassword = new TextDecoder().decode(truncated);
        }
        await auth.login(email, sendPassword);
        navigate("/profile");
      } catch (err) {
        setPasswordError("Login failed");
      }
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">EcoVision</h1>
        <p className="login-subtitle">
          AI-powered Sustainable Architecture Platform
        </p>

        {/* 🚫 منع validation الافتراضي */}
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <label>Email</label>
          <input
            type="text"  
            placeholder="architect@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {emailError && <span className="input-error">{emailError}</span>}

          <label>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {passwordError && (
            <span className="input-error">{passwordError}</span>
          )}

          <button type="submit">Login</button>
        </form>

        <p className="login-footer">
          © EcoVision
          <br />
          no account? <a href="/signup">Sign Up</a>
        </p>
      </div>
    </div>
  );
};

export default Login;
