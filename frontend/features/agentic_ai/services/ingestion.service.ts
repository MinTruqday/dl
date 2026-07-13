import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export async function queryRagAPI(
  documentId: string,
  query: string,
  thinking: boolean = false,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tro-chuyen/truy-van-rag`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId, query, thinking }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail ||
        "MODULE AGENTIC_AI: RAG backend busy or unavailable",
    );
  return data;
}

export async function streamAiChatAPI(payload: {
  query: string;
  thinking: boolean;
  session_id?: string | null;
  conversation_history?: any[];
  user_id?: string;
  image_data?: string | null;
  file_data?: string | null;
}) {
  const token = getToken();
  return fetch(`${API_URL}/tro-chuyen/truc-tuyen`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: payload.query,
      thinking: payload.thinking,
      session_id: payload.session_id,
      conversation_history: payload.conversation_history,
      user_id: payload.user_id,
      image_data: payload.image_data,
      file_data: payload.file_data,
    }),
  });
}

export async function ingestDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tiep-nap/dong-bo/${documentId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Vector ingestion pipeline failed");
  return data;
}
