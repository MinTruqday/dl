import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function cleanTempFilesAPI() {
  const res = await fetch(`${API_URL}/latex/don-dep`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Dọn dẹp tập tin tạm thời thất bại");
  return data;
}

export async function compileLatexPreviewAPI(
  content: string,
  isFragment: boolean = false,
) {
  const res = await fetch(`${API_URL}/latex/compile-preview`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, is_fragment: isFragment }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Biên dịch LaTeX thất bại");
  }
  return res.blob();
}

export async function formatLatexAPI(content: string) {
  const res = await fetch(`${API_URL}/latex/dinh-dang`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Định dạng mã nguồn LaTeX thất bại");
  return data;
}

export async function exportLatexAPI(content: string, format: string = "docx") {
  const res = await fetch(`${API_URL}/latex/xuat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, format }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất tài liệu thất bại");
  }
  return res.blob();
}

export async function cloudAutoSaveAPI(documentId: string, content: string) {
  const res = await fetch(`${API_URL}/latex/tu-dong-luu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tự động lưu mã nguồn thất bại");
  return data;
}

export async function exportProjectZipAPI(content: string) {
  const res = await fetch(`${API_URL}/latex/export-zip`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Xuất tệp nén dự án thất bại");
  }
  return res.blob();
}
