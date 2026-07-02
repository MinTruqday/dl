import {
  API_URL,
  getToken,
} from "@/features/auth/services/user_authentication.service";

export async function queryRagAPI(
  documentId: string,
  query: string,
  useSmart: boolean = false,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tro-chuyen/truy-van-rag`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId, query, useSmart }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail ||
        "Cố vấn AI đang bận xử lý dữ liệu khác, vui lòng thử lại sau",
    );
  return data;
}

export async function streamAiChatAPI(payload: {
  query: string;
  useSmart: boolean;
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
      useSmart: payload.useSmart,
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
  if (!res.ok) throw new Error(data.message || "Đồng bộ AI thất bại");
  return data;
}
