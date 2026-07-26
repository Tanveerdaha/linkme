import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/stores/authStore";

/**
 * Axios client for LinkMe API v1.
 * Base URL comes from NEXT_PUBLIC_API_URL (see .env.example).
 */
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8013/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15_000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token =
      useAuthStore.getState().accessToken ||
      window.localStorage.getItem("linkme_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (!original || error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    // Avoid refresh loops on auth endpoints.
    const url = original.url || "";
    if (url.includes("/auth/login") || url.includes("/auth/token/refresh") || url.includes("/auth/signup")) {
      return Promise.reject(error);
    }

    original._retry = true;

    if (!refreshPromise) {
      refreshPromise = useAuthStore
        .getState()
        .refreshSession()
        .finally(() => {
          refreshPromise = null;
        });
    }

    const access = await refreshPromise;
    if (!access) {
      return Promise.reject(error);
    }

    original.headers.Authorization = `Bearer ${access}`;
    return api(original);
  },
);

export default api;

export type HealthResponse = {
  status: string;
  database: boolean;
  redis: boolean;
};

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health/");
  return data;
}

export function getApiErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string; message?: string } | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    if (data && typeof data === "object") {
      const first = Object.values(data).flat()[0];
      if (typeof first === "string") return first;
    }
  }
  if (error instanceof Error) return error.message;
  return fallback;
}
