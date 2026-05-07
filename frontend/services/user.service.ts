import { API_URL, getToken, getAuthHeaders } from "./authentication.service";

export async function getAdminUsersAPI(limit: number = 50, offset: number = 0) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/nguoi-dung?limit=${limit}&offset=${offset}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách người dùng");
  return data;
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
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}/trang-thai`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ is_active: isActive }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật trạng thái tài khoản thất bại");
  return data;
}



export const searchUsersAPI = async (query: string, limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/cong-dong/tim-kiem-nguoi-dung?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tìm kiếm người dùng");
  return data;
};

export async function followUserAPI(userId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thực hiện thao tác này");
  const res = await fetch(`${API_URL}/cong-dong/nguoi-dung/${userId}/nguoi-theo-doi`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Theo dõi người dùng thất bại");
  return data;
}

export async function muteUserAPI(userId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/cong-dong/nguoi-dung/${userId}/tam-an`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạm ẩn người dùng thất bại");
  return data;
}

export async function blockUserAPI(userId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/cong-dong/nguoi-dung/${userId}/chan`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chặn người dùng thất bại");
  return data;
}
