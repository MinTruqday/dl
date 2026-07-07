import {
  API_URL,
  getToken,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getUsersAPI(limit: number = 50, offset: number = 0) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/nguoi-dung?limit=${limit}&offset=${offset}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách người dùng");
  return data;
}

export async function createUserAPI(data: { email: string, password: string, full_name: string, role: string }) {
  const { register } = await import("@/features/authentication/services/session.service");
  const slug = data.email.split("@")[0] + "-" + Math.floor(Math.random() * 10000);
  const newUser = await register(data.email, data.password, data.full_name, slug, true);
  
  if (data.role !== "reader" && newUser.id) {
    await updateUserRoleAPI(newUser.id, data.role);
  }
  return newUser;
}

export async function updateUserRoleAPI(userId: string, role: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}/vai-tro`, {
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
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}/status`, {
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
    `${API_URL}/nguoi-dung/tim-kiem?q=${encodeURIComponent(query)}&limit=${limit}`,
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
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa người dùng thất bại");
  return data;
}
