import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getDocumentVersionsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/version/document/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách phiên bản");
  return data.data || data;
}

export async function saveVersionAPI(documentId: string, versionNote: string) {
  const res = await fetch(
    `${API_URL}/version/save/${documentId}?version_note=${encodeURIComponent(versionNote)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lưu phiên bản thất bại");
  return data.data || data;
}

export async function restoreVersionAPI(versionId: string) {
  const res = await fetch(`${API_URL}/version/${versionId}/khoi-phuc`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Khôi phục phiên bản thất bại");
  return data.data || data;
}
