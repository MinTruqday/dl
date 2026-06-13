import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function updateTypographyAPI(data: {
  font_family: string;
  font_size?: number;
  line_height?: number;
  letter_spacing?: number;
}) {
  const res = await fetch(`${API_URL}/doc-sach/giao-dien`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật hiển thị thất bại");
  return result;
}

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

export async function setReadingGoalAPI(data: {
  target_documents?: number;
  target_pages?: number;
  period?: string;
}) {
  const res = await fetch(`${API_URL}/doc-sach/muc-tieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Thiết lập mục tiêu thất bại");
  return result;
}

export async function getReadingGoalAPI() {
  const res = await fetch(`${API_URL}/doc-sach/muc-tieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thông tin mục tiêu");
  return data;
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

export async function getMySeriesAPI() {
  const res = await fetch(`${API_URL}/tai-lieu/series/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách chuỗi tài liệu");
  return data;
}

export async function createSeriesAPI(data: {
  title: string;
  description: string;
  document_ids: string[];
}) {
  const res = await fetch(`${API_URL}/tai-lieu/series`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Không thể tạo chuỗi tài liệu mới");
  return result;
}
