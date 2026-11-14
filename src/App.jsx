import { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import "./App.css";
import { api } from "./services/api.js";
import { useAuth } from "./context/AuthContext.jsx";
import { useCart } from "./context/CartContext.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import UserDashboard from "./pages/UserDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import Checkout from "./pages/Checkout.jsx";
import ProductCard from "./components/ProductCard.jsx";

// Kadar tukaran statik (1 MYR = X)
const RATES = {
  MYR: { rate: 1.00, symbol: "RM" },
  IDR: { rate: 3300, symbol: "Rp" },
  USD: { rate: 0.21, symbol: "$" },
  VND: { rate: 5400, symbol: "₫" },
  PHP: { rate: 12.0, symbol: "₱" },
  SGD: { rate: 0.30, symbol: "S$" },
};

function formatPrice(baseMYR, currency) {
  const r = RATES[currency] || RATES.MYR;
  const amount = baseMYR * r.rate;
  if (currency === "IDR" || currency === "VND") {
    return `${r.symbol}${Math.round(amount).toLocaleString()}`;
  }
  return `${r.symbol}${amount.toFixed(2)}`;
}

function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const { addToCart } = useCart();
  const navigate = useNavigate();

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quota, setQuota] = useState(null);
  const [stock, setStock] = useState({ Premium: 0, Standard: 0, Basic: 0 });
  const [claimingId, setClaimingId] = useState(null);
  const [result, setResult] = useState(null);
  const [errorModal, setErrorModal] = useState(null);

  const [buyPlan, setBuyPlan] = useState("Premium");
  const [buyQty, setBuyQty] = useState(1);

  // Harga base dalam MYR
  const planPrices = { Premium: 0.50, Standard: 0.25, Basic: 0.00 };
  const planCurrency = { Premium: "MYR", Standard: "MYR", Basic: "MYR" };

  useEffect(() => {
    api.getProducts()
      .then((d) => setProducts(d.products || d))
      .catch(console.error)
      .finally(() => setLoading(false));

    const fetchStock = () =>
      api.getStock().then((d) => setStock(d.stock || { Premium: 0, Standard: 0, Basic: 0 })).catch(console.error);

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
    if (!user) { navigate("/login"); return; }
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
    if (!user) { navigate("/login"); return; }
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
      <Route path="/admin/login" element={<AdminLogin />} />
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
                  <button onClick={() => navigate("/dashboard")} style={navBtn}>📊 Dashboard</button>
                )}
                {user ? (
                  <>
                    <span style={{ color: "#8b98ad", fontSize: "12px" }}>👤 {user.email}</span>
                    <button onClick={signOut} style={navBtn}>Logout</button>
                  </>
                ) : (
                  <>
                    <button onClick={() => navigate("/admin/login")} style={navBtn}>🔐 Admin</button>
                    <button
                      onClick={() => navigate("/login")}
                      style={{ padding: "10px 16px", borderRadius: "8px", background: "#ffd43b", color: "#06101e", border: "none", cursor: "pointer", fontSize: "12px", fontWeight: "bold" }}
                    >
                      Login / Register
                    </button>
                  </>
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
                  <h1>Claim Free or<br />Buy Premium<br /><span>Instantly.</span></h1>
                  <p>Buy Premium/Standard at low prices, or claim free Basic accounts daily.</p>
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
                      <p>From {formatPrice(0.25, "MYR")}</p>
                    </div>
                    <div className="card-price">
                      <span>FROM</span>
                      <strong>{formatPrice(0.25, "MYR")}</strong>
                    </div>
                    <div className="card-decoration">NC.</div>
                  </div>
                </div>
              </section>

              {/* STOCK BANNER */}
              <section className="products-section" style={{ paddingBottom: "0", paddingTop: "40px" }}>
                <div className="stock-grid">
                  <div className="stock-card">
                    <div className="stock-label">💎 PREMIUM</div>
                    <div className="stock-value stock-premium">{stock.Premium || 0}</div>
                  </div>
                  <div className="stock-card">
                    <div className="stock-label">⭐ STANDARD</div>
                    <div className="stock-value stock-standard">{stock.Standard || 0}</div>
                  </div>
                  <div className="stock-card">
                    <div className="stock-label">🔹 BASIC (FREE)</div>
                    <div className="stock-value stock-basic">{stock.Basic || 0}</div>
                  </div>
                </div>
              </section>

              {/* BUY SECTION */}
              <section className="products-section" id="buy" style={{ paddingTop: "30px" }}>
                <div className="section-heading">
                  <div>
                    <div className="section-label">BUY PREMIUM / STANDARD</div>
                    <h2>Buy Now<span>.</span></h2>
                    <p>Instant delivery after payment.</p>
                  </div>
                </div>

                <div className="buy-card">
                  <div className="plan-grid">
                    {["Premium", "Standard", "Basic"].map((plan) => (
                      <button
                        key={plan}
                        onClick={() => setBuyPlan(plan)}
                        className={`plan-btn ${buyPlan === plan ? "active" : ""}`}
                      >
                        <div className="plan-label">{plan === "Basic" ? "BASIC (ALSO FREE)" : plan.toUpperCase()}</div>
                        <div className="plan-price">
                          {formatPrice(planPrices[plan], "MYR")}
                          <span className="plan-currency">MYR</span>
                        </div>
                        <div className="plan-stock">Stock: {stock[plan] || 0}</div>
                      </button>
                    ))}
                  </div>

                  <div className="buy-footer">
                    <div className="qty-control">
                      <span className="qty-label">QTY</span>
                      <div className="qty-box">
                        <button onClick={() => setBuyQty(Math.max(1, buyQty - 1))}>−</button>
                        <span>{buyQty}</span>
                        <button onClick={() => setBuyQty(buyQty + 1)}>+</button>
                      </div>
                    </div>

                    <div className="total-display">
                      <div className="total-label">TOTAL</div>
                      <div className="total-value">{formatPrice(planPrices[buyPlan] * buyQty, "MYR")}</div>
                    </div>

                    <button onClick={handleBuyNow} className="buy-now-btn">🛒 Buy Now</button>
                  </div>
                </div>
              </section>

              {/* FREE CLAIM SECTION */}
              <section className="products-section" id="free">
                <div className="section-heading">
                  <div>
                    <div className="section-label">FREE BASIC ACCOUNTS</div>
                    <h2>Claim Free<span>.</span></h2>
                    <p>Max 3 free claims per day. First come, first served.</p>
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
                  <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "15px" }}>Your Netflix account is ready.</p>
                  <div className="result-info">
                    <div className="result-row"><span>EMAIL</span><strong>{result.email || "—"}</strong></div>
                    <div className="result-row"><span>PLAN</span><strong>{result.plan || "—"}</strong></div>
                    <div className="result-row"><span>COUNTRY</span><strong>{result.country || "—"}</strong></div>
                    <div className="result-row"><span>EXPIRY</span><strong>{result.expires ? new Date(result.expires * 1000).toLocaleString() : "—"}</strong></div>
                    <div className="result-row"><span>LINK</span><a href={result.redemption_url} target="_blank" rel="noreferrer" style={{ color: "#4d91ff", fontSize: "11px", wordBreak: "break-all" }}>{result.redemption_url}</a></div>
                  </div>
                  <button onClick={() => { navigator.clipboard.writeText(result.redemption_url); alert("Copied!"); }} className="modal-primary-btn">📋 Copy Link</button>
                  <button onClick={() => setResult(null)} className="modal-secondary-btn">Close</button>
                </div>
              </div>
            )}

            {/* MODAL ERROR */}
            {errorModal && (
              <div style={modalOverlay}>
                <div style={{ ...modalCard, background: "#1a0f0f", border: "1px solid rgba(255,91,91,0.3)" }}>
                  <h2 style={{ color: "#ff7c7c" }}>⚠️ Error</h2>
                  <p style={{ color: "#8b98ad", fontSize: "13px", marginBottom: "15px" }}>{errorModal}</p>
                  <button onClick={() => setErrorModal(null)} className="modal-primary-btn">Close</button>
                </div>
              </div>
            )}
          </div>
        }
      />
    </Routes>
  );
}

const navBtn = { padding: "10px 16px", borderRadius: "8px", background: "transparent", color: "#fff", border: "1px solid rgba(255,255,255,0.15)", cursor: "pointer", fontSize: "12px", fontWeight: "bold" };
const modalOverlay = { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.85)", display: "grid", placeItems: "center", zIndex: 9999, padding: "20px" };
const modalCard = { background: "#101a2c", padding: "30px", borderRadius: "16px", maxWidth: "500px", width: "100%", border: "1px solid rgba(77,145,255,0.3)" };

export default App;