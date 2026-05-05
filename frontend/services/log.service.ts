import { API_URL, getAuthHeaders } from "./auth.service";

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/logs/moderator`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return { data: [] };
  return await res.json();
}
