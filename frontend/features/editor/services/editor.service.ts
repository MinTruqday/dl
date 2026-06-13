import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function compilePreviewAPI(
  content: string,
  isFragment: boolean = false,
) {
  const res = await fetch(`${API_URL}/latex/compile-preview`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, is_fragment: isFragment }),
  });
  if (!res.ok) {
    let errMsg = "Biên dịch LaTeX thất bại";
    try {
      const data = await res.json();
      errMsg = data.detail?.error || data.detail || errMsg;
    } catch (err: any) {
      console.warn("Could not parse error JSON:", err.message || err);
    }
    throw new Error(errMsg);
  }
  return await res.blob();
}

export async function exportToWordAPI(documentId: string) {
  const res = await fetch(`${API_URL}/export/${documentId}/docx`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    let errMsg = "Xuất file Word thất bại";
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || errMsg;
    } catch (err: any) {}
    throw new Error(errMsg);
  }
  return await res.blob();
}

export async function exportToEpubAPI(documentId: string) {
  const res = await fetch(`${API_URL}/export/${documentId}/epub`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    let errMsg = "Xuất file EPUB thất bại";
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || errMsg;
    } catch (err: any) {}
    throw new Error(errMsg);
  }
  return await res.blob();
}

export async function analyzeInternalPlagiarismAPI(
  documentId: string,
  content: any,
) {
  const res = await fetch(`${API_URL}/editor/${documentId}/check-plagiarism`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Phân tích đạo văn thất bại");
  return data;
}

export async function checkDeepPlagiarismAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/editor/${documentId}/check-plagiarism-chuyen-sau`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Kiểm tra đạo văn chuyên sâu thất bại");
  return data;
}

export async function syncKeystrokeBufferAPI(documentId: string, payload: any) {
  const res = await fetch(`${API_URL}/editor/${documentId}/sync-action`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đồng bộ thao tác thất bại");
  return data;
}

export async function addInlineSuggestionAPI(documentId: string, payload: any) {
  const res = await fetch(`${API_URL}/editor/document/${documentId}/goi-y`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thêm gợi ý nội dòng thất bại");
  return data;
}

export async function resolveSuggestionAPI(
  suggestionId: string,
  action: string,
) {
  const res = await fetch(
    `${API_URL}/editor/suggestion/${suggestionId}/resolve`,
    {
      method: "PUT",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý gợi ý thất bại");
  return data;
}

export async function syncPomodoroSessionAPI(payload: any) {
  const res = await fetch(`${API_URL}/editor/pomodoro`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Đồng bộ phiên Pomodoro thất bại");
  return data;
}

export async function autoSaveDraftAPI(documentId: string, content: any) {
  const res = await fetch(`${API_URL}/editor/${documentId}/auto-save`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tự động lưu bản nháp thất bại");
  return data;
}

export async function submitForReviewAPI(documentId: string) {
  const res = await fetch(`${API_URL}/editor/${documentId}/submit-review`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi duyệt tài liệu thất bại");
  return data;
}

export async function globalFindReplaceAPI(
  documentId: string,
  search: string,
  replace: string,
  matchCase: boolean = false,
) {
  const res = await fetch(`${API_URL}/editor/${documentId}/replace-all`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ search, replace, match_case: matchCase }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thay thế toàn cục thất bại");
  return data;
}

export async function addChapterAPI(
  documentId: string,
  data: {
    title: string;
    content: string;
    is_premium?: boolean;
    price_dl?: number;
  },
) {
  const res = await fetch(`${API_URL}/editor/${documentId}/chapter`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Thêm chương mới thất bại");
  return result;
}

export async function updateCoverAPI(documentId: string, coverUrl: string) {
  const res = await fetch(`${API_URL}/editor/${documentId}/cover-image`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ cover_url: coverUrl }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật ảnh bìa thất bại");
  return data;
}

export async function getAiSuggestionsAPI(documentId: string, context: string) {
  const res = await fetch(`${API_URL}/editor/${documentId}/ai-suggest`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lấy gợi ý AI thất bại");
  return data.data;
}

export async function summarizeDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/editor/${documentId}/summarize`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tóm tắt tài liệu thất bại");
  return data;
}

export async function extractSmartTagsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/editor/${documentId}/analyze-tags`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Tự động phân tích thẻ thất bại");
  return data;
}

export async function addInlineCommentAPI(
  documentId: string,
  payload: { block_id: string; text: string; selected_text?: string },
) {
  const res = await fetch(`${API_URL}/editor/${documentId}/comment`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thêm nhận xét thất bại");
  return data.data;
}

export async function resolveCommentAPI(commentId: string) {
  const res = await fetch(`${API_URL}/editor/comment/${commentId}/resolve`, {
    method: "PUT",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý nhận xét thất bại");
  return data.data;
}

export async function getVersionDiffAPI(
  documentId: string,
  versionIdA: string,
  versionIdB: string,
) {
  const res = await fetch(`${API_URL}/editor/${documentId}/compare-version`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      version_id_a: versionIdA,
      version_id_b: versionIdB,
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lấy so sánh phiên bản thất bại");
  return data.data;
}
