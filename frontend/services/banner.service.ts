import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getActiveBannersAPI() {
  const res = await fetch(`${API_URL}/anh-quang-cao`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách banner");
  return data;
}

export async function getAllBannersAPI() {
  const res = await fetch(`${API_URL}/anh-quang-cao/tat-ca`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải toàn bộ danh sách banner");
  return data;
}

export async function createBannerAPI(data: {
  title: string;
  image_url: string;
  link_url?: string;
  priority?: number;
}) {
  const res = await fetch(`${API_URL}/anh-quang-cao`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo banner thất bại");
  return result;
}

export async function deleteBannerAPI(id: string) {
  const res = await fetch(`${API_URL}/anh-quang-cao/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa banner thất bại");
  return data;
}
