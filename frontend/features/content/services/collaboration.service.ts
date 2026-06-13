import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function inviteCollaboratorAPI(
  documentId: string,
  email: string,
  role: string = "editor",
) {
  const res = await fetch(`${API_URL}/collaboration/invite`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, email, role }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi lời mời cộng tác thất bại");
  return data;
}

export async function getCollaboratorsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/collaboration/document/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách người cộng tác");
  return data;
}

export async function removeCollaboratorAPI(collaborationId: string) {
  const res = await fetch(`${API_URL}/collaboration/${collaborationId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa người cộng tác thất bại");
  return data;
}

export async function getCollaborationInvitesAPI() {
  const res = await fetch(`${API_URL}/collaboration/invite`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách lời mời");
  return data;
}

export async function respondToInviteAPI(inviteId: string, status: string) {
  const res = await fetch(`${API_URL}/collaboration/invite/${inviteId}`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Phản hồi lời mời thất bại");
  return data;
}

export async function getCollaborationActivitiesAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/hoat-dong`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử hoạt động");
  return data;
}

export async function transferOwnershipAPI(documentId: string, userId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/transfer-owner`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chuyển quyền sở hữu thất bại");
  return data;
}

export async function pingCollaborationStatusAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/ping`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ping trạng thái thất bại");
  return data;
}

export async function getOnlineCollaboratorsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/online`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách trực tuyến");
  return data;
}

export async function updateCollaboratorRoleAPI(
  collaborationId: string,
  role: string,
) {
  const res = await fetch(
    `${API_URL}/collaboration/${collaborationId}/vai-tro`,
    {
      method: "PATCH",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Cập nhật vai trò cộng tác viên thất bại");
  return data;
}

export async function sendMemoAPI(documentId: string, message: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/message`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Gửi tin nhắn trao đổi thất bại");
  return data;
}

export async function getMemosAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/message`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nội dung trao đổi");
  return data;
}

export async function updateCollabAccessAPI(
  documentId: string,
  accessLevel: string,
) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/access`,
    {
      method: "PATCH",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ access_level: accessLevel }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cài đặt quyền cộng tác");
  return data;
}

export async function getSentPendingInvitesAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/loi-moi-da-gui`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách lời mời đã gửi");
  return data;
}

export async function revokeInviteAPI(inviteId: string) {
  const res = await fetch(`${API_URL}/collaboration/invite/${inviteId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Thu hồi lời mời cộng tác thất bại");
  return data;
}

export async function getContributionStatsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/thong-ke-dong-gop`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thống kê đóng góp");
  return data;
}

export async function createSnapshotAPI(
  documentId: string,
  versionName: string,
) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/version`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ version_name: versionName }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Tạo bản sao nháp cộng tác thất bại");
  return data;
}

export async function getSnapshotsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/version`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách bản sao nháp");
  return data;
}

export async function acquireLockAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/lock`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lấy khóa biên tập thất bại");
  return data;
}

export async function releaseLockAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/unlock`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Nhả khóa biên tập thất bại");
  return data;
}

export async function getLockStatusAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/trang-thai-khoa`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể lấy trạng thái khóa");
  return data;
}

export async function generateInviteCodeAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/invite-code`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tạo mã mời cộng tác");
  return data;
}

export async function joinViaInviteCodeAPI(inviteCode: string) {
  const res = await fetch(`${API_URL}/collaboration/join/${inviteCode}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Tham gia cộng tác biên tập thất bại");
  return data;
}

export async function createCollabTaskAPI(
  documentId: string,
  taskDesc: string,
  assignedTo: string,
) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/nhiem-vu`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ task_desc: taskDesc, assigned_to: assignedTo }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo nhiệm vụ cộng tác");
  return data;
}

export async function getCollabTasksAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/document/${documentId}/nhiem-vu`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách nhiệm vụ");
  return data;
}

export async function updateCollabTaskAPI(taskId: string, isDone: boolean) {
  const res = await fetch(`${API_URL}/collaboration/task/${taskId}`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ is_done: isDone }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật nhiệm vụ thất bại");
  return data;
}

export async function addTaskCommentAPI(taskId: string, commentText: string) {
  const res = await fetch(
    `${API_URL}/collaboration/task/${taskId}/comment`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ comment_text: commentText }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể thảo luận trong nhiệm vụ");
  return data;
}

export async function getTaskCommentsAPI(taskId: string) {
  const res = await fetch(
    `${API_URL}/collaboration/task/${taskId}/comment`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách bình luận nhiệm vụ",
    );
  return data;
}
