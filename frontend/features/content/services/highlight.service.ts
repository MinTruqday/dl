import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function createHighlightAPI(
  documentId: string,
  textOrData: string | { text: string; color?: string; note?: string },
  color?: string,
  note?: string,
) {
  let bodyData: any = {};
  if (typeof textOrData === "object" && textOrData !== null) {
    bodyData = {
      text: textOrData.text,
      color: textOrData.color || color || "#e4e4e7",
      note: textOrData.note || note || "",
    };
  } else {
    bodyData = {
      text: textOrData,
      color: color || "#e4e4e7",
      note: note || "",
    };
  }

  const res = await fetch(`${API_URL}/danh-dau/tai-lieu/${documentId}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Lỗi khởi tạo siêu dữ liệu đánh dấu");
  return result;
}

export async function getHighlightsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/danh-dau/tai-lieu/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất bộ sưu tập đánh dấu");
  return data;
}

export async function updateHighlightNoteAPI(
  highlightId: string,
  note: string,
) {
  const res = await fetch(`${API_URL}/danh-dau/${highlightId}/ghi-chu`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi lưu trữ dữ liệu chú thích");
  return data;
}

export async function deleteHighlightAPI(highlightId: string) {
  const res = await fetch(`${API_URL}/danh-dau/${highlightId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa bỏ bản ghi đánh dấu");
  return data;
}

export async function getAllNotesAPI(skip: number = 0, limit: number = 50) {
  const res = await fetch(
    `${API_URL}/danh-dau/ghi-chu?skip=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất tập hợp chú thích");
  return data;
}

export async function getReadingPreferencesAPI() {
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất tham số cấu hình hiển thị");
  return data;
}

export async function updateReadingPreferencesAPI(data: {
  theme?: string;
  font_size?: number;
  line_height?: number;
  font_family?: string;
  is_dyslexic_mode?: boolean;
}) {
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Lỗi lưu trữ tham số cấu hình hiển thị");
  return result;
}

export async function exportHighlightsMarkdownAPI(documentId: string) {
  const res = await fetch(`${API_URL}/danh-dau/tai-lieu/${documentId}/xuat`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi kết xuất siêu dữ liệu đánh dấu");
  return data;
}
