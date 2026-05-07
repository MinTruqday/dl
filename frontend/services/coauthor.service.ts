import { API_URL, getAuthHeaders } from "./authentication.service";

export async function inviteCoauthorAPI(documentId: string, targetUserId: string) {
  const res = await fetch(`${API_URL}/dong-tac-gia/moi/${documentId}?target_user_id=${targetUserId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi lời mời đồng tác giả thất bại");
  return data;
}

export async function getCoauthorInvitesAPI() {
  const res = await fetch(`${API_URL}/dong-tac-gia/loi-moi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách lời mời cộng tác");
  return data;
}
