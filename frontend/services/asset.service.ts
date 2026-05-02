import { API_URL, getToken } from './auth.service';

export async function getAuthorAssetsAPI(type: string = "all") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/assets?type=${type}`, {
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách tài nguyên.");
    return await res.json();
}

export async function uploadAuthorAssetAPI(data: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/assets`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Không thể tải lên tài nguyên.");
    return await res.json();
}

export async function deleteAuthorAssetAPI(assetId: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/assets/${assetId}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("Không thể xóa tài nguyên.");
    return await res.json();
}
