import { API_URL, getToken, getAuthHeaders } from "@/features/auth/services/authentication.service";

export const getNotificationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/notification`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông báo");
  return data;
};

export const markNotificationReadAPI = async (id: string) => {
  const res = await fetch(`${API_URL}/notification/${id}/da-doc`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đánh dấu thông báo");
  return data;
};

export const markAllNotificationsReadAPI = async () => {
  const res = await fetch(`${API_URL}/notification/read-all`, {
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
  const res = await fetch(`${API_URL}/notification/settings`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu hình thông báo");
  return data;
};

export const updateNotificationSettingsAPI = async (settings: any) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/notification/settings`, {
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
