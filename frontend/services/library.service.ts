import { API_URL, getAuthHeaders } from "./authentication.service";

export async function createReadingListAPI(data: {
  name: string;
  description?: string;
  is_public?: boolean;
}) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo danh sách đọc thất bại");
  return result;
}

export async function getMyReadingListsAPI() {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách đọc");
  return data;
}

export async function getReadingListByIdAPI(listId: string) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach/${listId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải chi tiết danh sách");
  return data;
}

export async function addDocumentToListAPI(listId: string, documentId: string) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach/${listId}/tai-lieu/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thêm vào danh sách thất bại");
  return data;
}

export async function removeDocumentFromListAPI(listId: string, documentId: string) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach/${listId}/tai-lieu/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa khỏi danh sách thất bại");
  return data;
}

