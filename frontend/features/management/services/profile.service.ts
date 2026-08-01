import {
  API_URL,
  getToken,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getUsersAPI(limit: number = 50, offset: number = 0) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(
    `${API_URL}/nguoi-dung?limit=${limit}&offset=${offset}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tài khoản người dùng",
    );
  return data;
}

export async function createUserAPI(data: {
  email: string;
  password: string;
  full_name: string;
  role: string;
}) {
  const { register } =
    await import("@/features/authentication/services/session.service");
  const slug =
    data.email.split("@")[0] + "-" + Math.floor(Math.random() * 10000);
  const newUser = await register(
    data.email,
    data.password,
    data.full_name,
    slug,
    true,
  );

  const userId = newUser.id || newUser._id;
  if (data.role !== "reader" && userId) {
    await updateUserRoleAPI(userId, data.role);
  }
  return newUser;
}

export async function updateUserRoleAPI(userId: string, role: string) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}/vai-tro`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi phân quyền tài khoản người dùng");
  return data;
}

export async function updateUserStatusAPI(userId: string, isActive: boolean) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/nguoi-dung/${userId}/trang-thai`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ is_active: isActive }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật trạng thái hoạt động tài khoản",
    );
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
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy vấn dữ liệu người dùng");
  return data;
}

export async function deleteUserAPI(userId: string) {
  return updateUserStatusAPI(userId, false);
}

export async function updateUserShadowbanAPI(userId: string, status: boolean) {
  const res = await fetch(`${API_URL}/van-hanh/nguoi-dung/${userId}/cam-ngam`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail || data.message || "Không thể cập nhật quyền hiển thị",
    );
  return data;
}

export async function updateUserKycAPI(
  userId: string,
  status: "PENDING" | "VERIFIED" | "REJECTED",
) {
  const res = await fetch(
    `${API_URL}/van-hanh/nguoi-dung/${userId}/xac-minh/${status}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail || data.message || "Không thể cập nhật xác minh danh tính",
    );
  return data;
}
