import { API_URL, getAuthHeaders } from "./authentication.service";

export async function inviteCollaboratorAPI(documentId: string, email: string, role: string = "editor") {
  const res = await fetch(`${API_URL}/cong-tac/moi`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, email, role }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi lời mời cộng tác thất bại");
  return data;
}

export async function getCollaboratorsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/cong-tac/tai-lieu/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách người cộng tác");
  return data;
}

export async function removeCollaboratorAPI(collaborationId: string) {
  const res = await fetch(`${API_URL}/cong-tac/${collaborationId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa người cộng tác thất bại");
  return data;
}
