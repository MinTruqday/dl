import { API_URL, getToken } from "./authentication.service";

export const getConversationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tro-chuyen/hoi-thoai`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách hội thoại");
  return data;
};

export const getMessagesAPI = async (
  otherUserId: string,
  limit: number = 50,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/tro-chuyen/tin-nhan/${otherUserId}?limit=${limit}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử tin nhắn");
  return data;
};

export const sendMessageAPI = async (receiverId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tro-chuyen/tin-nhan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ receiver_id: receiverId, content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi tin nhắn thất bại");
  return data;
};
