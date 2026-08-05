import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function inviteCollaboratorAPI(
  documentId: string,
  email: string,
  role: string = "editor",
) {
  const res = await fetch(`${API_URL}/cong-tac/loi-moi`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, email, role }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo yêu cầu cộng tác");
  return data;
}

export async function getCollaboratorsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/cong-tac/tai-lieu/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tài khoản cộng tác",
    );
  return data;
}

export async function removeCollaboratorAPI(collaborationId: string) {
  const res = await fetch(`${API_URL}/cong-tac/${collaborationId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi thu hồi quyền truy cập cộng tác");
  return data;
}

export async function getCollaborationInvitesAPI() {
  const res = await fetch(`${API_URL}/cong-tac/loi-moi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách yêu cầu chờ xử lý",
    );
  return data;
}

export async function respondToInviteAPI(inviteId: string, status: string) {
  const res = await fetch(`${API_URL}/cong-tac/loi-moi/${inviteId}`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi xử lý phản hồi yêu cầu cộng tác");
  return data;
}

export async function getCollaborationActivitiesAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/hoat-dong`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký hoạt động phiên");
  return data;
}

export async function transferOwnershipAPI(documentId: string, userId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/documents/${documentId}/transfer-ownership`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi chuyển giao quyền sở hữu tài liệu");
  return data;
}

export async function pingCollaborationStatusAPI(documentId: string) {
  const res = await fetch(`${API_URL}/cong-tac/tai-lieu/${documentId}/ping`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể đồng bộ tín hiệu nhịp tim kết nối",
    );
  return data;
}

export async function getOnlineCollaboratorsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/truc-tuyen`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải trạng thái hiện diện trực tuyến",
    );
  return data;
}

export async function updateCollaboratorRoleAPI(
  collaborationId: string,
  role: string,
) {
  const res = await fetch(`${API_URL}/cong-tac/${collaborationId}/vai-tro`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi phân quyền truy cập cho tài khoản");
  return data;
}

export async function sendMemoAPI(documentId: string, message: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/tin-nhan`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo bản tin giao tiếp");
  return data;
}

export async function getMemosAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/tin-nhan`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải luồng dữ liệu giao tiếp");
  return data;
}

export async function updateCollabAccessAPI(
  documentId: string,
  accessLevel: string,
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/quyen-truy-cap`,
    {
      method: "PATCH",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ access_level: accessLevel }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình tham số bảo mật luồng");
  return data;
}

export async function getSentPendingInvitesAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/documents/${documentId}/sent-invitations`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách yêu cầu chờ duyệt",
    );
  return data;
}

export async function revokeInviteAPI(inviteId: string) {
  const res = await fetch(`${API_URL}/cong-tac/loi-moi/${inviteId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi vô hiệu hóa yêu cầu kết nối");
  return data;
}

export async function getContributionStatsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/documents/${documentId}/contribution-stats`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải số liệu phân tích tần suất đóng góp",
    );
  return data;
}

export async function createSnapshotAPI(
  documentId: string,
  versionName: string,
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/phien-ban`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ version_name: versionName }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xuất bản sao phiên làm việc (Snapshot)",
    );
  return data;
}

export async function getSnapshotsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/phien-ban`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải bộ sưu tập lịch sử phiên bản",
    );
  return data;
}

export async function acquireLockAPI(documentId: string) {
  const res = await fetch(`${API_URL}/cong-tac/tai-lieu/${documentId}/khoa`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi cấp phát luồng điều khiển độc quyền (Mutex Lock)",
    );
  return data;
}

export async function releaseLockAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/mo-khoa`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Lỗi giải phóng luồng điều khiển độc quyền (Mutex Unlock)",
    );
  return data;
}

export async function getLockStatusAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/trang-thai-khoa`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cờ tín hiệu đồng bộ phiên");
  return data;
}

export async function generateInviteCodeAPI(documentId: string) {
  const res = await fetch(`${API_URL}/cong-tac/tai-lieu/${documentId}/ma-moi`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo token xác thực phiên kết nối",
    );
  return data;
}

export async function joinViaInviteCodeAPI(inviteCode: string) {
  const res = await fetch(`${API_URL}/cong-tac/tham-gia/${inviteCode}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi xác thực và cấp quyền truy cập phiên");
  return data;
}

