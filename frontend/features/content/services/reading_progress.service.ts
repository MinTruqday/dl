import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function getReadingHistoryAPI(
  skip: number = 0,
  limit: number = 20,
) {
  const res = await fetch(
    `${API_URL}/doc-sach/lich-su?skip=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử đọc");
  return data;
}

export async function updateReadingProgressAPI(data: {
  document_id: string;
  progress_percentage: number;
  current_chapter_slug?: string;
}) {
  const res = await fetch(`${API_URL}/doc-sach/tien-do`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật tiến độ thất bại");
  return result;
}

export async function getPinnedDocumentsAPI() {
  const res = await fetch(`${API_URL}/to-dam`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách ghim");
  return data;
}

export async function pinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/to-dam/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghim tài liệu thất bại");
  return data;
}

export async function unpinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/to-dam/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bỏ ghim tài liệu thất bại");
  return data;
}

export async function searchInDocumentAPI(documentId: string, query: string) {
  const res = await fetch(
    `${API_URL}/doc-sach/tai-lieu/${documentId}/tim-kiem?q=${encodeURIComponent(query)}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Tìm kiếm trong tài liệu thất bại");
  return data;
}

export async function clearReadingHistoryAPI() {
  const res = await fetch(`${API_URL}/doc-sach/lich-su`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa lịch sử thất bại");
  return data;
}

export async function deleteReadingHistoryItemAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc-sach/lich-su/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa mục lịch sử thất bại");
  return data;
}
