import { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import "./App.css";
import { api } from "./services/api.js";
import { useAuth } from "./context/AuthContext.jsx";
import { useCart } from "./context/CartContext.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import UserDashboard from "./pages/UserDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import Checkout from "./pages/Checkout.jsx";
import ProductCard from "./components/ProductCard.jsx";

function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const { addToCart } = useCart();
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quota, setQuota] = useState(null);
  const [stock, setStock] = useState(null);
  const [claimingId, setClaimingId] = useState(null);
  const [result, setResult] = useState(null);
  const [errorModal, setErrorModal] = useState(null);

  const [buyPlan, setBuyPlan] = useState("Premium");
  const [buyQty, setBuyQty] = useState(1);

  const planPrices = { Premium: 0.50, Standard: 0.25, Basic: 0.25 };

  useEffect(() => {
    api.getProducts()
      .then((d) => setProducts(d.products || d))
      .catch(console.error)
      .finally(() => setLoading(false));

    const fetchStock = () =>
      api.getStock().then((d) => setStock(d.stock)).catch(console.error);

    fetchStock();
    const interval = setInterval(fetchStock, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (user) {
      api.getQuota().then(setQuota).catch(console.error);
    } else {
      setQuota(null);
    }
  }, [user]);

  const handleClaimFree = async (productId) => {
    if (!user) {
      navigate("/login");
      return;
    }
    setClaimingId(productId);
    setResult(null);
    setErrorModal(null);

    try {
      const data = await api.claimFree(productId);
      setResult(data);
      if (data.redemption_url) window.open(data.redemption_url, "_blank");
      setQuota(await api.getQuota());
      setStock((await api.getStock()).stock);
    } catch (err) {
      setErrorModal(err.message);
    } finally {
      setClaimingId(null);
    }
  };

  const handleBuyNow = () => {
    if (!user) {
      navigate("/login");
      return;
    }
    const selected = products.find((p) => p.plan === buyPlan);
    addToCart({
      id: selected?.id || Date.now(),
      name: selected?.name || `Netflix ${buyPlan}`,
      plan: buyPlan,
      price: planPrices[buyPlan],
      quantity: buyQty,
    });
    navigate("/checkout");
  };

  if (authLoading) {
    return (
      <div style={{ color: "#fff", padding: "50px", textAlign: "center", background: "#080d19", minHeight: "100vh" }}>
        Loading...
      </div>
    );
  }

  const basicProducts = products.filter((p) => p.plan === "Basic");

  return (
    <Routes>
      <Route path="/login" element={<AuthPage onBack={() => navigate("/")} />} />
      <Route path="/dashboard" element={<UserDashboard />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route
        path="*"
        element={
          <div className="app">
            <header className="navbar">
              <a href="#" className="brand">
                <span className="brand-icon">N</span>
                <span>NET<span>COOKIES</span></span>
              </a>
              <nav className="nav-links">
                <a href="#home">Home</a>
                <a href="#buy">Buy</a>
                <a href="#free">Free</a>
              </nav>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                {user && (
                  <button onClick={() => navigate("/dashboard")} style={navBtn}>
                    📊 Dashboard
                  </button>
                )}
                {user ? (
                  <>
                    <span style={{ color: "#8b98ad", fontSize: "12px" }}>👤 {user.email}</span>
                    <button onClick={signOut} style={navBtn}>Logout</button>
                  </>
                ) : (
                  <button
                    onClick={() => navigate("/login")}
                    style={{
                      padding: "10px 16px", borderRadius: "8px",
                      background: "#ffd43b", color: "#06101e",
                      border: "none", cursor: "pointer",
                      fontSize: "12px", fontWeight: "bold",
                    }}
                  >
                    Login / Register
                  </button>
                )}
              </div>
            </header>

            <main>
              {/* HERO */}
              <section className="hero" id="home">
                <div className="hero-content">
                  <div className="hero-badge">
                    <span className="online-dot"></span>
                    FREE + PREMIUM ACCOUNTS
                  </div>
                  <h1>
                    Claim Free or<br />
                    Buy Premium<br />
                    <span>Instantly.</span>
                  </h1>
                  <p>
                    Buy Premium/Standard at low prices, or claim free Basic accounts daily.
                  </p>
                  <div className="hero-actions">
                    <a href="#buy" className="primary-btn">Buy Now <span>→</span></a>
                    <a href="#free" className="secondary-btn">Claim Free</a>
                  </div>
                </div>
                <div className="hero-visual">
                  <div className="hero-glow"></div>
                  <div className="netflix-card">
                    <div className="netflix-logo">N</div>
                    <div className="netflix-card-info">
                      <span>NETFLIX</span>
                      <h2>Premium Access</h2>
                      <p>From $0.25</p>
                    </div>
                    <div className="card-price">
                      <span>FROM</span>
                      <strong>$0.25</strong>
                    </div>
                    <div className="card-decoration">NC.</div>
                  </div>
                </div>
              </section>

              {/* STOCK BANNER */}
              {stock && (
                <section className="products-section" style={{ paddingBottom: "0", paddingTop: "40px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "30px" }}>
                    <div style={stockCard}>
                      <div style={stockLabel}>💎 PREMIUM</div>
                      <div style={{ ...stockValue, color: "#ffd43b" }}>{stock.Premium || 0}</div>
                    </div>
                    <div style={stockCard}>
                      <div style={stockLabel}>⭐ STANDARD</div>
                      <div style={{ ...stockValue, color: "#4d91ff" }}>{stock.Standard || 0}</div>
                    </div>
                    <div style={stockCard}>
                      <div style={stockLabel}>🔹 BASIC (FREE)</div>
                      <div style={{ ...stockValue, color: "#55e2a1" }}>{stock.Basic || 0}</div>
                    </div>
                  </div>
                </section>
              )}

              {/* BUY SECTION */}
              <section className="products-section" id="buy" style={{ paddingTop: "30px" }}>
                <div className="section-heading">
                  <div>
                    <div className="section-label">BUY PREMIUM / STANDARD</div>
                    <h2>Buy Now<span>.</span></h2>
                    <p>Instant delivery after payment.</p>
                  </div>
                </div>

                <div style={{ background: "#0e1727", padding: "28px", borderRadius: "14px", border: "1px solid rgba(77,145,255,0.2)" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "15px", marginBottom: "20px" }}>
                    {["Premium", "Standard", "Basic"].map((plan) => (
                      <button
                        key={plan}
                        onClick={() => setBuyPlan(plan)}
                        style={{
                          padding: "20px",
                          borderRadius: "12px",
                          border: buyPlan === plan ? "2px solid #4d91ff" : "1px solid rgba(255,255,255,0.1)",
                          background: buyPlan === plan ? "rgba(77,145,255,0.1)" : "#0d1525",
                          cursor: "pointer",
                          textAlign: "left",
                        }}
                      >
                        <div style={{ color: "#8b98ad", fontSize: "10px", fontWeight: 800, letterSpacing: "1px" }}>
                          {plan === "Basic" ? "BASIC (ALSO FREE)" : plan.toUpperCase()}
                        </div>
                        <div style={{ color: "#fff", fontSize: "18px", fontWeight: "bold", marginTop: "5px" }}>
                          ${planPrices[plan].toFixed(2)}{" "}
                          <span style={{ fontSize: "10px", color: "#6e7b91" }}>USD</span>
                        </div>
                        <div style={{ color: "#6e7b91", fontSize: "11px", marginTop: "5px" }}>
                          Stock: {stock?.[plan] || 0}
                        </div>
                      </button>
                    ))}
                  </div>

                  <div style={{ display: "flex", gap: "15px", alignItems: "center", flexWrap: "wrap" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ color: "#8b98ad", fontSize: "12px", fontWeight: 700 }}>QTY</span>
                      <div style={{ display: "flex", alignItems: "center", background: "#0d1525", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.1)" }}>
                        <button onClick={() => setBuyQty(Math.max(1, buyQty - 1))} style={qtyBtn}>−</button>
                        <span style={{ color: "#fff", minWidth: "40px", textAlign: "center", fontWeight: "bold" }}>{buyQty}</span>
                        <button onClick={() => setBuyQty(buyQty + 1)} style={qtyBtn}>+</button>
                      </div>
                    </div>

                    <div style={{ marginLeft: "auto", textAlign: "right" }}>
                      <div style={{ color: "#8b98ad", fontSize: "10px", fontWeight: 700 }}>TOTAL</div>
                      <div style={{ color: "#ffd43b", fontSize: "22px", fontWeight: "bold" }}>
                        ${(planPrices[buyPlan] * buyQty).toFixed(2)}
                      </div>
                    </div>

                    <button
                      onClick={handleBuyNow}
                      style={{
                        padding: "14px 30px", borderRadius: "8px",
                        background: "#ffd43b", color: "#06101e",
                        border: "none", fontWeight: "bold", fontSize: "14px",
                        cursor: "pointer",
                      }}
                    >
                      🛒 Buy Now
                    </button>
                  </div>
                </div>
              </section>

              {/* FREE CLAIM SECTION */}
              <section className="products-section" id="free">
                <div className="section-heading">
                  <div>
                    <div className="section-label">FREE BASIC ACCOUNTS</div>
                    <h2>Claim Free<span>.</span></h2>
                    <p>Max 10 free claims per day. First come, first served.</p>
                  </div>
                  <div className="product-count">{basicProducts.length} LISTINGS</div>
                </div>

                {loading ? (
                  <div className="empty-state"><h3>Loading...</h3></div>
                ) : basicProducts.length === 0 ? (
                  <div className="empty-state">
                    <h3>No Basic accounts available</h3>
                    <p>Come back later or buy Premium/Standard above.</p>
                  </div>
                ) : (
                  <div className="product-grid">
                    {basicProducts.map((product) => (
                      <ProductCard
                        key={product.id}
                        product={product}
                        onClaimFree={handleClaimFree}
                        claimingId={claimingId}
                        quota={quota}
                        stock={stock}
                      />
                    ))}
                  </div>
                )}
              </section>
            </main>

            <footer className="footer">
              <a href="#home" className="brand">
                <span className="brand-icon">N</span>
                <span>NET<span>COOKIES</span></span>
              </a>
              <p>© {new Date().getFullYear()} NetCookies. All rights reserved.</p>
              <a href="#home">Back to top ↑</a>
            </footer>

            {/* MODAL RESULT */}
            {result && (
              <div style={modalOverlay}>
                <div style={modalCard}>
                  <h2 style={{ color: "#ffd43b" }}>🎉 Success!</h2>
                  <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "15px" }}>
                    Your Netflix account is ready.
                  </p>
                  <div style={{ background: "#0d1525", padding: "15px", borderRadius: "8px", marginBottom: "15px" }}>
                    <p style={{ color: "#8b98ad", fontSize: "11px", marginBottom: "8px" }}>
                      PLAN: {result.plan || "—"}
                    </p>
                    <p style={{ color: "#4d91ff", fontSize: "12px", wordBreak: "break-all" }}>
                      {result.redemption_url}
                    </p>
                  </div>
                  <button
                    onClick={() => { navigator.clipboard.writeText(result.redemption_url); alert("Copied!"); }}
                    style={{ width: "100%", padding: "12px", borderRadius: "8px", background: "#4d91ff", color: "#fff", border: "none", fontWeight: "bold", cursor: "pointer", marginBottom: "10px" }}
                  >
                    📋 Copy Link
                  </button>
                  <button
                    onClick={() => setResult(null)}
                    style={{ width: "100%", padding: "12px", borderRadius: "8px", background: "transparent", color: "#8b98ad", border: "1px solid rgba(255,255,255,0.15)", cursor: "pointer" }}
                  >
                    Close
                  </button>
                </div>
              </div>
            )}

            {/* MODAL ERROR */}
            {errorModal && (
              <div style={modalOverlay}>
                <div style={{ ...modalCard, background: "#1a0f0f", border: "1px solid rgba(255,91,91,0.3)" }}>
                  <h2 style={{ color: "#ff7c7c" }}>⚠️ Error</h2>
                  <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "15px" }}>{errorModal}</p>
                  <button
                    onClick={() => setErrorModal(null)}
                    style={{ width: "100%", padding: "12px", borderRadius: "8px", background: "#4d91ff", color: "#fff", border: "none", fontWeight: "bold", cursor: "pointer" }}
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        }
      />
    </Routes>
  );
}

const navBtn = {
  padding: "10px 16px", borderRadius: "8px",
  background: "transparent", color: "#fff",
  border: "1px solid rgba(255,255,255,0.15)",
  cursor: "pointer", fontSize: "12px", fontWeight: "bold",
};
const stockCard = {
  background: "linear-gradient(135deg, #1a2f4d, #0e1727)",
  padding: "20px", borderRadius: "12px",
  border: "1px solid rgba(77,145,255,0.2)", textAlign: "center",
};
const stockLabel = { fontSize: "11px", color: "#6e7b91", fontWeight: 800, letterSpacing: "1px" };
const stockValue = { fontSize: "32px", fontWeight: "bold", marginTop: "5px" };
const qtyBtn = {
  width: "36px", height: "36px", borderRadius: "6px",
  background: "transparent", color: "#c5d1e4",
  border: "none", cursor: "pointer", fontSize: "18px", fontWeight: "bold",
};
const modalOverlay = {
  position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
  background: "rgba(0,0,0,0.85)", display: "grid",
  placeItems: "center", zIndex: 9999, padding: "20px",
};
const modalCard = {
  background: "#101a2c", padding: "30px", borderRadius: "16px",
  maxWidth: "500px", width: "100%",
  border: "1px solid rgba(77,145,255,0.3)",
};

export default App;