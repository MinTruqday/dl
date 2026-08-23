import { API_URL, authenticatedFetch } from "@/shared/services/api-client";
export async function getDocumentDraftAPI(documentId) {
  const response = await authenticatedFetch(`${API_URL}/tai-lieu/${documentId}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Không thể tải dữ liệu bản thảo");
  return data;
}
export async function getMyDocumentsAPI(search = "", cursor = "", limit = 50) {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (search) params.append("q", search);
  if (cursor) params.append("cursor", cursor);
  const response = await authenticatedFetch(`${API_URL}/tai-lieu/ca-nhan?${params.toString()}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Không thể tải danh sách tài liệu cá nhân");
  return data.data || data;
}
export async function createDocumentAPI(data) {
  const response = await authenticatedFetch(`${API_URL}/tai-lieu`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Không thể tạo tài liệu mới");
  return result;
}
export async function updateDocumentAPI(id, data) {
  const response = await authenticatedFetch(`${API_URL}/tai-lieu/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Không thể cập nhật tài liệu");
  return result;
}
export async function retryDocumentIndexingAPI(id) {
  const response = await authenticatedFetch(`${API_URL}/tai-lieu/${id}/lap-chi-muc-lai`, {
    method: "POST",
  });
  const result = await response.json();
  if (!response.ok)
    throw new Error(result.detail || result.message || "Không thể lập chỉ mục lại tài liệu");
  return result;
}
export async function deleteAuthorDocumentAPI(id) {
  const response = await authenticatedFetch(`${API_URL}/tai-lieu/${id}`, {
    method: "DELETE",
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Không thể xóa tài liệu");
  return result;
}
