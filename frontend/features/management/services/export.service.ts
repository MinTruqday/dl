import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function exportDocumentPdfAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ket-xuat/${documentId}/pdf`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Lỗi kết xuất tài liệu định dạng PDF");
  }
  return res.blob();
}

export async function exportDocumentDocxAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ket-xuat/${documentId}/docx`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Lỗi kết xuất tài liệu định dạng Word");
  }
  return res.blob();
}

export async function exportProtectedDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ket-xuat/${documentId}/drm`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      data.message || data.detail || "Không thể kết xuất tài liệu bảo mật",
    );
  }
  return {
    blob: await res.blob(),
    contentDisposition: res.headers.get("content-disposition") || "",
  };
}
