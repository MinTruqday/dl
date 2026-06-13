import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/audit/kiem-duyet-vien`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) return { data: [] };
  return data;
}
