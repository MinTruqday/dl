import { API_URL, getAuthHeaders } from "./authentication.service";

export async function exportDocumentPdfAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat-tai-lieu/${documentId}/pdf`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất bản sao PDF thất bại");
  }
  return res.blob();
}

export async function exportDocumentEpubAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat-tai-lieu/${documentId}/epub`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất bản sao EPUB thất bại");
  }
  return res.blob();
}
