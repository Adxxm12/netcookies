import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    
    // TODO: Verify dengan Supabase auth + check owner ID
    // Contoh ringkas:
    if (email === "admin@netcookies.store" && password === "admin123") {
      localStorage.setItem("admin_token", "dummy_admin_token");
      navigate("/admin/dashboard");
    } else {
      setError("Invalid credentials");
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#080d19", padding: "20px" }}>
      <form onSubmit={handleLogin} style={{ background: "#101a2c", padding: "40px", borderRadius: "16px", width: "100%", maxWidth: "400px", border: "1px solid rgba(77,145,255,0.3)" }}>
        <h1 style={{ color: "#fff", marginBottom: "10px", fontSize: "24px" }}>🔐 Admin Login</h1>
        <p style={{ color: "#8b98ad", fontSize: "12px", marginBottom: "25px" }}>Restricted area.</p>
        
        {error && <div style={{ color: "#ff7c7c", fontSize: "12px", marginBottom: "15px" }}>{error}</div>}
        
        <label style={{ color: "#8b98ad", fontSize: "11px", fontWeight: 800 }}>EMAIL</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
          style={{ width: "100%", padding: "12px", marginTop: "6px", marginBottom: "15px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.1)", background: "#0d1525", color: "#fff" }} />
        
        <label style={{ color: "#8b98ad", fontSize: "11px", fontWeight: 800 }}>PASSWORD</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
          style={{ width: "100%", padding: "12px", marginTop: "6px", marginBottom: "20px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.1)", background: "#0d1525", color: "#fff" }} />
        
        <button type="submit" disabled={loading}
          style={{ width: "100%", padding: "14px", borderRadius: "8px", background: "#ffd43b", color: "#06101e", border: "none", fontWeight: "bold", cursor: "pointer" }}>
          {loading ? "Loading..." : "Login"}
        </button>
      </form>
    </div>
  );
}