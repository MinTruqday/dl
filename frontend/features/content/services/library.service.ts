import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function createReadingListAPI(data: {
  name: string;
  description?: string;
  is_public?: boolean;
}) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(
      result.message || "Không thể tạo cấu trúc danh sách lưu trữ",
    );
  return result;
}

export async function getMyReadingListsAPI() {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải bộ sưu tập danh sách lưu trữ",
    );
  return data;
}

export async function getReadingListByIdAPI(listId: string) {
  const res = await fetch(`${API_URL}/thu-vien/danh-sach/${listId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải cấu trúc chi tiết danh sách",
    );
  return data;
}

export async function addDocumentToListAPI(listId: string, documentId: string) {
  const res = await fetch(
    `${API_URL}/thu-vien/lists/${listId}/documents/${documentId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi liên kết tài liệu vào danh sách");
  return data;
}

export async function removeDocumentFromListAPI(
  listId: string,
  documentId: string,
) {
  const res = await fetch(
    `${API_URL}/thu-vien/lists/${listId}/documents/${documentId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi gỡ bỏ liên kết tài liệu khỏi danh sách",
    );
  return data;
}
