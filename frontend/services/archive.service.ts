import { API_URL, getToken } from "./authentication.service";

export async function getArchiveAPI(type: string = "all") {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru?type=${type}`, {
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách tệp tin");
  return data;
}

export async function uploadArchiveAPI(data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể lưu trữ tệp tin");
  return result;
}

export async function deleteArchiveAPI(archiveId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể xóa tệp tin");
  return result;
}

export async function uploadDocumentFileAPI(file: File) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/tai-len/tai-lieu`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tải tài liệu");
  return data;
}

export async function getFileDownloadUrlAPI(filePath: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${encodeURIComponent(filePath)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể lấy đường dẫn tải xuống");
  return data.download_url;
}

export async function uploadImageAPI(file: File) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/tai-len/hinh-anh`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tải hình ảnh");
  return data;
}

export async function uploadMediaAPI(formData: FormData) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/social/upload-media`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tải tệp tin lên thất bại.");
  return data;
}
