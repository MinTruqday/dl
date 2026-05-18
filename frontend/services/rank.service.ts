import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getSocialRankingAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/xep-hang?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng xếp hạng");
  return data;
}

export async function getReaderRankingAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/xep-hang/doc-gia?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng xếp hạng độc giả");
  return data;
}

export async function getContributionRankingAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/xep-hang/dong-gop?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng xếp hạng đóng góp");
  return data;
}

export async function getFeaturedAuthorsAPI(limit: number = 10) {
  const res = await fetch(`${API_URL}/xep-hang/tac-gia-noi-bat?limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách tác giả");
  return data;
}
