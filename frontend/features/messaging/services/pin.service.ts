import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

const authorizedHeaders = () => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  return { Authorization: `Bearer ${token}` };
};

export const togglePinAPI = async (messageId: string) => {
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/ghim`, {
    method: "POST",
    headers: authorizedHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật trạng thái ghim");
  return data;
};

export const togglePinConversationAPI = async (otherUserId: string) => {
  const res = await fetch(
    `${API_URL}/tin-nhan/cuoc-tro-chuyen/${otherUserId}/ghim`,
    { method: "POST", headers: authorizedHeaders() },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật trạng thái ghim cuộc trò chuyện",
    );
  return data;
};

export const getPinnedMessagesAPI = async (otherUserId: string) => {
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tin-nhan-ghim`, {
    headers: authorizedHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải tin nhắn đã ghim");
  return data;
};
