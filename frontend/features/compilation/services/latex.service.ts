import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function cleanTempFilesAPI() {
  const res = await fetch(`${API_URL}/soan-thao/latex/don-dep`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi giải phóng bộ nhớ đệm tập tin tạm");
  return data;
}

export async function cloudAutoSaveAPI(documentId: string, content: string) {
  const res = await fetch(`${API_URL}/soan-thao/latex/tu-dong-luu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, content }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể đồng bộ hóa dữ liệu mã nguồn tự động",
    );
  return data;
}

export async function getLatexDraftAPI() {
  const res = await fetch(`${API_URL}/soan-thao/latex/ban-nhap`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải bộ đệm dữ liệu nháp");
  return data;
}

export async function compileLatexPreviewAPI(
  content: string,
  isFragment: boolean = false,
) {
  const res = await fetch(`${API_URL}/soan-thao/latex/bien-dich`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, is_fragment: isFragment }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(
      data.message || "Không thể thực hiện tiến trình kết xuất LaTeX",
    );
  }
  return res.blob();
}

export async function formatLatexAPI(content: string) {
  const res = await fetch(`${API_URL}/soan-thao/latex/dinh-dang`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thực hiện tiến trình chuẩn hóa cú pháp LaTeX",
    );
  return data;
}

export async function exportLatexAPI(content: string, format: string = "docx") {
  const res = await fetch(`${API_URL}/soan-thao/latex/ket-xuat/${format}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, format }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(
      data.message || "Không thể tạo luồng kết xuất tài liệu đích",
    );
  }
  return res.blob();
}

export async function exportProjectZipAPI(content: string) {
  const res = await fetch(`${API_URL}/soan-thao/latex/ket-xuat-zip`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(
      data.message || "Không thể tạo luồng nén và kết xuất dự án",
    );
  }
  return res.blob();
}
