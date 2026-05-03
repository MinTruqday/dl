import { API_URL, getToken } from "./auth.service";

export async function getCollaborationInvitesAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/coauthor/invites`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể tải danh sách lời mời cộng tác.");
  return await res.json();
}

export async function inviteCollaboratorAPI(
  documentId: string,
  email: string,
  role: string,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/documents/${documentId}/coauthors`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ email, role }),
  });
  const json = await res.json();
  if (!res.ok)
    throw new Error(
      json.message || json.detail || "Không thể gửi lời mời cộng tác.",
    );
  return json;
}

export async function respondToInviteAPI(inviteId: string, status: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/coauthor/respond/${inviteId}?status=${status}`,
    {
      method: "POST",
      headers: { Authorization: "Bearer " + token },
    },
  );
  if (!res.ok) throw new Error("Không thể phản hồi lời mời cộng tác.");
  return await res.json();
}

export const inviteCoauthorAPI = async (
  documentId: string,
  targetUserId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(
    `${API_URL}/coauthor/invite/${documentId}?target_user_id=${targetUserId}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) throw new Error("Không thể gửi lời mời đồng tác giả.");
  return await res.json();
};
