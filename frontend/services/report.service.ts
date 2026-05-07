import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getReportsAPI(status: string = "pending", skip: number = 0, limit: number = 30) {
  const res = await fetch(`${API_URL}/bao-cao/hang-doi?status=${status}&skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách báo cáo");
  return data;
}

export async function resolveReportAPI(reportId: string, action: string) {
  const res = await fetch(`${API_URL}/bao-cao/${reportId}/giai-quyet`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý báo cáo thất bại");
  return data;
}
