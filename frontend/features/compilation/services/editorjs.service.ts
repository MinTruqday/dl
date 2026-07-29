import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function compilePreviewAPI(
  content: string,
  isFragment: boolean = false,
) {
  const res = await fetch(`${API_URL}/soan-thao/editorjs/bien-dich`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content, is_fragment: isFragment }),
  });
  if (!res.ok) {
    let errMsg = "Lỗi thực thi tiến trình kết xuất LaTeX";
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

export async function exportToWordAPI(content: string) {
  const res = await fetch(`${API_URL}/soan-thao/editorjs/ket-xuat/docx`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    let errMsg = "Lỗi khởi tạo luồng kết xuất định dạng Word";
    try {
      const data = await res.json();
      errMsg = data.detail || data.message || errMsg;
    } catch (err: any) {}
    throw new Error(errMsg);
  }
  return await res.blob();
}

export async function syncKeystrokeBufferAPI(documentId: string, payload: any) {
  const res = await fetch(`${API_URL}/soan-thao/${documentId}/dong-bo`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi đồng bộ chuỗi sự kiện thao tác");
  return data;
}

export async function addInlineSuggestionAPI(documentId: string, payload: any) {
  const res = await fetch(`${API_URL}/soan-thao/${documentId}/goi-y`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo khối dữ liệu đề xuất nội tuyến");
  return data;
}

export async function resolveSuggestionAPI(
  suggestionId: string,
  action: string,
) {
  const res = await fetch(
    `${API_URL}/soan-thao/goi-y/${suggestionId}/giai-quyet`,
    {
      method: "PUT",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi phản hồi quyết định khối đề xuất");
  return data;
}

export async function syncPomodoroSessionAPI(payload: any) {
  const res = await fetch(`${API_URL}/soan-thao/dong-ho-pomodoro`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi đồng bộ trạng thái phiên làm việc Pomodoro");
  return data;
}

export async function autoSaveDraftAPI(documentId: string, content: any) {
  const res = await fetch(
    `${API_URL}/soan-thao/${documentId}/tu-dong-luu`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi đồng bộ hóa dữ liệu bản nháp tự động");
  return data;
}

export async function submitForReviewAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/soan-thao/${documentId}/gui-danh-gia`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo luồng yêu cầu xét duyệt tài liệu");
  return data;
}

export async function globalFindReplaceAPI(
  documentId: string,
  search: string,
  replace: string,
  matchCase: boolean = false,
) {
  const res = await fetch(
    `${API_URL}/soan-thao/${documentId}/tim-va-thay-the`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ search, replace, match_case: matchCase }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi biểu thức thay thế chuỗi toàn cục");
  return data;
}

export async function addInlineCommentAPI(
  documentId: string,
  payload: { block_id: string; text: string; selected_text?: string },
) {
  const res = await fetch(
    `${API_URL}/soan-thao/${documentId}/binh-luan`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi lưu trữ dữ liệu phản hồi nội dung");
  return data.data;
}

export async function resolveCommentAPI(commentId: string) {
  const res = await fetch(
    `${API_URL}/soan-thao/binh-luan/${commentId}/giai-quyet`,
    {
      method: "PUT",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật trạng thái dữ liệu phản hồi");
  return data.data;
}

export async function getVersionDiffAPI(
  documentId: string,
  versionIdA: string,
  versionIdB: string,
) {
  const res = await fetch(
    `${API_URL}/soan-thao/${documentId}/so-sanh-phien-ban`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        version_id_a: versionIdA,
        version_id_b: versionIdB,
      }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy xuất dữ liệu đối chiếu phiên bản");
  return data.data;
}

export async function getAiSuggestionsAPI(documentId: string, context: string) {
  const res = await fetch(`${API_URL}/goi-y-ai`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy xuất bộ dữ liệu mạng mô hình ngôn ngữ");
  return data.data;
}

export async function summarizeDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/tom-tat`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi chạy tiến trình cô đọng nội dung tài liệu");
  return data;
}
