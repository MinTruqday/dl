import { API_URL, getToken } from './auth.service';

export const getConversationsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách hội thoại.");
    return await res.json();
};

export const getMessagesAPI = async (otherUserId: string, limit: number = 50) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/messages/${otherUserId}?limit=${limit}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải lịch sử tin nhắn.");
    return await res.json();
};

export const sendMessageAPI = async (receiverId: string, content: string) => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ receiver_id: receiverId, content })
    });
    if (!res.ok) throw new Error("Không thể gửi tin nhắn.");
    return await res.json();
};
