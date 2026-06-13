import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getActiveBannersAPI() {
  const res = await fetch(`${API_URL}/banner`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách biểu ngữ");
  return data;
}

export async function getAllBannersAPI() {
  const res = await fetch(`${API_URL}/banner/tat-ca`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải toàn bộ danh sách biểu ngữ");
  return data;
}

export async function createBannerAPI(data: {
  title: string;
  image_url: string;
  link_url?: string;
  priority?: number;
}) {
  const res = await fetch(`${API_URL}/banner`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo biểu ngữ thất bại");
  return result;
}

export async function deleteBannerAPI(id: string) {
  const res = await fetch(`${API_URL}/banner/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xoá biểu ngữ thất bại");
  return data;
}
