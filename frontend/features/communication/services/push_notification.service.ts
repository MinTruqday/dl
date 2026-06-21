import { API_URL, getToken, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export const getNotificationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/thong-bao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông báo");
  return data;
};

export const markNotificationReadAPI = async (id: string) => {
  const res = await fetch(`${API_URL}/thong-bao/${id}/read`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đánh dấu thông báo");
  return data;
};

export const markAllNotificationsReadAPI = async () => {
  const res = await fetch(`${API_URL}/thong-bao/doc-tat-ca`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể đánh dấu tất cả thông báo");
  return data;
};

export const getNotificationSettingsAPI = async () => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu hình thông báo");
  return data;
};

export const updateNotificationSettingsAPI = async (settings: any) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật cấu hình thông báo");
  return data;
};
