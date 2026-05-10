import { API_URL, getAuthHeaders, getToken } from "./authentication.service";

export async function processTextAPI(text: string, action: string, context: string = "", targetLang: string = "Vietnamese") {
  const res = await fetch(`${API_URL}/ai/van-ban`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, action, context, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý văn bản bằng AI thất bại");
  return data;
}

export async function smartSearchAIAPI(query: string) {
  const res = await fetch(`${API_URL}/ai/tim-kiem-thong-minh?q=${encodeURIComponent(query)}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm kiếm thông minh thất bại");
  return data;
}

export async function generateFlashcardAPI(documentId: string, text: string, context: string = "") {
  const res = await fetch(`${API_URL}/ai/tai-lieu/${documentId}/the-ghi-nho`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, context }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo flashcard thất bại");
  return data;
}

export async function reviewFlashcardAPI(cardId: string, quality: number) {
  const res = await fetch(`${API_URL}/ai/the-ghi-nho/on-tap`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ card_id: cardId, quality }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghi nhận ôn tập thất bại");
  return data;
}

export async function getAiSessionsAPI(documentId?: string) {
  const url = documentId 
    ? `${API_URL}/ai/lich-su?document_id=${documentId}`
    : `${API_URL}/ai/lich-su`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử hội thoại");
  return data;
}

export async function createAiSessionAPI(documentId: string, firstQuery: string = "") {
  const res = await fetch(`${API_URL}/ai/lich-su`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, first_query: firstQuery }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Khởi tạo hội thoại mới thất bại");
  return data;
}

export async function updateAiSessionTitleAPI(sessionId: string, title: string) {
  const res = await fetch(`${API_URL}/ai/lich-su/${sessionId}/tieu-de`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật tiêu đề thất bại");
  return data;
}

export async function deleteAiSessionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/ai/lich-su/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa hội thoại thất bại");
  return data;
}
export async function streamAiChatAPI(payload: any) {
  const token = getToken();
  return await fetch(`${API_URL}/ai/tro-chuyen`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
}

export async function queryRagAPI(documentId: string, query: string, useSmart: boolean = false, sessionId?: string) {
  const res = await fetch(`${API_URL}/ai/tro-chuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, query, useSmart, session_id: sessionId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Truy vấn AI thất bại");
  return data;
}

export async function translateTextAPI(text: string, targetLang: string = "vi") {
  return await processTextAPI(text, "translate", "", targetLang);
}
