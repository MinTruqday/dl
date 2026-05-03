import { API_URL, getToken } from "./auth.service";

export async function getApprovalQueueAPI(
  skip: number = 0,
  limit: number = 30,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/governance/approval-queue?skip=${skip}&limit=${limit}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok)
    throw new Error("Giao thức truy xuất danh sách chờ phê duyệt thất bại");
  return await res.json();
}

export async function getReportsAPI(
  status: string = "pending",
  skip: number = 0,
  limit: number = 30,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/governance/compliance/reports?status=${status}&skip=${skip}&limit=${limit}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok)
    throw new Error("Giao thức truy xuất danh sách báo cáo thất bại");
  return await res.json();
}

export async function resolveDocumentApprovalAPI(
  documentId: string,
  action: string,
  reason: string,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/governance/documents/${documentId}/resolve`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action, reason }),
    },
  );
  if (!res.ok) throw new Error("Giao thức phê duyệt thực thể thất bại");
  return await res.json();
}

export async function resolveReportAPI(reportId: string, action: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/governance/compliance/reports/${reportId}/resolve`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action }),
    },
  );
  if (!res.ok) throw new Error("Giao thức xử lý báo cáo thất bại");
  return await res.json();
}

export async function submitReportAPI(payload: {
  item_id: string;
  item_type: string;
  reason: string;
  detail?: string;
}) {
  const token = getToken();
  const res = await fetch(`${API_URL}/governance/compliance/reports`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "Giao thức gửi báo cáo vi phạm thất bại");
  }
  return await res.json();
}
