import axios from "axios";

/** Default API origin: same hostname as the SPA (localhost vs 127.0.0.1) on port 8001. */
function defaultApiBaseUrl(): string {
  if (typeof window !== "undefined" && window.location?.hostname) {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8001`;
  }
  return "http://localhost:8001";
}

/** Override with VITE_API_BASE_URL in `.env` / deploy env. */
export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ||
  defaultApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

const storedToken = localStorage.getItem("squadron_ops_token");
if (storedToken) {
  api.defaults.headers.common.Authorization = `Bearer ${storedToken}`;
}
