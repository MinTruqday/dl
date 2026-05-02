import { API_URL, getToken } from './auth.service';

export async function getLeaderboardAPI() {
    const token = getToken();
    const headers: any = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}/social/ranking`, { headers });
    if (!res.ok) throw new Error("Không thể tải bảng xếp hạng.");
    return await res.json();
}

export async function getAuthorStatsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/wallet/revenue`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải thông số phân tích.");
    return await res.json();
}

export async function getAuthorDemographicsAPI() {
    const token = getToken();
    const res = await fetch(`${API_URL}/social/ranking`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải dữ liệu nhân khẩu học.");
    return await res.json();
}
