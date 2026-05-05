import { API_URL, getAuthHeaders } from "./auth.service";

export async function getApprovalQueueAPI() {
  const res = await fetch(`${API_URL}/drafts/queue`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách phê duyệt.");
  return await res.json();
}

export async function moderateDocumentAPI(
  documentId: string,
  action: string,
  reason: string = "",
) {
  const res = await fetch(
    `${API_URL}/drafts/${documentId}/moderate`,
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
