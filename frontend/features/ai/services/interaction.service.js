import { API_URL, getAuthHeaders, getToken } from "@/shared/services/api-client";
export async function getAiSessionsAPI(documentId, userId) {
  const params = new URLSearchParams();
  if (documentId) params.set("document_id", documentId);
  if (userId) params.set("user_id", userId);
  const url = `${API_URL}/lich-su?${params.toString()}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử trò chuyện");
  return data;
}
export async function createAiSessionAPI(documentId = "", firstQuery = "", mode = "chat") {
  const res = await fetch(`${API_URL}/lich-su`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id: documentId || null,
      first_query: firstQuery,
      mode,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tạo phiên trò chuyện");
  return data;
}
export async function getAiSessionAPI(sessionId) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải cuộc trò chuyện");
  return data;
}
export async function getAiWorkspaceAPI(sessionId) {
  const res = await fetch(`${API_URL}/tro-chuyen/khong-gian/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tiến trình");
  return data.data;
}
export async function updateAiSessionTitleAPI(sessionId, title) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}/tieu-de`, {
    method: "PUT",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đổi tên phiên trò chuyện");
  return data;
}
export async function updateAiSessionStateAPI(sessionId, state) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}/trang-thai`, {
    method: "PATCH",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(state),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể cập nhật cuộc trò chuyện");
  return data;
}
export async function getAiCapabilitiesAPI() {
  const res = await fetch(`${API_URL}/tro-chuyen/kha-nang`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải khả năng AI");
  return data;
}
export async function deleteAiSessionAPI(sessionId) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể xóa phiên trò chuyện");
  return data;
}
export async function streamAiChatAPI(payload, signal) {
  const token = getToken();
  return await fetch(`${API_URL}/tro-chuyen/phat-truc-tiep`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    signal,
  });
}
export async function cancelAiExecutionAPI(sessionId) {
  const res = await fetch(`${API_URL}/ngat-qua-trinh/${sessionId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể dừng tiến trình");
  return data;
}
export async function getPendingAiApprovalsAPI(sessionId) {
  const res = await fetch(`${API_URL}/ngat-qua-trinh/phe-duyet/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải yêu cầu xác nhận");
  return data.data ?? [];
}
export async function resolveAiApprovalAPI(approvalId, status, scope = "once") {
  const res = await fetch(`${API_URL}/ngat-qua-trinh/phe-duyet/phan-hoi/${approvalId}`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status, scope }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể gửi lựa chọn xác nhận");
  return data.data;
}
export async function getUserInstructionsAPI() {
  const res = await fetch(`${API_URL}/tro-chuyen/tuy-chon-ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải chỉ dẫn cá nhân");
  return data;
}
export async function saveUserInstructionsAPI(instructions) {
  const res = await fetch(`${API_URL}/tro-chuyen/tuy-chon-ca-nhan`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ instructions }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể lưu chỉ dẫn cá nhân");
  return data;
}
export async function clearUserInstructionsAPI() {
  const res = await fetch(`${API_URL}/tro-chuyen/tuy-chon-ca-nhan`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể xóa chỉ dẫn cá nhân");
  return data;
}
