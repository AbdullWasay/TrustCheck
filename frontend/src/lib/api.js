// Empty base URL = same origin.
// Local: Vite proxies /api → FastAPI :8000
// Vercel: /api/* rewrites to the Python backend service
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

const USER_KEY = "trustcheck_user";

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function storeUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser() {
  localStorage.removeItem(USER_KEY);
}

async function request(path, { method = "GET", body, userId } = {}) {
  const headers = {
    "Content-Type": "application/json",
  };

  if (userId) {
    headers["X-User-Id"] = userId;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg || JSON.stringify(item)).join(", ")
          : "Request failed.";
    throw new Error(message);
  }

  return data;
}

export const api = {
  health: () => request("/api/health"),
  register: (payload) =>
    request("/api/auth/register", { method: "POST", body: payload }),
  login: (payload) =>
    request("/api/auth/login", { method: "POST", body: payload }),
  listChecks: (userId) => request("/api/checks", { userId }),
  startCheck: (userId, payload) =>
    request("/api/checks", { method: "POST", body: payload, userId }),
  updateDetails: (userId, checkId, payload) =>
    request(`/api/checks/${checkId}/details`, {
      method: "PUT",
      body: payload,
      userId,
    }),
  getCheck: (userId, checkId) =>
    request(`/api/checks/${checkId}`, { userId }),
};
