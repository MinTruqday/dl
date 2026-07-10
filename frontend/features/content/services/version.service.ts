import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getDocumentVersionsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/phien-ban/tai-lieu/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất bộ sưu tập lịch sử phiên bản");
  return data.data || data;
}

export async function saveVersionAPI(documentId: string, versionNote: string) {
  const res = await fetch(
    `${API_URL}/phien-ban/luu/${documentId}?version_note=${encodeURIComponent(versionNote)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi kết xuất bản sao cấu trúc phiên bản");
  return data.data || data;
}

export async function restoreVersionAPI(versionId: string) {
  const res = await fetch(`${API_URL}/phien-ban/${versionId}/khoi-phuc`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi phục hồi dữ liệu từ bản sao lưu");
  return data.data || data;
}
