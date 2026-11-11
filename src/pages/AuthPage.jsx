import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function AuthPage({ onBack }) {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (mode === "login") {
        await signIn(email, password);
        // Redirect ke homepage selepas login
        navigate("/");
      } else {
        await signUp(email, password);
        setMessage("✅ Account created! Please login.");
        setMode("login");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "grid", placeItems: "center",
      background: "#080d19", padding: "20px"
    }}>
      <div style={{
        background: "#101a2c", padding: "40px", borderRadius: "16px",
        width: "100%", maxWidth: "420px",
        border: "1px solid rgba(77,145,255,0.2)"
      }}>
        <h2 style={{ color: "#fff", marginBottom: "8px" }}>
          {mode === "login" ? "Login" : "Register"}
        </h2>
        <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "25px" }}>
          {mode === "login"
            ? "Sign in to claim or buy Netflix accounts."
            : "Create a free account to get started."}
        </p>

        <form onSubmit={handleSubmit}>
          <label style={labelStyle}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={inputStyle}
              placeholder="you@email.com"
            />
          </label>

          <label style={labelStyle}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              style={inputStyle}
              placeholder="Minimum 6 characters"
            />
          </label>

          {error && (
            <p style={{ color: "#ff7c7c", fontSize: "12px", marginBottom: "12px" }}>
              ❌ {error}
            </p>
          )}
          {message && (
            <p style={{ color: "#55e2a1", fontSize: "12px", marginBottom: "12px" }}>
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%", padding: "14px", borderRadius: "8px",
              background: "#ffd43b", color: "#06101e", border: "none",
              fontWeight: "bold", cursor: "pointer", marginTop: "10px",
              fontSize: "14px"
            }}
          >
            {loading ? "⏳ Loading..." : mode === "login" ? "Login" : "Register"}
          </button>
        </form>

        <p style={{ color: "#8b98ad", fontSize: "13px", textAlign: "center", marginTop: "20px" }}>
          {mode === "login" ? "No account yet? " : "Already have an account? "}
          <button
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); setMessage(""); }}
            style={{
              background: "none", border: "none", color: "#4d91ff",
              cursor: "pointer", fontWeight: "bold", padding: 0
            }}
          >
            {mode === "login" ? "Register" : "Login"}
          </button>
        </p>

        <button
          onClick={onBack}
          style={{
            width: "100%", padding: "10px", marginTop: "15px",
            background: "transparent", color: "#8b98ad",
            border: "1px solid rgba(255,255,255,0.15)", borderRadius: "8px",
            cursor: "pointer", fontSize: "12px"
          }}
        >
          ← Back
        </button>
      </div>
    </div>
  );
}

const labelStyle = {
  display: "block", color: "#aebbd0", fontSize: "12px",
  fontWeight: 700, marginBottom: "15px"
};
const inputStyle = {
  display: "block", width: "100%", padding: "12px", marginTop: "8px",
  borderRadius: "8px", border: "1px solid rgba(255,255,255,0.15)",
  background: "#0d1525", color: "#fff", fontSize: "14px",
  boxSizing: "border-box"
};