import { supabase } from "./supabase";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const handleResponse = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message = "Something went wrong";
    if (typeof data.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data.detail)) {
      message = data.detail.map((e) => e.msg || JSON.stringify(e)).join(", ");
    } else if (data.detail) {
      message = JSON.stringify(data.detail);
    }
    throw new Error(message);
  }
  return data;
};

const getAuthHeaders = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) throw new Error("Please login first");
  return {
    "Authorization": `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  };
};

export const api = {
  getProducts: async () => {
    const res = await fetch(`${API_BASE_URL}/api/rewards`);
    return handleResponse(res);
  },

  getStock: async () => {
    const res = await fetch(`${API_BASE_URL}/api/stock`);
    return handleResponse(res);
  },

  getQuota: async () => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/giveaway/quota`, { headers });
    return handleResponse(res);
  },

  claimFree: async (productId) => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/giveaway/claim`, {
      method: "POST",
      headers,
      body: JSON.stringify({ product_id: productId }),
    });
    return handleResponse(res);
  },

  checkout: async (items) => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/checkout`, {
      method: "POST",
      headers,
      body: JSON.stringify({ items }),
    });
    return handleResponse(res);
  },

  getOrderStatus: async (orderId) => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/orders/${orderId}/status`, { headers });
    return handleResponse(res);
  },

  getMyOrders: async () => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/orders/my`, { headers });
    return handleResponse(res);
  },

  adminGetStats: async () => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/admin/stats`, { headers });
    return handleResponse(res);
  },

  adminGetOrders: async () => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/admin/orders`, { headers });
    return handleResponse(res);
  },

  adminRevoke: async (orderId) => {
    const headers = await getAuthHeaders();
    const res = await fetch(`${API_BASE_URL}/api/admin/revoke/${orderId}`, {
      method: "POST",
      headers,
    });
    return handleResponse(res);
  },
};