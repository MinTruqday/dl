import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/nhat-ky/kiem-duyet-vien`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) return { data: [] };
  return data;
}
