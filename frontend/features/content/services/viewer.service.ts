import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export class DocumentAccessError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function getDocumentForReadingAPI(
  documentId: string,
  password?: string,
) {
  const headers = getAuthHeaders();
  if (password) {
    headers["x-document-password"] = password;
  }
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}`, { headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new DocumentAccessError(
      res.status,
      data.message || data.detail || "Không thể mở tài liệu",
    );
  }
  return data.data || data;
}

export async function getDocumentDecryptionKeyAPI(documentId: string) {
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/khoa-giai-ma`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok || !data.data?.key) {
    throw new Error(data.message || data.detail || "Không thể lấy khóa giải mã");
  }
  return data.data.key as string;
}

export async function getZipTreeAPI(fileUrl: string) {
  const query = new URLSearchParams({ file_url: fileUrl });
  const res = await fetch(`${API_URL}/doc-sach/tree-zip?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.detail || "Không thể đọc tệp ZIP");
  }
  return data.data || [];
}

export async function getZipContentAPI(fileUrl: string, path: string) {
  const query = new URLSearchParams({ file_url: fileUrl, path });
  const res = await fetch(
    `${API_URL}/doc-sach/content-zip?${query.toString()}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) {
    throw new Error(
      data.message || data.detail || "Không thể đọc nội dung tệp ZIP",
    );
  }
  return data.data || {};
}
