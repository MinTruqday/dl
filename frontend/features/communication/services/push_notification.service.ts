import {
  API_URL,
  getToken,
  getAuthHeaders,
} from "@/features/auth/services/user_authentication.service";

export const getNotificationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/thong-bao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const resultData = await res.json();
  if (!res.ok) throw new Error(resultData.message || "Không thể tải thông báo");
  return resultData;
};

export const markNotificationReadAPI = async (id: string) => {
  const res = await fetch(`${API_URL}/thong-bao/${id}/doc-hieu`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(resultData.message || "Không thể đánh dấu thông báo");
  return resultData;
};

export const markAllNotificationsReadAPI = async () => {
  const res = await fetch(`${API_URL}/thong-bao/doc-tat-ca`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(
      resultData.message || "Không thể đánh dấu tất cả thông báo",
    );
  return resultData;
};

export const getNotificationSettingsAPI = async () => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể tải cấu hình thông báo.");
  return await res.json();
};

export const updateNotificationSettingsAPI = async (settings: any) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error("Không thể cập nhật cấu hình thông báo.");
  return await res.json();
};
