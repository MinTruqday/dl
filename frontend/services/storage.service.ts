import { API_URL, getToken } from "./auth.service";

export async function uploadDocumentFile(file: File) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/storage/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Tải lên thất bại.");
  return data;
}

export async function getFileDownloadUrl(filePath: string) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(
    `${API_URL}/storage/${encodeURIComponent(filePath)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Lấy đường dẫn thất bại.");
  return data.download_url;
}

export async function uploadDocumentAPI(file: File) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/upload/document`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tải tài liệu.");
  return data;
}

export const getStorageQuotaAPI = async () => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/quota`, {
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể tải hạn mức dung lượng.");
  return data;
};

export async function uploadImageAPI(file: File) {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/upload/image/`, {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
    body: formData,
  });
  if (!res.ok) return null;
  return await res.json();
}

export async function uploadMediaAPI(file: File) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/upload/media/`, {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
    body: formData,
  });
  if (!res.ok) throw new Error("Tải phương tiện lên thất bại.");
  return await res.json();
}
