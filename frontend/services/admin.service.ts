import { API_URL, getToken } from './auth.service';

export async function getApprovalQueueAPI(skip: number = 0, limit: number = 30) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/approval-queue?skip=${skip}&limit=${limit}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải hàng chờ phê duyệt.");
    return await res.json();
}

export async function getReportsAPI(status: string = "pending", skip: number = 0, limit: number = 30) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/reports?status=${status}&skip=${skip}&limit=${limit}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
    return await res.json();
}

export async function moderateDocumentAPI(documentId: string, action: string, reason: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/documents/${documentId}/moderate`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action, reason })
    });
    if (!res.ok) throw new Error("Thao tác phê duyệt thất bại.");
    return await res.json();
}

export async function getAdminReportsAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/reports`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
    return await res.json();
}

export async function resolveReportAPI(reportId: string, action: string) {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/reports/${reportId}/resolve`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action })
    });
    if (!res.ok) throw new Error("Thao tác xử lý báo cáo thất bại.");
    return await res.json();
}

export async function getModeratorActivityAPI() {
    const token = getToken();
    if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
    const res = await fetch(`${API_URL}/moderation/activity`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Không thể tải nhật ký hoạt động.");
    return await res.json();
}

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
export async function createReportAPI(payload: { item_id: string; item_type: string; reason: string; description?: string }) {
    const token = getToken();
    const res = await fetch(`${API_URL}/moderation/report`, {
        method: "POST",
        headers: { 
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || "Không thể gửi báo cáo vào lúc này.");
    }
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
