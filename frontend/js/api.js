/**
 * api.js — fetch wrapper with automatic JWT Authorization header
 * Handles 401 by clearing localStorage and redirecting to login.
 */

// In production (Vercel), API is served at /api.
// For local development, you can override by setting window.API_BASE_URL before importing this module.
const API_BASE = window.API_BASE_URL || "/api";

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // Handle 401 — clear auth and redirect
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/index.html";
    return null;
  }

  // 204 No Content — return null
  if (response.status === 204) {
    return null;
  }

  const data = await response.json();

  if (!response.ok) {
    // Throw structured error
    const err = new Error(data?.error?.message || "오류가 발생했습니다");
    err.code = data?.error?.code || "UNKNOWN_ERROR";
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

// Convenience methods
const api = {
  get: (path, options = {}) => apiFetch(path, { method: "GET", ...options }),
  post: (path, body, options = {}) =>
    apiFetch(path, {
      method: "POST",
      body: JSON.stringify(body),
      ...options,
    }),
  put: (path, body, options = {}) =>
    apiFetch(path, {
      method: "PUT",
      body: JSON.stringify(body),
      ...options,
    }),
  patch: (path, body, options = {}) =>
    apiFetch(path, {
      method: "PATCH",
      body: JSON.stringify(body),
      ...options,
    }),
  delete: (path, options = {}) =>
    apiFetch(path, { method: "DELETE", ...options }),
};

export default api;
