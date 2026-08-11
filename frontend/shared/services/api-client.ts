const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export const API_URL = configuredApiUrl || "http://localhost:8000";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL?.trim() ||
  API_URL.replace(/^http/, "ws");

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("doclib_token");
  return token && token !== "null" && token !== "undefined" ? token : null;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

