import { useState } from "react";
import "../styles/signup.css";

const Signup = () => {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [errors, setErrors] = useState<any>({});

  const handlePhoneChange = (value: string) => {
  // allow only numbers
  const digitsOnly = value.replace(/\D/g, "");

  // prevent leading zero
  if (digitsOnly.startsWith("0")) return;

  // max 10 digits
  if (digitsOnly.length <= 10) {
    setPhone(digitsOnly);
  }
};


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: any = {};

    // Full name
    if (!fullName) {
      newErrors.fullName = "Full name is required";
    }

    // Phone
    // Phone (Egyptian number validation)
if (!phone) {
  newErrors.phone = "Phone number is required";
} else if (!/^[1-9][0-9]{9}$/.test(phone)) {
  newErrors.phone = "Enter a valid Egyptian phone number (10 digits only)";
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
      try {
        // truncate password to 72 bytes to match bcrypt limit
        const pwBytes = new TextEncoder().encode(password);
        let sendPassword = password;
        if (pwBytes.length > 72) {
          // truncate and decode safely
          const truncated = pwBytes.slice(0, 72);
          sendPassword = new TextDecoder().decode(truncated);
        }

        const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
        const res = await fetch(`${base}/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: fullName,
            phone_number: "+20" + phone,
            email,
            password: sendPassword,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setErrors({ form: err.detail || "Signup failed" });
          return;
        }

        // success — redirect or show message
        console.log("Signup created");
        window.location.href = "/login";
      } catch (err) {
        setErrors({ form: "Network error" });
      }
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

<div className="phone-input-wrapper">
  <div className="phone-prefix">
    <img src="/src/assets/egypt.png" alt="Egypt" className="flag-icon" />
    <span>+20</span>
  </div>

  <input
  type="text"
  placeholder="1001231765"
  value={phone}
  onChange={(e) => handlePhoneChange(e.target.value)}
/>

</div>

{errors.phone && <span className="input-error">{errors.phone}</span>}



          <label>Email</label>
          <input
            type="text"
            placeholder="architect@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {errors.email && <span className="input-error">{errors.email}</span>}

          <label>Password</label>
          <input
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {errors.password && <span className="input-error">{errors.password}</span>}

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

          {errors.form && <div className="input-error">{errors.form}</div>}

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
