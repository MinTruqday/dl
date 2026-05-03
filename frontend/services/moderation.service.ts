import { API_URL, getAuthHeaders, getToken } from "./auth.service";

export async function getApprovalQueueAPI() {
  const res = await fetch(`${API_URL}/moderation/approval-queue`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách phê duyệt.");
  return await res.json();
}

export async function getReportsAPI() {
  const res = await fetch(`${API_URL}/moderation/reports`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
  return await res.json();
}

export async function moderateDocumentAPI(
  documentId: string,
  action: string,
  reason: string = "",
) {
  const res = await fetch(
    `${API_URL}/moderation/documents/${documentId}/moderate`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action, reason }),
    },
  );
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Thao tác kiểm duyệt thất bại.");
  }
  return await res.json();
}

export async function resolveReportAPI(reportId: string, action: string) {
  const res = await fetch(`${API_URL}/moderation/reports/${reportId}/resolve`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) throw new Error("Xử lý báo cáo thất bại.");
  return await res.json();
}

export async function getModeratorActivityAPI() {
  // Backend chưa có endpoint logs riêng trong moderation router, dùng tạm audit logs của document
  const res = await fetch(`${API_URL}/moderation/audit-logs`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) return { data: [] }; // Fallback nếu không có quyền
  return await res.json();
}
