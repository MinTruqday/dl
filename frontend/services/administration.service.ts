import { API_URL, getToken } from './auth.service';

export async function getAuthorApplicationsAPI(status: string = "PENDING") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/applications/authors?status=${status}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách đơn ứng tuyển.");
    return await res.json();
}

export async function reviewAuthorApplicationAPI(applicationId: string, status: string, reason: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/applications/authors/${applicationId}/review`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status, reason })
    });
    if (!res.ok) throw new Error("Thao tác xử lý hồ sơ thất bại.");
    return await res.json();
}

export async function getAdminConfigAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/config`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải cấu hình hệ thống.");
    return await res.json();
}

export async function updateAdminConfigAPI(config: any) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/config`, {
        method: "PUT",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error("Cập nhật cấu hình thất bại.");
    return await res.json();
}

export async function getSystemHealthAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/sys-health`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể kiểm tra sức khỏe hệ thống.");
    return await res.json();
}

export async function getMaintenanceModeAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/maintenance`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải trạng thái bảo trì.");
    return await res.json();
}

export async function toggleMaintenanceModeAPI(enabled: boolean, message: string = "Hệ thống đang bảo trì.") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/maintenance`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ enabled, message })
    });
    if (!res.ok) throw new Error("Thao tác chuyển đổi bảo trì thất bại.");
    return await res.json();
}

export async function triggerBackupAPI(action: string = "dump") {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/backup`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error("Khởi tạo sao lưu thất bại.");
    return await res.json();
}

export async function triggerCollectionAPI(source: string, url: string, index_type: string, target_class: string) {
    const token = getToken();
    const res = await fetch(`${API_URL}/administration/collector/trigger`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ source, url, index_type, target_class })
    });
    if (!res.ok) throw new Error("Không thể kích hoạt tiến trình thu thập.");
    return await res.json();
}

export async function getCollectorStatsAPI() {
    const token = getToken();
    const res = await fetch(`${API_URL}/administration/collector/stats`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải trạng thái thu thập.");
    return await res.json();
}

export async function getPayoutsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/payouts`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách thanh toán.");
    return await res.json();
}

export async function reviewPayoutAPI(payoutId: string, status: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/payouts/${payoutId}/review?status=${status}`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Thao tác phê duyệt thanh toán thất bại.");
    return await res.json();
}

export async function getBannersAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/banners`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách banner.");
    return await res.json();
}

export async function deleteBannerAPI(id: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/administration/banners/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể xóa banner.");
    return await res.json();
}
