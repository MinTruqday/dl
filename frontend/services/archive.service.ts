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

export async function renameArchiveAPI(archiveId: string, filename: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/doi-ten`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ filename }),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể đổi tên tệp tin");
  return result;
}

export async function togglePinArchiveAPI(archiveId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/ghim`, {
    method: "PATCH",
    headers: { Authorization: "Bearer " + token },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể thay đổi trạng thái ghim");
  return result;
}

export async function restoreArchiveAPI(archiveId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/khoi-phuc`, {
    method: "PATCH",
    headers: { Authorization: "Bearer " + token },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể khôi phục tệp tin");
  return result;
}

export async function permanentlyDeleteArchiveAPI(archiveId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/vinh-vien`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể xóa vĩnh viễn tệp tin");
  return result;
}

export async function updateArchiveDescriptionAPI(archiveId: string, description: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/mo-ta`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ description }),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể cập nhật mô tả tệp tin");
  return result;
}

export async function toggleArchiveVisibilityAPI(archiveId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/rieng-tu`, {
    method: "PATCH",
    headers: { Authorization: "Bearer " + token },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể thay đổi trạng thái hiển thị");
  return result;
}

export async function shareArchiveAPI(archiveId: string, email: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/chia-se`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ email }),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể chia sẻ tệp tin");
  return result;
}

export async function updateArchiveTagsAPI(archiveId: string, tags: string[]) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/luu-tru/${archiveId}/nhan`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ tags }),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể cập nhật danh sách nhãn");
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
  const res = await fetch(`${API_URL}/tai-len/luu-tru/${encodeURIComponent(filePath)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể lấy đường dẫn tải xuống");
  return data.data?.download_url || data.download_url;
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
