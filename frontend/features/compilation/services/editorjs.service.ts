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
    let errMsg = "Không thể thực hiện tiến trình kết xuất LaTeX";
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
    let errMsg = "Không thể tạo luồng kết xuất định dạng Word";
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
  if (!res.ok) throw new Error(data.message || "Không thể đồng bộ chuỗi sự kiện thao tác");
  return data;
}

export async function addInlineSuggestionAPI(documentId: string, payload: any) {
  const res = await fetch(`${API_URL}/soan-thao/${documentId}/goi-y`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tạo khối dữ liệu đề xuất nội tuyến");
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
  if (!res.ok) throw new Error(data.message || "Không thể thực hiện phản hồi quyết định khối đề xuất");
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
    throw new Error(data.message || "Không thể đồng bộ trạng thái phiên làm việc Pomodoro");
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
  if (!res.ok) throw new Error(data.message || "Không thể đồng bộ hóa dữ liệu bản nháp tự động");
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
  if (!res.ok) throw new Error(data.message || "Không thể tạo luồng yêu cầu xét duyệt tài liệu");
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
  if (!res.ok) throw new Error(data.message || "Không thể thực hiện biểu thức thay thế chuỗi toàn cục");
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
  if (!res.ok) throw new Error(data.message || "Không thể lưu dữ liệu phản hồi nội dung");
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
  if (!res.ok) throw new Error(data.message || "Không thể cập nhật trạng thái dữ liệu phản hồi");
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
    throw new Error(data.message || "Không thể tải dữ liệu đối chiếu phiên bản");
  return data.data;
}
