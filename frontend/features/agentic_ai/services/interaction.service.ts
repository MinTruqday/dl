import {
  API_URL,
  getAuthHeaders,
  getToken,
} from "@/shared/services/api-client";

export async function processTextAPI(
  text: string,
  action: string,
  context: string = "",
  targetLang: string = "Vietnamese",
) {
  const res = await fetch(`${API_URL}/suy-luan/hanh-dong`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, action, context, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xử lý văn bản",
    );
  return data;
}

export async function getAiSessionsAPI(documentId?: string, userId?: string) {
  const params = new URLSearchParams();
  if (documentId) params.set("document_id", documentId);
  if (userId) params.set("user_id", userId);
  const url = `${API_URL}/lich-su?${params.toString()}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Không thể tải lịch sử trò chuyện",
    );
  return data;
}

export async function createAiSessionAPI(
  documentId: string = "",
  firstQuery: string = "",
  mode: "chat" | "work" | "goal" | "learn" | "plan" = "chat",
) {
  const res = await fetch(`${API_URL}/lich-su`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId || null,
      first_query: firstQuery,
      mode,
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo phiên trò chuyện",
    );
  return data;
}

export async function getAiSessionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải cuộc trò chuyện");
  return data;
}

export async function getAiWorkspaceAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/tro-chuyen/khong-gian/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tiến trình");
  return data.data;
}

export async function updateAiSessionTitleAPI(
  sessionId: string,
  title: string,
) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}/tieu-de`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể đổi tên phiên trò chuyện",
    );
  return data;
}

export async function updateAiSessionStateAPI(
  sessionId: string,
  state: { is_pinned?: boolean; is_archived?: boolean },
) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}/trang-thai`, {
    method: "PATCH",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật cuộc trò chuyện");
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

export async function deleteAiSessionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xóa phiên trò chuyện",
    );
  return data;
}
export async function streamAiChatAPI(payload: any, signal?: AbortSignal) {
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

export async function cancelAiExecutionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/ngat-qua-trinh/${sessionId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể dừng tiến trình");
  return data;
}

export async function getPendingAiApprovalsAPI(sessionId: string) {
  const res = await fetch(
    `${API_URL}/ngat-qua-trinh/phe-duyet/${sessionId}`,
    { headers: getAuthHeaders() },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải yêu cầu xác nhận");
  return data.data ?? [];
}

export async function resolveAiApprovalAPI(
  approvalId: string,
  status: "APPROVED" | "REJECTED",
  scope: "once" | "session" | "safe_session" = "once",
) {
  const res = await fetch(
    `${API_URL}/ngat-qua-trinh/phe-duyet/phan-hoi/${approvalId}`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ status, scope }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể gửi lựa chọn xác nhận");
  return data.data;
}

export async function queryRagAPI(
  documentId: string,
  query: string,
  thinking: boolean = false,
  sessionId?: string,
) {
  const res = await fetch(`${API_URL}/tro-chuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      document_ids: [documentId],
      query,
      thinking,
      session_id: sessionId,
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể trả lời từ dữ liệu tài liệu",
    );
  return data;
}

export async function translateTextAPI(
  text: string,
  targetLang: string = "vi",
) {
  const res = await fetch(`${API_URL}/suy-luan/dich-thuat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể dịch nội dung",
    );
  return data;
}

export async function suggestCitationsAPI(text: string, style: string = "APA") {
  const res = await fetch(`${API_URL}/suy-luan/trich-dan-thong-minh`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, style }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể đề xuất trích dẫn",
    );
  return data;
}

export async function transformToneAPI(
  text: string,
  tone: string,
  expansion: boolean = false,
) {
  const res = await fetch(`${API_URL}/suy-luan/bien-doi-van-ban`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, tone, expansion }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể chuyển đổi văn bản",
    );
  return data;
}

export async function peerReviewAPI(text: string, criteria: string[] = []) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-duyet-noi-dung`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, criteria }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể kiểm tra nội dung",
    );
  return data;
}

export async function multiDocSynthesisAPI(
  documentIds: string[],
  query: string,
) {
  const res = await fetch(`${API_URL}/suy-luan/tong-hop-tai-lieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds, query }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Không thể tổng hợp tài liệu",
    );
  return data;
}

export async function getUserInstructionsAPI() {
  const res = await fetch(`${API_URL}/tro-chuyen/tuy-chon-ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải chỉ dẫn cá nhân");
  return data;
}

export async function saveUserInstructionsAPI(instructions: string) {
  const res = await fetch(`${API_URL}/tro-chuyen/tuy-chon-ca-nhan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
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
