const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getToken = () => {
  if (typeof window !== "undefined") {
    return (
      localStorage.getItem("token") ||
      localStorage.getItem("access_token") ||
      sessionStorage.getItem("token") ||
      ""
    );
  }
  return "";
};

export const togglePinAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/ghim`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật trạng thái dữ liệu ghim",
    );
  return data;
};

export const togglePinConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/cuoc-tro-chuyen/${otherUserId}/ghim`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật ưu tiên cuộc trò chuyện",
    );
  return data;
};

export const getPinnedMessagesAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tin-nhan-ghim`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tin nhắn ghim",
    );
  return data;
};
