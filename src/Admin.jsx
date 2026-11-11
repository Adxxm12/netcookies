
import { useMemo, useState } from "react";
import "./Admin.css";

const EMPTY_FORM = {
  name: "Netflix Premium",
  plan: "Premium",
  quality: "4K UHD",
  country: "🇲🇾 Malaysia",
  duration: "30 Days",
  price: "0.50",
  stock: "1",
  status: "active",
};

function Admin({ products, setProducts, onClose }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const totalStock = products.reduce(
    (total, product) => total + Number(product.stock || 0),
    0
  );

  const available = products.filter(
    (product) => Number(product.stock) > 0
  ).length;

  const soldOut = products.filter(
    (product) => Number(product.stock) <= 0
  ).length;

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      const matchesSearch =
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.country.toLowerCase().includes(search.toLowerCase()) ||
        product.plan.toLowerCase().includes(search.toLowerCase());

      const matchesFilter =
        filter === "all" ||
        (filter === "available" && Number(product.stock) > 0) ||
        (filter === "soldout" && Number(product.stock) <= 0) ||
        (filter === "hidden" && product.status === "hidden");

      return matchesSearch && matchesFilter;
    });
  }, [products, search, filter]);

  const updateField = (e) => {
    const { name, value } = e.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const saveProduct = (e) => {
    e.preventDefault();

    const price = Number(form.price);
    const stock = Number(form.stock);

    if (!Number.isFinite(price) || price < 0) {
      alert("Masukkan harga yang sah.");
      return;
    }

    if (!Number.isInteger(stock) || stock < 0) {
      alert("Stok mesti nombor bulat dan tidak negatif.");
      return;
    }

    const productData = {
      ...form,
      price,
      stock,
      status: form.status,
    };

    if (editingId !== null) {
      setProducts((previous) =>
        previous.map((product) =>
          product.id === editingId
            ? { ...product, ...productData }
            : product
        )
      );
    } else {
      setProducts((previous) => [
        ...previous,
        {
          id: Date.now(),
          ...productData,
        },
      ]);
    }

    resetForm();
  };

  const editProduct = (product) => {
    setEditingId(product.id);

    setForm({
      name: product.name,
      plan: product.plan,
      quality: product.quality,
      country: product.country,
      duration: product.duration,
      price: String(product.price),
      stock: String(product.stock),
      status: product.status || "active",
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const deleteProduct = (id) => {
    const confirmed = window.confirm(
      "Kau pasti nak padam listing ini?"
    );

    if (!confirmed) return;

    setProducts((previous) =>
      previous.filter((product) => product.id !== id)
    );

    if (editingId === id) resetForm();
  };

  const changeStock = (id, amount) => {
    setProducts((previous) =>
      previous.map((product) => {
        if (product.id !== id) return product;

        return {
          ...product,
          stock: Math.max(0, Number(product.stock) + amount),
        };
      })
    );
  };

  const toggleVisibility = (id) => {
    setProducts((previous) =>
      previous.map((product) => {
        if (product.id !== id) return product;

        return {
          ...product,
          status:
            product.status === "hidden" ? "active" : "hidden",
        };
      })
    );
  };

  return (
    <div className="admin-page">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-icon">N</div>
          <div>
            <h2>NETCOOKIES</h2>
            <span>ADMIN CONTROL</span>
          </div>
        </div>

        <div className="sidebar-label">MANAGEMENT</div>

        <div className="sidebar-link active">
          <span>▦</span> Dashboard
        </div>

        <div className="sidebar-link">
          <span>◈</span> Products
        </div>

        <div className="sidebar-link">
          <span>⚙</span> Inventory
        </div>

        <div className="sidebar-bottom">
          <div className="admin-profile">
            <div className="profile-avatar">A</div>
            <div>
              <strong>Administrator</strong>
              <span>Store Manager</span>
            </div>
          </div>

          <button className="sidebar-exit" onClick={onClose}>
            ← Back to Store
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <div>
            <span className="admin-breadcrumb">NETCOOKIES /</span>
            <h1>Dashboard</h1>
          </div>

          <button className="admin-back-btn" onClick={onClose}>
            View Store ↗
          </button>
        </header>

        <section className="admin-welcome">
          <div>
            <span className="admin-welcome-tag">OVERVIEW</span>
            <h2>Welcome back, Admin.</h2>
            <p>Manage your Netflix listings and inventory here.</p>
          </div>
          <div className="welcome-decoration">NC.</div>
        </section>

        {/* STATS */}
        <section className="admin-stats">
          <div className="admin-stat-card">
            <div className="stat-icon blue">▦</div>
            <span>TOTAL LISTINGS</span>
            <h2>{products.length}</h2>
            <p>All registered products</p>
          </div>

          <div className="admin-stat-card">
            <div className="stat-icon green">✓</div>
            <span>AVAILABLE LISTINGS</span>
            <h2>{available}</h2>
            <p>Listings with stock</p>
          </div>

          <div className="admin-stat-card">
            <div className="stat-icon yellow">◈</div>
            <span>TOTAL STOCK</span>
            <h2>{totalStock}</h2>
            <p>Available account units</p>
          </div>

          <div className="admin-stat-card">
            <div className="stat-icon red">!</div>
            <span>SOLD OUT</span>
            <h2>{soldOut}</h2>
            <p>Listings without stock</p>
          </div>
        </section>

        {/* PRODUCT FORM */}
        <section className="admin-panel">
          <div className="admin-panel-heading">
            <div>
              <span className="admin-section-label">
                PRODUCT MANAGEMENT
              </span>
              <h2>{editingId ? "Edit Listing" : "Add New Listing"}</h2>
            </div>

            {editingId && (
              <button
                className="cancel-edit-btn"
                onClick={resetForm}
              >
                Cancel Edit
              </button>
            )}
          </div>

          <form className="admin-form" onSubmit={saveProduct}>
            <div className="admin-form-grid">
              <label>
                Product Name
                <input
                  name="name"
                  value={form.name}
                  onChange={updateField}
                  placeholder="Netflix Premium"
                  required
                />
              </label>

              <label>
                Plan
                <select
                  name="plan"
                  value={form.plan}
                  onChange={updateField}
                >
                  <option>Premium</option>
                  <option>Standard</option>
                  <option>Basic</option>
                </select>
              </label>

              <label>
                Quality
                <select
                  name="quality"
                  value={form.quality}
                  onChange={updateField}
                >
                  <option>4K UHD</option>
                  <option>1080p</option>
                  <option>720p</option>
                </select>
              </label>

              <label>
                Country
                <input
                  name="country"
                  value={form.country}
                  onChange={updateField}
                  placeholder="🇲🇾 Malaysia"
                  required
                />
              </label>

              <label>
                Duration
                <input
                  name="duration"
                  value={form.duration}
                  onChange={updateField}
                  placeholder="30 Days"
                  required
                />
              </label>

              <label>
                Price (USD)
                <input
                  name="price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.price}
                  onChange={updateField}
                  required
                />
              </label>

              <label>
                Stock Quantity
                <input
                  name="stock"
                  type="number"
                  min="0"
                  step="1"
                  value={form.stock}
                  onChange={updateField}
                  required
                />
              </label>

              <label>
                Listing Visibility
                <select
                  name="status"
                  value={form.status}
                  onChange={updateField}
                >
                  <option value="active">Visible</option>
                  <option value="hidden">Hidden</option>
                </select>
              </label>
            </div>

            <div className="admin-form-actions">
              <button type="button" onClick={resetForm}>
                Reset
              </button>

              <button type="submit" className="save-product-btn">
                {editingId ? "Update Listing" : "+ Add Product"}
              </button>
            </div>
          </form>
        </section>

        {/* INVENTORY */}
        <section className="admin-panel inventory-panel">
          <div className="admin-panel-heading">
            <div>
              <span className="admin-section-label">
                INVENTORY CONTROL
              </span>
              <h2>Product Listings</h2>
            </div>

            <span className="inventory-total">
              {products.length} TOTAL
            </span>
          </div>

          <div className="inventory-toolbar">
            <input
              type="text"
              placeholder="Search product, country or plan..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Listings</option>
              <option value="available">Available</option>
              <option value="soldout">Sold Out</option>
              <option value="hidden">Hidden</option>
            </select>
          </div>

          <div className="inventory-list">
            {filteredProducts.map((product) => (
              <div className="inventory-item" key={product.id}>
                <div className="inventory-product">
                  <div className="inventory-netflix-icon">N</div>

                  <div>
                    <h3>{product.name}</h3>
                    <p>
                      {product.country} · {product.plan} ·{" "}
                      {product.duration}
                    </p>
                  </div>
                </div>

                <div className="inventory-price">
                  <span>PRICE</span>
                  <strong>
                    ${Number(product.price).toFixed(2)}
                  </strong>
                </div>

                <div className="inventory-stock">
                  <span>STOCK</span>
                  <div className="stock-controls">
                    <button
                      onClick={() => changeStock(product.id, -1)}
                      disabled={Number(product.stock) <= 0}
                    >
                      −
                    </button>

                    <strong>{product.stock}</strong>

                    <button
                      onClick={() => changeStock(product.id, 1)}
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="inventory-status">
                  <span
                    className={
                      product.status === "hidden"
                        ? "status-hidden"
                        : Number(product.stock) > 0
                        ? "status-active"
                        : "status-sold"
                    }
                  >
                    {product.status === "hidden"
                      ? "HIDDEN"
                      : Number(product.stock) > 0
                      ? "AVAILABLE"
                      : "SOLD OUT"}
                  </span>
                </div>

                <div className="inventory-actions">
                  <button
                    className="edit-btn"
                    onClick={() => editProduct(product)}
                    title="Edit listing"
                  >
                    ✎
                  </button>

                  <button
                    className="visibility-btn"
                    onClick={() => toggleVisibility(product.id)}
                    title="Toggle visibility"
                  >
                    {product.status === "hidden" ? "◉" : "◌"}
                  </button>

                  <button
                    className="delete-btn"
                    onClick={() => deleteProduct(product.id)}
                    title="Delete listing"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}

            {filteredProducts.length === 0 && (
              <div className="admin-empty">
                <h3>No listings found</h3>
                <p>Try changing your search or filter.</p>
              </div>
            )}
          </div>
        </section>

        <footer className="admin-footer">
          <span>NETCOOKIES ADMIN PANEL</span>
          <span>Inventory Management</span>
        </footer>
      </main>
    </div>
  );
}

export default Admin;
