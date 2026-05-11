import { API_URL, getAuthHeaders } from "./authentication.service";

export async function updateTypographyAPI(data: {
  font_family: string;
  font_size?: number;
  line_height?: number;
  letter_spacing?: number;
}) {
  const res = await fetch(`${API_URL}/doc/trinh-bay`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật hiển thị thất bại");
  return result;
}

export async function getReadingHistoryAPI(skip: number = 0, limit: number = 20) {
  const res = await fetch(`${API_URL}/doc/lich-su?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử đọc");
  return data;
}

export async function updateReadingProgressAPI(data: {
  document_id: string;
  progress_percentage: number;
  current_chapter_slug?: string;
}) {
  const res = await fetch(`${API_URL}/doc/tien-do`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật tiến độ thất bại");
  return result;
}

export async function getContinueReadingAPI() {
  const res = await fetch(`${API_URL}/doc/dang-doc`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách đang đọc");
  return data;
}

export async function setReadingGoalAPI(data: {
  target_documents?: number;
  target_pages?: number;
  period?: string;
}) {
  const res = await fetch(`${API_URL}/doc/muc-tieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Thiết lập mục tiêu thất bại");
  return result;
}

export async function getReadingGoalAPI() {
  const res = await fetch(`${API_URL}/doc/muc-tieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông tin mục tiêu");
  return data;
}

export async function getPinnedDocumentsAPI() {
  const res = await fetch(`${API_URL}/ghim`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách ghim");
  return data;
}

export async function pinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ghim/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghim tài liệu thất bại");
  return data;
}

export async function unpinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ghim/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bỏ ghim tài liệu thất bại");
  return data;
}

export async function searchInDocumentAPI(documentId: string, query: string) {
  const res = await fetch(`${API_URL}/doc/tai-lieu/${documentId}/tim-kiem?q=${encodeURIComponent(query)}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm kiếm trong tài liệu thất bại");
  return data;
}

export async function getHighlightsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc/diem-nhan/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách điểm nhấn");
  return data;
}

export async function createHighlightAPI(data: {
  document_id: string;
  selection_range: any;
  text: string;
  color?: string;
  note?: string;
}) {
  const res = await fetch(`${API_URL}/doc/diem-nhan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo điểm nhấn thất bại");
  return result;
}

export async function deleteHighlightAPI(highlightId: string) {
  const res = await fetch(`${API_URL}/doc/diem-nhan/${highlightId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa điểm nhấn thất bại");
  return data;
}

export async function toggleBookmarkAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc/danh-dau/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thao tác đánh dấu thất bại");
  return data;
}

export async function getBookmarksAPI() {
  const res = await fetch(`${API_URL}/ho-so/danh-dau`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bộ sưu tập");
  return data;
}

export async function getBookmarkFoldersAPI() {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách thư mục");
  return data;
}

export async function createBookmarkFolderAPI(name: string) {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tạo thư mục mới");
  return data;
}

export async function getReadingListsAPI() {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách bộ sưu tập");
  return data;
}

export async function createReadingListAPI(data: { title: string; description?: string }) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể tạo danh sách đọc mới");
  return result;
}

export async function clearReadingHistoryAPI() {
  const res = await fetch(`${API_URL}/reader/history`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa lịch sử thất bại");
  return data;
}

export async function deleteReadingHistoryItemAPI(documentId: string) {
  const res = await fetch(`${API_URL}/reader/history/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa mục lịch sử thất bại");
  return data;
}

export async function getMySeriesAPI() {
  const res = await fetch(`${API_URL}/tai-lieu/chuoi-tai-lieu/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách chuỗi tài liệu");
  return data;
}

export async function createSeriesAPI(data: { title: string; description: string; document_ids: string[] }) {
  const res = await fetch(`${API_URL}/tai-lieu/chuoi-tai-lieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể tạo chuỗi tài liệu mới");
  return result;
}
