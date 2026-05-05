import { API_URL, getAuthHeaders } from "./auth.service";

export async function getReportsAPI() {
  const res = await fetch(`${API_URL}/reports/queue`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách báo cáo.");
  return await res.json();
}

export async function resolveReportAPI(reportId: string, action: string) {
  const res = await fetch(`${API_URL}/reports/${reportId}/resolve`, {
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

export async function submitReportAPI(payload: {
  item_id: string;
  item_type: string;
  reason: string;
  description?: string;
}) {
  const res = await fetch(`${API_URL}/feedback/report`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Giao thức gửi báo cáo vi phạm thất bại");
  }
  return await res.json();
}
