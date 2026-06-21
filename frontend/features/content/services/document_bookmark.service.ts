import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function toggleBookmarkAPI(documentId: string) {
  const res = await fetch(`${API_URL}/danh-dau/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thao tác dấu trang thất bại");
  return data;
}

export async function getBookmarksAPI(limit: number = 100) {
  const res = await fetch(`${API_URL}/danh-dau?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách dấu trang");
  return data;
}

export async function createBookmarkFolderAPI(name: string) {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Tạo thư mục dấu trang thất bại");
  return data;
}

export async function getBookmarkFoldersAPI() {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách thư mục dấu trang",
    );
  return data;
}

export async function assignBookmarksToFolderAPI(
  folderId: string,
  bookmarkIds: string[],
) {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc/${folderId}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ bookmark_ids: bookmarkIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật thư mục thất bại");
  return data;
}

export async function deleteBookmarkFolderAPI(folderId: string) {
  const res = await fetch(`${API_URL}/danh-dau/thu-muc/${folderId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa thư mục thất bại");
  return data;
}
