import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getMyProfileAPI() {
  const res = await fetch(`${API_URL}/ho-so/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải thông tin định danh cá nhân",
    );
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
  if (!res.ok)
    throw new Error(result.message || "Không thể lưu dữ liệu hồ sơ cá nhân");
  return result;
}

export async function applyForAuthorAPI(motivation: string, portfolio: string) {
  const res = await fetch(`${API_URL}/ho-so/tac-gia/ung-tuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ motivation, portfolio }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể gửi hồ sơ tác giả");
  return data;
}

export async function deleteMyAccountAPI() {
  const res = await fetch(`${API_URL}/ho-so/xoa-tai-khoan`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể xóa tài khoản");
  return data;
}
