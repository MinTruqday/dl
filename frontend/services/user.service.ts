import { API_URL, getToken } from './auth.service';

export async function getAdminUsersAPI(limit: number = 50, offset: number = 0) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/users?limit=${limit}&offset=${offset}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách người dùng.");
    return await res.json();
}

export async function updateUserRoleAPI(userId: string, role: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/users/${userId}/role`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ role })
    });
    if (!res.ok) throw new Error("Cập nhật quyền thất bại.");
    return await res.json();
}

export async function updateUserStatusAPI(userId: string, isActive: boolean) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/users/${userId}/status`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ is_active: isActive })
    });
    if (!res.ok) throw new Error("Cập nhật trạng thái tài khoản thất bại.");
    return await res.json();
}
