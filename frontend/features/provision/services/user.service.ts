import { API_URL, getToken, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getAdminUsersAPI(limit: number = 50, offset: number = 0) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/user?limit=${limit}&offset=${offset}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách người dùng");
  return data;
}

export async function updateUserRoleAPI(userId: string, role: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/user/${userId}/role`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật quyền thất bại");
  return data;
}

export async function updateUserStatusAPI(userId: string, isActive: boolean) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/user/${userId}/status`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ is_active: isActive }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Cập nhật trạng thái tài khoản thất bại");
  return data;
}

export async function searchUsersAPI(query: string, limit: number = 10) {
  const res = await fetch(
    `${API_URL}/user/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tìm kiếm người dùng");
  return data;
}

export async function deleteUserAPI(userId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/user/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa người dùng thất bại");
  return data;
}
