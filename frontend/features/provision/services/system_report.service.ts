import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function getReportsAPI(
  status: string = "pending",
  skip: number = 0,
  limit: number = 30,
) {
  const res = await fetch(
    `${API_URL}/van-hanh/bao-cao/hang-doi?status=${status}&skip=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách báo cáo");
  return data;
}

export async function resolveReportAPI(reportId: string, action: string) {
  const res = await fetch(`${API_URL}/van-hanh/bao-cao/${reportId}/resolve`, {
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

export async function submitReportAPI(payload: {
  item_id: string;
  item_type: string;
  reason: string;
  detail: string;
}) {
  const res = await fetch(`${API_URL}/phan-hoi/bao-cao`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_id: payload.item_id,
      item_type: payload.item_type,
      reason: payload.reason,
      description: payload.detail,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi báo cáo thất bại");
  return data;
}
