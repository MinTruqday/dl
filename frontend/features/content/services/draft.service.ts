import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getApprovalQueueAPI() {
  const res = await fetch(`${API_URL}/draft/hang-doi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách phê duyệt");
  return data;
}

export async function moderateDocumentAPI(
  documentId: string,
  action: string,
  reason: string = "",
) {
  const res = await fetch(`${API_URL}/draft/${documentId}/kiem-duyet`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action, reason }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Thao tác kiểm duyệt thất bại");
  }
  return data;
}
