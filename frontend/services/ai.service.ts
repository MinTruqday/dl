import { API_URL, getAuthHeaders } from './auth.service';

export async function translateTextAPI(text: string, target_lang: string = "vi") {
    const res = await fetch(`${API_URL}/inference/translate`, {
        method: "POST",
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, target_lang })
    });
    if (!res.ok) throw new Error("Dịch thuật thất bại.");
    return await res.json();
}

export async function getAIFeedSummaryAPI() {
    const res = await fetch(`${API_URL}/social/ai/feed-summary`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Không thể tóm tắt bảng tin.");
    return await res.json();
}

export async function ingestDocumentAPI(documentId: string) {
    const res = await fetch(`${API_URL}/ai/ingest/${documentId}`, {
        method: "POST",
        headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Đồng bộ AI thất bại.");
    return await res.json();
}

export async function generateAICoverAPI(documentId: string) {
    const res = await fetch(`${API_URL}/ai/generate-cover/${documentId}`, {
        method: "POST",
        headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Tạo ảnh bìa AI thất bại.");
    return await res.json();
}

export async function getDocumentSentimentAPI(documentId: string) {
    const res = await fetch(`${API_URL}/documents/${documentId}/analytics/sentiment`, {
        headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Không thể phân tích cảm quan tài liệu.");
    return await res.json();
}

export async function queryRagAPI(documentId: string, query: string, usePro: boolean = false) {
    const res = await fetch(`${API_URL}/ai/query`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId, query, use_pro: usePro })
    });
    if (!res.ok) throw new Error("Cố vấn AI đang bận xử lý dữ liệu khác, vui lòng thử lại sau.");
    return await res.json();
}

export async function streamAiChatAPI(payload: {
    query: string;
    usePro: boolean;
    session_id?: string | null;
    conversation_history?: any[];
    user_id?: string;
    image_data?: string | null;
    file_data?: string | null;
}) {
    return fetch(`${API_URL}/ai/stream`, {
        method: "POST",
        headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({
            query: payload.query,
            use_pro: payload.usePro,
            session_id: payload.session_id,
            conversation_history: payload.conversation_history,
            user_id: payload.user_id,
            image_data: payload.image_data,
            file_data: payload.file_data
        })
    });
}
