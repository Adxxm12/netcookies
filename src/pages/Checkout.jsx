import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext.jsx";
import { api } from "../services/api.js";

export default function Checkout() {
  const { cart, clearCart } = useCart();
  const navigate = useNavigate();

  const [order, setOrder] = useState(null);
  const [status, setStatus] = useState("creating"); // creating | pending | paid | error
  const [error, setError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);

  const createdRef = useRef(false);

  // Create order ONCE
  useEffect(() => {
    if (createdRef.current) return;

    if (cart.length === 0) {
      navigate("/dashboard");
      return;
    }

    createdRef.current = true;

    const createOrder = async () => {
      try {
        const items = cart.map((item) => ({
          plan: String(item.plan || "Unknown"),
          quantity: Number(item.quantity) || 1,
          price_usd: Number(item.price) || 0,
        }));

        console.log("Sending checkout items:", items);

        const data = await api.checkout(items);
        setOrder(data);
        setStatus("pending");
        clearCart();
      } catch (err) {
        console.error("Checkout error:", err);
        setError(err.message || "Unknown error");
        setStatus("error");
      }
    };

    createOrder();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll status every 5 seconds
  useEffect(() => {
    if (!order || status !== "pending") return;

    const interval = setInterval(async () => {
      try {
        const data = await api.getOrderStatus(order.order_id);
        setElapsed(data.elapsed_seconds || 0);

        if (data.status === "paid") {
          setResult(data);
          setStatus("paid");
          clearInterval(interval);
        } else if (data.status === "revoked") {
          setError("This order has been revoked.");
          setStatus("error");
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [order, status]);

  // ==== LOADING ====
  if (status === "creating") {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={{ color: "#fff" }}>Creating order...</h2>
        </div>
      </div>
    );
  }

  // ==== ERROR ====
  if (status === "error") {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={{ color: "#ff7c7c" }}>⚠️ Error</h2>
          <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "20px" }}>{error}</p>
          <button onClick={() => navigate("/dashboard")} style={btnStyle}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ==== SUCCESS ====
  if (status === "paid") {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={{ color: "#55e2a1" }}>🎉 Success!</h2>
          <p style={{ color: "#8b98ad", marginBottom: "20px" }}>
            Your Netflix account is ready.
          </p>
          <div style={infoBox}>
            <div><strong style={labelStyle}>PLAN</strong><br />{result?.plan_delivered || "—"}</div>
            <div><strong style={labelStyle}>ORDER</strong><br />{result?.order_id || "—"}</div>
          </div>
          <div style={{ background: "#0d1525", padding: "15px", borderRadius: "8px", marginTop: "15px" }}>
            <p style={{ color: "#8b98ad", fontSize: "11px", marginBottom: "8px" }}>NETFLIX LINK</p>
            <p style={{ color: "#4d91ff", fontSize: "12px", wordBreak: "break-all" }}>
              {result?.redemption_url || "—"}
            </p>
          </div>
          <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
            <button
              onClick={() => {
                if (result?.redemption_url) {
                  navigator.clipboard.writeText(result.redemption_url);
                  alert("Copied!");
                }
              }}
              style={{ ...btnStyle, flex: 1 }}
            >
              📋 Copy Link
            </button>
            <button
              onClick={() => {
                if (result?.redemption_url) window.open(result.redemption_url, "_blank");
              }}
              style={{ ...btnStyle, flex: 1, background: "#ffd43b", color: "#06101e" }}
            >
              Open Netflix ↗
            </button>
          </div>
          <button
            onClick={() => navigate("/dashboard")}
            style={{ ...btnStyle, marginTop: "10px", width: "100%" }}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ==== PENDING (QR) ====
  const remaining = Math.max(0, (order?.verify_in_seconds || 60) - elapsed);

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <h2 style={{ color: "#ffd43b" }}>💳 Complete Payment</h2>
        <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "20px" }}>
          Scan the QR below and pay{" "}
          <strong style={{ color: "#fff" }}>
            RM {order?.total_myr?.toFixed(2) || "0.00"}
          </strong>
        </p>

        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img
            src="/qr-gxbank.png"
            alt="Payment QR"
            style={{
              maxWidth: "250px",
              width: "100%",
              borderRadius: "12px",
              background: "#fff",
              padding: "10px",
            }}
            onError={(e) => {
              console.error("QR image failed to load");
              e.target.style.display = "none";
            }}
          />
        </div>

        <div style={infoBox}>
          <div>
            <strong style={labelStyle}>ORDER ID</strong>
            <br />
            {order?.order_id || "—"}
          </div>
          <div>
            <strong style={labelStyle}>AMOUNT</strong>
            <br />
            RM {order?.total_myr?.toFixed(2) || "0.00"} (${order?.total_usd?.toFixed(2) || "0.00"} USD)
          </div>
        </div>

        <div
          style={{
            background: "rgba(77,145,255,0.1)",
            padding: "15px",
            borderRadius: "8px",
            marginTop: "15px",
            border: "1px solid rgba(77,145,255,0.2)",
          }}
        >
          <p style={{ color: "#4d91ff", fontSize: "13px", margin: 0 }}>
            ⏳ Please wait <strong>{remaining}s</strong> for verification...
          </p>
          <p style={{ color: "#8b98ad", fontSize: "11px", marginTop: "5px", margin: 0 }}>
            Your Netflix link will be ready in 1 minute.
          </p>
        </div>

        <button
          onClick={() => navigate("/dashboard")}
          style={{ ...btnStyle, marginTop: "15px", width: "100%" }}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}

const pageStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  background: "#080d19",
  padding: "20px",
};
const cardStyle = {
  background: "#101a2c",
  padding: "30px",
  borderRadius: "16px",
  maxWidth: "500px",
  width: "100%",
  border: "1px solid rgba(77,145,255,0.3)",
};
const btnStyle = {
  padding: "12px",
  borderRadius: "8px",
  cursor: "pointer",
  background: "transparent",
  color: "#8b98ad",
  border: "1px solid rgba(255,255,255,0.15)",
  fontWeight: "bold",
};
const infoBox = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "10px",
  background: "#0d1525",
  padding: "15px",
  borderRadius: "8px",
  color: "#fff",
  fontSize: "12px",
};
const labelStyle = { color: "#6e7b91", fontSize: "9px", letterSpacing: "1px" };