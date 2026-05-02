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
