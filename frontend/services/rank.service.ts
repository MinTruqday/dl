import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getSocialRankingAPI() {
  const res = await fetch(`${API_URL}/cong-dong/xep-hang`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng xếp hạng");
  return data;
}

export async function getReaderRankingAPI() {
  const res = await fetch(`${API_URL}/cong-dong/xep-hang-doc-gia`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng xếp hạng độc giả");
  return data;
}
