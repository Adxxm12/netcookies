import { useState } from "react";
import { useCart } from "../context/CartContext.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function ProductCard({ product, onClaimFree, claimingId, quota, stock }) {
  const { addToCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [quantity, setQuantity] = useState(1);

  const isFree = product.plan === "Basic";
  const isClaiming = claimingId === product.id;
  const quotaHabis = quota && quota.remaining <= 0;
  const stockHabis = stock && stock[product.plan] <= 0;
  const maxQty = stock ? Math.max(1, stock[product.plan] || 1) : 10;

  const handleBuyNow = () => {
    if (!user) {
      alert("Please login first");
      return;
    }
    addToCart({ ...product, quantity });
    navigate("/checkout");
  };

  return (
    <article className="product-card">
      <div className="product-card-top">
        <div className="product-icon">N</div>
        <span className="stock-badge">{isFree ? "● FREE" : `● ${product.plan}`}</span>
      </div>

      <div className="product-details">
        <span className="product-category">NETFLIX ACCOUNT</span>
        <h3>{product.name}</h3>
        <p className="product-country">{product.country || "🌍 Global"}</p>
      </div>

      <div className="product-specs">
        <div><span>PLAN</span><strong>{product.plan}</strong></div>
        <div><span>QUALITY</span><strong>{product.quality || "4K UHD"}</strong></div>
        <div><span>DURATION</span><strong>{product.duration || "30 Days"}</strong></div>
        <div>
          <span>PRICE</span>
          <strong style={{ color: "#ffd43b" }}>
            {isFree ? "FREE" : `$${Number(product.price).toFixed(2)}`}
          </strong>
        </div>
      </div>

      <div className="product-card-bottom" style={{ flexDirection: "column", alignItems: "stretch", gap: "10px" }}>
        {isFree ? (
          <button
            disabled={isClaiming || quotaHabis || stockHabis}
            onClick={() => onClaimFree(product.id)}
            style={{
              width: "100%",
              padding: "12px 16px",
              borderRadius: "8px",
              border: "1px solid rgba(77,145,255,0.3)",
              background: "rgba(77,145,255,0.12)",
              color: "#91baff",
              fontWeight: "bold",
              fontSize: "12px",
              cursor: isClaiming || quotaHabis || stockHabis ? "not-allowed" : "pointer",
              opacity: isClaiming || quotaHabis || stockHabis ? 0.5 : 1,
            }}
          >
            {isClaiming
              ? "⏳ Opening..."
              : !user
              ? "Login First"
              : quotaHabis
              ? "Quota Used"
              : stockHabis
              ? "Out of Stock"
              : "🎁 Claim Free"}
          </button>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ color: "#8b98ad", fontSize: "11px", fontWeight: 700 }}>QTY</span>
              <div style={{
                display: "flex", alignItems: "center",
                background: "#0d1525", borderRadius: "8px",
                border: "1px solid rgba(255,255,255,0.1)",
              }}>
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  style={qtyBtn}
                >
                  −
                </button>
                <span style={{ color: "#fff", minWidth: "30px", textAlign: "center", fontSize: "13px", fontWeight: "bold" }}>
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(Math.min(maxQty, quantity + 1))}
                  style={qtyBtn}
                >
                  +
                </button>
              </div>
              <span style={{ color: "#ffd43b", fontSize: "13px", fontWeight: "bold", marginLeft: "auto" }}>
                ${(Number(product.price) * quantity).toFixed(2)}
              </span>
            </div>

            <button
              onClick={handleBuyNow}
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "8px",
                border: "none",
                background: "#ffd43b",
                color: "#06101e",
                fontWeight: "bold",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              🛒 Buy Now — ${(Number(product.price) * quantity).toFixed(2)}
            </button>
          </>
        )}
      </div>
    </article>
  );
}

const qtyBtn = {
  width: "32px", height: "32px", borderRadius: "6px",
  background: "transparent", color: "#c5d1e4",
  border: "none", cursor: "pointer", fontSize: "16px", fontWeight: "bold",
};