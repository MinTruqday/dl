import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function exportDocumentPdfAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat/${documentId}/pdf`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất bản sao PDF thất bại");
  }
  return res.blob();
}

export async function exportDocumentDocxAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat/${documentId}/docx`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất bản sao Word thất bại");
  }
  return res.blob();
}
