import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getMyProfileAPI() {
  const res = await fetch(`${API_URL}/profile/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông tin hồ sơ");
  return data;
}

export async function updateMyProfileAPI(data: {
  full_name?: string;
  bio?: string;
  avatar_url?: string;
  cover_url?: string;
  location?: string;
  website?: string;
}) {
  const res = await fetch(`${API_URL}/profile/ca-nhan`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật hồ sơ thất bại");
  return result;
}

export async function getUserProfileAPI(slug: string) {
  const res = await fetch(`${API_URL}/profile/thanh-vien/${slug}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông tin thành viên");
  return data;
}

export async function getReadingStreaksAPI() {
  const res = await fetch(`${API_URL}/profile/chuoi-ngay`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải chuỗi ngày đọc");
  return data;
}

export async function getBadgesAPI() {
  const res = await fetch(`${API_URL}/profile/huy-hieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách huy hiệu");
  return data;
}

