import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { api } from "../services/api.js";

export default function AdminDashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [s, o] = await Promise.all([api.adminGetStats(), api.adminGetOrders()]);
        setStats(s);
        setOrders(o.orders || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#080d19", padding: "30px 20px" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
        
        {/* HEADER */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px", flexWrap: "wrap", gap: "15px" }}>
          <div>
            <h1 style={{ color: "#fff", margin: 0 }}>👑 Admin Dashboard</h1>
            <p style={{ color: "#8b98ad", margin: "5px 0 0 0", fontSize: "13px" }}>
              NetCookies Control Panel {user?.email ? `- ${user.email}` : ""}
            </p>
          </div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={() => navigate("/")} style={btnStyle}>← Home</button>
            <button onClick={signOut} style={{ ...btnStyle, color: "#ff7c7c" }}>Logout</button>
          </div>
        </div>

        {/* STATS CARDS */}
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "12px", marginBottom: "30px" }}>
            <div style={statCard}>
              <div style={statLabel}>REVENUE TODAY</div>
              <div style={{ ...statValue, color: "#55e2a1" }}>${stats.revenue_today_usd?.toFixed(2) || "0.00"}</div>
              <div style={statSub}>RM {stats.revenue_today_myr?.toFixed(2) || "0.00"}</div>
            </div>
            <div style={statCard}>
              <div style={statLabel}>REVENUE THIS MONTH</div>
              <div style={{ ...statValue, color: "#4d91ff" }}>${stats.revenue_month_usd?.toFixed(2) || "0.00"}</div>
              <div style={statSub}>RM {stats.revenue_month_myr?.toFixed(2) || "0.00"}</div>
            </div>
            <div style={statCard}>
              <div style={statLabel}>TOTAL REVENUE</div>
              <div style={{ ...statValue, color: "#ffd43b" }}>${stats.revenue_total_usd?.toFixed(2) || "0.00"}</div>
              <div style={statSub}>RM {stats.revenue_total_myr?.toFixed(2) || "0.00"}</div>
            </div>
          </div>
        )}

        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "12px", marginBottom: "30px" }}>
            <div style={statCard}>
              <div style={statLabel}>TOTAL ORDERS</div>
              <div style={statValue}>{stats.total_orders || 0}</div>
            </div>
            <div style={statCard}>
              <div style={statLabel}>PAID</div>
              <div style={{ ...statValue, color: "#55e2a1" }}>{stats.paid_orders || 0}</div>
            </div>
            <div style={statCard}>
              <div style={statLabel}>PENDING</div>
              <div style={{ ...statValue, color: "#ffd43b" }}>{stats.pending_orders || 0}</div>
            </div>
          </div>
        )}

        {/* PLAN POPULARITY */}
        {stats && stats.plan_popularity && Object.keys(stats.plan_popularity).length > 0 && (
          <div style={{ background: "#0e1727", padding: "20px", borderRadius: "12px", marginBottom: "30px" }}>
            <h3 style={{ color: "#fff", fontSize: "14px", marginBottom: "15px" }}>📊 Plan Popularity</h3>
            <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
              {Object.entries(stats.plan_popularity).map(([plan, count]) => (
                <div key={plan} style={{ background: "#0d1525", padding: "12px 20px", borderRadius: "8px" }}>
                  <span style={{ color: "#8b98ad", fontSize: "11px" }}>{plan}</span>
                  <span style={{ color: "#fff", fontWeight: "bold", marginLeft: "10px" }}>{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* RECENT ORDERS */}
        <h2 style={{ color: "#fff", fontSize: "18px", marginBottom: "15px" }}>Recent Orders</h2>
        {loading ? (
          <p style={{ color: "#8b98ad" }}>Loading...</p>
        ) : orders.length === 0 ? (
          <p style={{ color: "#8b98ad" }}>No orders yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {orders.slice(0, 20).map((order) => (
              <div key={order.order_id} style={orderCard}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center", marginBottom: "5px", flexWrap: "wrap" }}>
                    <strong style={{ color: "#fff" }}>{order.order_id}</strong>
                    <span style={statusBadge(order.status)}>{order.status.toUpperCase()}</span>
                  </div>
                  <p style={{ color: "#8b98ad", fontSize: "12px", margin: 0 }}>
                    {order.user_email} · {order.items?.map((i) => `${i.quantity}x ${i.plan}`).join(", ")}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "#ffd43b", fontWeight: "bold" }}>${order.total_usd?.toFixed(2) || "0.00"}</div>
                  <div style={{ color: "#6e7b91", fontSize: "11px" }}>RM {order.total_myr?.toFixed(2) || "0.00"}</div>
                  {order.status === "paid" && (
                    <button
                      onClick={async () => {
                        if (!confirm("Revoke this order?")) return;
                        await api.adminRevoke(order.order_id);
                        setOrders(orders.map((o) => o.order_id === order.order_id ? { ...o, status: "revoked", redemption_url: null } : o));
                      }}
                      style={{ ...btnStyle, marginTop: "8px", padding: "6px 10px", fontSize: "10px", color: "#ff7c7c" }}
                    >
                      Revoke
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
const statSub = {
  color: "#6e7b91", fontSize: "11px", marginTop: "3px"
};
const orderCard = {
  background: "#0e1727", padding: "18px", borderRadius: "12px",
  border: "1px solid rgba(255,255,255,0.08)",
  display: "flex", justifyContent: "space-between", alignItems: "center", gap: "15px",
  flexWrap: "wrap"
};
const statusBadge = (status) => ({
  padding: "3px 8px", borderRadius: "5px", fontSize: "9px", fontWeight: "bold",
  background: status === "paid" ? "rgba(53,214,145,0.15)" : status === "pending" ? "rgba(255,212,59,0.15)" : "rgba(255,91,91,0.15)",
  color: status === "paid" ? "#55e2a1" : status === "pending" ? "#ffd43b" : "#ff7c7c",
});