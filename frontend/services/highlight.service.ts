import { API_URL, getAuthHeaders } from "./authentication.service";

export async function createHighlightAPI(documentId: string, data: {
  text: string;
  chapter_slug?: string;
  color?: string;
  start_offset?: number;
  end_offset?: number;
  note?: string;
}) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/tai-lieu/${documentId}/danh-dau`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo đánh dấu thất bại");
  return result;
}

export async function getHighlightsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/tai-lieu/${documentId}/danh-dau`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách đánh dấu");
  return data;
}

export async function updateHighlightNoteAPI(highlightId: string, note: string) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/danh-dau/${highlightId}/ghi-chu`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật ghi chú thất bại");
  return data;
}

export async function deleteHighlightAPI(highlightId: string) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/danh-dau/${highlightId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa đánh dấu thất bại");
  return data;
}

export async function getAllNotesAPI(skip: number = 0, limit: number = 50) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/ghi-chu?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách ghi chú");
  return data;
}

export async function getReadingPreferencesAPI() {
  const res = await fetch(`${API_URL}/doc-tai-lieu/tuy-chinh`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải cài đặt tùy chỉnh đọc");
  return data;
}

export async function updateReadingPreferencesAPI(data: {
  theme?: string;
  font_size?: number;
  line_height?: number;
  font_family?: string;
  is_dyslexic_mode?: boolean;
}) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/tuy-chinh`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật cài đặt đọc thất bại");
  return result;
}

export async function exportHighlightsMarkdownAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc-tai-lieu/tai-lieu/${documentId}/danh-dau/xuat-tai-lieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xuất dữ liệu đánh dấu thất bại");
  return data;
}
