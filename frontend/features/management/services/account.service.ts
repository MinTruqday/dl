import {
  API_URL,
  getAuthHeaders,
  removeToken,
} from "@/features/authentication/services/session.service";

export async function getMyProfileAPI() {
  const res = await fetch(`${API_URL}/ho-so/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi trích xuất thông tin định danh cá nhân");
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
  if (!res.ok) throw new Error(result.message || "Lỗi lưu trữ dữ liệu hồ sơ cá nhân");
  return result;
}

export async function getUserProfileAPI(slug: string) {
  const res = await fetch(`${API_URL}/ho-so/member/${slug}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất hồ sơ thành viên hệ thống");
  return data;
}

export async function applyForAuthorAPI(
  motivation: string,
  portfolio: string,
) {
  const res = await fetch(`${API_URL}/ho-so/tac-gia/ung-tuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ motivation, portfolio }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.detail || "Không thể gửi yêu cầu");
  }
  return data;
}

export async function deleteMyAccountAPI() {
  const res = await fetch(`${API_URL}/ho-so/xoa-tai-khoan`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || data.detail || "Không thể xóa tài khoản");
  }
  removeToken();
  return data;
}
