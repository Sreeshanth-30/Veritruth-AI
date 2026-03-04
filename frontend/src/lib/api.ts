/* ──────────────────────────────────────────────────────────── */
/*  VeriTruth AI — Axios API Client                            */
/* ──────────────────────────────────────────────────────────── */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach JWT ──────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = Cookies.get("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: handle 401 → refresh ───────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = Cookies.get("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        Cookies.set("access_token", data.access_token, { sameSite: "Strict" });
        Cookies.set("refresh_token", data.refresh_token, { sameSite: "Strict" });

        processQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Safely extract a human-readable message from an Axios error.
 * FastAPI 422 responses return `detail` as an array of Pydantic objects;
 * all other errors return `detail` as a plain string.
 */
export function getErrorMessage(
  err: unknown,
  fallback = "An unexpected error occurred"
): string {
  if (!err || typeof err !== "object") return fallback;
  const axiosErr = err as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = axiosErr?.response?.data?.detail;

  if (typeof detail === "string") return detail;

  // Pydantic v2 validation errors: array of {type, loc, msg, input, ctx}
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((d: unknown) => {
        if (d && typeof d === "object") {
          const e = d as { msg?: string; loc?: unknown[] };
          const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : undefined;
          return field ? `${field}: ${e.msg ?? "invalid"}` : (e.msg ?? "invalid");
        }
        return String(d);
      })
      .join("; ");
  }

  if (axiosErr.message) return axiosErr.message;
  return fallback;
}

export default api;
