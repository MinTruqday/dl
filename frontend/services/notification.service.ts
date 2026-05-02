import { API_URL, getToken } from './auth.service';

export const getNotificationsAPI = async () => {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải thông báo.");
    return await res.json();
};

export const markNotificationReadAPI = async (id: string) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể đánh dấu thông báo.");
    return await res.json();
};

export const markAllNotificationsReadAPI = async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/mark-all-read`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể đánh dấu tất cả thông báo.");
    return await res.json();
};

export const getNotificationSettingsAPI = async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/settings`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải cấu hình thông báo.");
    return await res.json();
};

export const updateNotificationSettingsAPI = async (settings: any) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/notifications/settings`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error("Không thể cập nhật cấu hình thông báo.");
    return await res.json();
};
