import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "guill_access_token";

export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function setToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}

// API base URL. In production point this at the reverse-proxy HTTPS endpoint.
const API_BASE =
  (process.env.EXPO_PUBLIC_API_BASE as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...options, headers });
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(res.status, body?.error ?? "request_failed");
  }
  return body as T;
}

export const api = {
  get: <T>(p: string) => request<T>(p, { method: "GET" }),
  post: <T>(p: string, data: unknown) => request<T>(p, { method: "POST", body: JSON.stringify(data) }),
  patch: <T>(p: string, data: unknown) => request<T>(p, { method: "PATCH", body: JSON.stringify(data) }),
  del: <T>(p: string) => request<T>(p, { method: "DELETE" }),
};

// Common response shapes (keep in sync with packages/contracts/openapi.yaml).
export interface Trip {
  id: string;
  title: string;
  origin?: string;
  destination?: string;
  status: string;
  vehicle_id?: string | null;
  trailer_id?: string | null;
}

export interface Profile {
  id: string;
  name?: string;
  [key: string]: unknown;
}
