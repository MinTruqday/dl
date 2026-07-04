import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getMyProfileAPI() {
  const res = await fetch(`${API_URL}/ho-so/ca-nhan`, {
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
  const res = await fetch(`${API_URL}/ho-so/ca-nhan`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Cập nhật hồ sơ thất bại");
  return result;
}

export async function getUserProfileAPI(slug: string) {
  const res = await fetch(`${API_URL}/ho-so/member/${slug}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thông tin thành viên");
  return data;
}

