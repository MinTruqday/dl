import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/kiem-toan/logs`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) return { data: [] };
  return data;
}
