import { useState } from "react";
import "../styles/signup.css";

const Signup = () => {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [errors, setErrors] = useState<any>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: any = {};

    // Full name
    if (!fullName) {
      newErrors.fullName = "Full name is required";
    }

    // Phone
    if (!phone) {
      newErrors.phone = "Phone number is required";
    }

    // Email
    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Invalid email format";
    }

    // Password
    if (!password) {
      newErrors.password = "Password is required";
    }

    // Confirm password
    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      console.log("Signup success");
      // later → API call
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-card">
        <h1 className="signup-title">EcoVision</h1>
        <p className="signup-subtitle">Create your architect account</p>

        <form className="signup-form" onSubmit={handleSubmit} noValidate>
          <label>Full Name</label>
          <input
            type="text"
            placeholder="Your full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          {errors.fullName && (
            <span className="input-error">{errors.fullName}</span>
          )}

          <label>Phone Number</label>
          <input
            type="text"
            placeholder="Your phone number"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          {errors.phone && (
            <span className="input-error">{errors.phone}</span>
          )}

          <label>Email</label>
          <input
            type="text"   
            placeholder="architect@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {errors.email && (
            <span className="input-error">{errors.email}</span>
          )}

          <label>Password</label>
          <input
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {errors.password && (
            <span className="input-error">{errors.password}</span>
          )}

          <label>Confirm Password</label>
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {errors.confirmPassword && (
            <span className="input-error">{errors.confirmPassword}</span>
          )}

          <button type="submit">Sign Up</button>
        </form>

        <p className="signup-footer">
          © EcoVision
          <br />
          already have an account? <a href="/login">Login</a>
        </p>
      </div>
    </div>
  );
};

export default Signup;
