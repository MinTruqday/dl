import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

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

  const res = await fetch(`${API_URL}/to-dam/tai-lieu/${documentId}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(bodyData),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo nêu bật thất bại");
  return result;
}

export async function getHighlightsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/to-dam/tai-lieu/${documentId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách nêu bật");
  return data;
}

export async function updateHighlightNoteAPI(
  highlightId: string,
  note: string,
) {
  const res = await fetch(`${API_URL}/to-dam/${highlightId}/ghi-chu`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Cập nhật ghi chú nêu bật thất bại");
  return data;
}

export async function deleteHighlightAPI(highlightId: string) {
  const res = await fetch(`${API_URL}/to-dam/${highlightId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa nêu bật thất bại");
  return data;
}

export async function getAllNotesAPI(skip: number = 0, limit: number = 50) {
  const res = await fetch(
    `${API_URL}/to-dam/ghi-chu?skip=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách ghi chú");
  return data;
}

export async function getReadingPreferencesAPI() {
  const res = await fetch(`${API_URL}/setting`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cài đặt tùy chỉnh đọc");
  return data;
}

export async function updateReadingPreferencesAPI(data: {
  theme?: string;
  font_size?: number;
  line_height?: number;
  font_family?: string;
  is_dyslexic_mode?: boolean;
}) {
  const res = await fetch(`${API_URL}/setting`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Cập nhật cài đặt đọc thất bại");
  return result;
}

export async function exportHighlightsMarkdownAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/to-dam/tai-lieu/${documentId}/xuat`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xuất dữ liệu nêu bật thất bại");
  return data;
}
