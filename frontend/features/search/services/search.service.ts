import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export async function searchDocumentsAPI(query: string, limit = 100) {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });
  const response = await fetch(`${API_URL}/tim-kiem/tai-lieu?${params}`, {
    headers: getAuthHeaders(),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || payload.message || "Không thể tìm tài liệu");
  }
  return payload;
}

export async function smartSearchAPI(query: string, limit = 20) {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });
  const response = await fetch(`${API_URL}/tim-kiem/thong-minh?${params}`, {
    headers: getAuthHeaders(),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      payload.detail || payload.message || "Không thể tìm kiếm theo nội dung",
    );
  }
  return payload;
}