export async function createCollabTaskAPI(
  documentId: string,
  taskDesc: string,
  assignedTo: string,
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/cong-viec`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ task_desc: taskDesc, assigned_to: assignedTo }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo cấu trúc công việc phân tán",
    );
  return data;
}

export async function getCollabTasksAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/cong-viec`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải ma trận công việc hiện hành",
    );
  return data;
}

export async function updateCollabTaskAPI(taskId: string, isDone: boolean) {
  const res = await fetch(`${API_URL}/cong-tac/nhiem-vu/${taskId}`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ is_done: isDone }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật cờ trạng thái xử lý tiến trình",
    );
  return data;
}

export async function addTaskCommentAPI(taskId: string, commentText: string) {
  const res = await fetch(`${API_URL}/cong-tac/nhiem-vu/${taskId}/binh-luan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ comment_text: commentText }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi đính kèm gói tin văn bản vào tiến trình",
    );
  return data;
}

export async function getTaskCommentsAPI(taskId: string) {
  const res = await fetch(`${API_URL}/cong-tac/nhiem-vu/${taskId}/binh-luan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải chuỗi phản hồi liên kết");
  return data;
}

export async function createCommentAPI(payload: {
  item_id: string;
  item_type: string;
  content: string;
  parent_id?: string | null;
}) {
  const res = await fetch(`${API_URL}/soan-thao/${payload.item_id}/binh-luan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      block_id: payload.parent_id || "document",
      text: payload.content,
      selected_text: "",
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể lưu nội dung phản hồi văn bản");
  return data;
}

export async function getCommentsByItemAPI(itemId: string) {
  const res = await fetch(`${API_URL}/soan-thao/${itemId}/binh-luan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu trúc cây phản hồi");
  const comments = Array.isArray(data.data) ? data.data : [];
  return {
    ...data,
    data: comments.map((comment: any) => ({
      ...comment,
      content: comment.content || comment.text,
      path: comment.path || "document",
      author: comment.author || {
        username: comment.user_name,
        full_name: comment.user_name,
      },
      user: comment.user || {
        id: comment.user_id,
        full_name: comment.user_name,
      },
    })),
  };
}

export async function deleteCommentAPI(commentId: string) {
  const res = await fetch(
    `${API_URL}/soan-thao/binh-luan/${commentId}/giai-quyet`,
    {
      method: "PUT",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi hủy bỏ node dữ liệu phản hồi");
  return data;
}

export async function configureShareLinkAPI(
  documentId: string,
  payload: {
    is_active: boolean;
    password?: string;
    default_role: string;
    expires_in_hours?: number;
  },
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/lien-ket-chia-se`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình liên kết chia sẻ");
  return data;
}

export async function getShareLinkConfigAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/lien-ket-chia-se`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu hình liên kết chia sẻ");
  return data;
}

export async function getPublicShareLinkInfoAPI(shareToken: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/thong-tin-lien-ket/${shareToken}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải thông tin liên kết phòng cộng tác",
    );
  return data;
}

export async function joinViaShareLinkAPI(
  shareToken: string,
  password?: string,
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tham-gia-lien-ket/${shareToken}`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ password: password || null }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tham gia không gian cộng tác qua liên kết",
    );
  return data;
}

export async function createAccessRequestAPI(
  documentId: string,
  payload: { requested_role: string; message?: string },
) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/xin-quyen`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể gửi yêu cầu xin quyền cộng tác");
  return data;
}

export async function getDocumentAccessRequestsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/tai-lieu/${documentId}/yeu-cau-xin-quyen`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách yêu cầu xin quyền");
  return data;
}

export async function getMyIncomingAccessRequestsAPI() {
  const res = await fetch(`${API_URL}/cong-tac/yeu-cau-xin-quyen-cua-toi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách yêu cầu xin quyền tới tài liệu",
    );
  return data;
}

export async function reviewAccessRequestAPI(
  requestId: string,
  payload: { status: "ACCEPTED" | "REJECTED"; role?: string },
) {
  const res = await fetch(
    `${API_URL}/cong-tac/yeu-cau-xin-quyen/${requestId}`,
    {
      method: "PATCH",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể phản hồi yêu cầu xin quyền");
  return data;
}

