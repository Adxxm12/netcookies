import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

export default function UserDashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      navigate("/");
      return;
    }
    api.getMyOrders()
      .then((data) => setOrders(data.orders || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user, navigate]);

  if (!user) return null;

  const totalSpent = orders
    .filter((o) => o.status === "paid")
    .reduce((sum, o) => sum + (o.total_usd || 0), 0);

  return (
    <div style={{ minHeight: "100vh", background: "#080d19", padding: "30px 20px" }}>
      <div style={{ maxWidth: "900px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" }}>
          <div>
            <h1 style={{ color: "#fff", margin: 0 }}>📊 My Dashboard</h1>
            <p style={{ color: "#8b98ad", margin: "5px 0 0 0", fontSize: "13px" }}>{user.email}</p>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={() => navigate("/")} style={btnStyle}>← Home</button>
            <button onClick={signOut} style={btnStyle}>Logout</button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "30px" }}>
          <div style={statCard}>
            <div style={statLabel}>TOTAL ORDERS</div>
            <div style={statValue}>{orders.length}</div>
          </div>
          <div style={statCard}>
            <div style={statLabel}>PAID ORDERS</div>
            <div style={statValue}>{orders.filter((o) => o.status === "paid").length}</div>
          </div>
          <div style={statCard}>
            <div style={statLabel}>TOTAL SPENT</div>
            <div style={{ ...statValue, color: "#ffd43b" }}>${totalSpent.toFixed(2)}</div>
          </div>
        </div>

        <h2 style={{ color: "#fff", fontSize: "18px", marginBottom: "15px" }}>Order History</h2>
        {loading ? (
          <p style={{ color: "#8b98ad" }}>Loading...</p>
        ) : orders.length === 0 ? (
          <div style={{ background: "#0e1727", padding: "40px", borderRadius: "12px", textAlign: "center" }}>
            <p style={{ color: "#8b98ad" }}>No orders yet. Start shopping!</p>
            <button onClick={() => navigate("/")} style={{ ...btnStyle, marginTop: "15px", background: "#ffd43b", color: "#06101e" }}>
              Go Shopping
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {orders.map((order) => (
              <div key={order.order_id} style={orderCard}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "5px" }}>
                    <strong style={{ color: "#fff" }}>{order.order_id}</strong>
                    <span style={statusBadge(order.status)}>{order.status.toUpperCase()}</span>
                  </div>
                  <p style={{ color: "#8b98ad", fontSize: "12px", margin: 0 }}>
                    {order.items?.map((i) => `${i.quantity}x ${i.plan}`).join(", ")}
                  </p>
                  <p style={{ color: "#6e7b91", fontSize: "11px", margin: "4px 0 0 0" }}>
                    {new Date(order.created_at).toLocaleString("en-MY")}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "#ffd43b", fontWeight: "bold" }}>${order.total_usd?.toFixed(2)}</div>
                  <div style={{ color: "#6e7b91", fontSize: "11px" }}>RM {order.total_myr?.toFixed(2)}</div>
                  {order.status === "paid" && order.redemption_url && (
                    <button
                      onClick={() => window.open(order.redemption_url, "_blank")}
                      style={{ ...btnStyle, marginTop: "8px", padding: "8px 12px", fontSize: "11px", background: "#4d91ff", color: "#fff" }}
                    >
                      Open Netflix ↗
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const btnStyle = {
  padding: "10px 16px", borderRadius: "8px", cursor: "pointer",
  background: "transparent", color: "#fff",
  border: "1px solid rgba(255,255,255,0.15)", fontWeight: "bold", fontSize: "12px"
};
const statCard = {
  background: "#0e1727", padding: "20px", borderRadius: "12px",
  border: "1px solid rgba(255,255,255,0.08)", textAlign: "center"
};
const statLabel = {
  color: "#6e7b91", fontSize: "10px", fontWeight: 800, letterSpacing: "1px"
};
const statValue = {
  color: "#fff", fontSize: "24px", fontWeight: "bold", marginTop: "5px"
};
const orderCard = {
  background: "#0e1727", padding: "18px", borderRadius: "12px",
  border: "1px solid rgba(255,255,255,0.08)",
  display: "flex", justifyContent: "space-between", alignItems: "center", gap: "15px"
};
const statusBadge = (status) => ({
  padding: "3px 8px", borderRadius: "5px", fontSize: "9px", fontWeight: "bold",
  background: status === "paid" ? "rgba(53,214,145,0.15)" : status === "pending" ? "rgba(255,212,59,0.15)" : "rgba(255,91,91,0.15)",
  color: status === "paid" ? "#55e2a1" : status === "pending" ? "#ffd43b" : "#ff7c7c",
});