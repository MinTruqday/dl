import {
  API_URL,
  getAuthHeaders,
  getToken,
} from "@/features/authentication/services/session.service";

export async function processTextAPI(
  text: string,
  action: string,
  context: string = "",
  targetLang: string = "Vietnamese",
) {
  const res = await fetch(`${API_URL}/suy-luan/tao-noi-dung`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, action, context, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Xử lý văn bản bằng AI thất bại");
  return data;
}

export async function smartSearchAIAPI(query: string) {
  const res = await fetch(
    `${API_URL}/suy-luan/tim-kiem-thong-minh?q=${encodeURIComponent(query)}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm kiếm thông minh thất bại");
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
    throw new Error(data.message || "Không thể tải lịch sử hội thoại");
  return data;
}

export async function createAiSessionAPI(
  documentId: string,
  firstQuery: string = "",
) {
  const res = await fetch(`${API_URL}/lich-su`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, first_query: firstQuery }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Khởi tạo hội thoại mới thất bại");
  return data;
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
  if (!res.ok) throw new Error(data.message || "Cập nhật tiêu đề thất bại");
  return data;
}

export async function deleteAiSessionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa hội thoại thất bại");
  return data;
}
export async function streamAiChatAPI(payload: any) {
  const token = getToken();
  return await fetch(`${API_URL}/tro-chuyen/tro-chuyen`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function queryRagAPI(
  documentId: string,
  query: string,
  useSmart: boolean = false,
  sessionId?: string,
) {
  const res = await fetch(`${API_URL}/tro-chuyen/tro-chuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      query,
      useSmart,
      session_id: sessionId,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Truy vấn AI thất bại");
  return data;
}

export async function translateTextAPI(
  text: string,
  targetLang: string = "vi",
) {
  return await processTextAPI(text, "translate", "", targetLang);
}

export async function suggestCitationsAPI(text: string, style: string = "APA") {
  const res = await fetch(`${API_URL}/suy-luan/trich-dan-thong-minh`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, style }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gợi ý trích dẫn thất bại");
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
  if (!res.ok) throw new Error(data.message || "Biến đổi văn bản thất bại");
  return data;
}

export async function peerReviewAPI(text: string, criteria: string[] = []) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-duyet-noi-dung`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, criteria }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thẩm định nội dung thất bại");
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
  if (!res.ok) throw new Error(data.message || "Tổng hợp đa tài liệu thất bại");
  return data;
}
