import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({ baseURL: BASE_URL });

/* ===== INTERCEPTORS ===== */

// Attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("acadrix_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("acadrix_token");
      localStorage.removeItem("acadrix_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

/* ===== AUTH ===== */
export const login = (data) => api.post("/auth/login", data);
export const register = (data) => api.post("/auth/register", data);
export const loginUser = login;
export const registerUser = register;
export const getMe = () => api.get("/auth/me");

/* ===== DOCUMENTS ===== */
export const uploadDocument = (formData) =>
  api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const listDocuments = () => api.get("/documents/");
export const deleteDocument = (id) => api.delete(`/documents/${id}`);

/* ===== QUERY ===== */
export const queryDocuments = (data) => api.post("/query/", data);

/* ===== HISTORY ===== */
export const getHistory = (limit = 20) => api.get(`/history/?limit=${limit}`);
export const deleteHistoryItem = (id) => api.delete(`/history/${id}`);
export const clearHistory = () => api.delete("/history/");
