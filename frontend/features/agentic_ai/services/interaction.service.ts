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
  const res = await fetch(`${API_URL}/suy-luan/hanh-dong`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, action, context, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "MODULE AGENTIC_AI: Text processing failed");
  return data;
}

export async function smartSearchAIAPI(query: string) {
  const res = await fetch(
    `${API_URL}/kham-pha/tim-kiem-thong-minh?q=${encodeURIComponent(query)}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Semantic search failed");
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
    throw new Error(data.message || "MODULE AGENTIC_AI: Failed to retrieve conversation history");
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
    throw new Error(data.message || "MODULE AGENTIC_AI: Failed to initialize AI session");
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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Failed to update session title");
  return data;
}

export async function deleteAiSessionAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/lich-su/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Failed to delete session");
  return data;
}
export async function streamAiChatAPI(payload: any) {
  const token = getToken();
  return await fetch(`${API_URL}/tro-chuyen/phat-truc-tiep`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: RAG query inference failed");
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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Translation inference failed");
  return data;
}

export async function suggestCitationsAPI(text: string, style: string = "APA") {
  const res = await fetch(`${API_URL}/suy-luan/trich-dan-thong-minh`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, style }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Citation suggestion inference failed");
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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Text transformation inference failed");
  return data;
}

export async function peerReviewAPI(text: string, criteria: string[] = []) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-duyet-noi-dung`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, criteria }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Content review inference failed");
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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Multi-document synthesis inference failed");
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

