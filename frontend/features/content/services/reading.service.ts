import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getReadingHistoryAPI(
  skip: number = 0,
  limit: number = 20,
) {
  const res = await fetch(
    `${API_URL}/doc-hieu/lich-su?skip=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải bộ nhớ tạm lịch sử truy cập",
    );
  return data;
}

export async function updateReadingProgressAPI(data: {
  document_id: string;
  progress_percentage: number;
  current_chapter_slug?: string;
}) {
  const res = await fetch(`${API_URL}/doc-hieu/tien-do`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(
      result.message || "Không thể đồng bộ tham số trạng thái tiến trình",
    );
  return result;
}

export async function getPinnedDocumentsAPI() {
  const res = await fetch(`${API_URL}/ghim`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách đánh dấu ưu tiên");
  return data;
}

export async function pinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ghim/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể ghim tài liệu");
  return data;
}

export async function unpinDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/ghim/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể bỏ ghim tài liệu");
  return data;
}

export async function setPinnedDocumentsAPI(documentIds: string[]) {
  const res = await fetch(`${API_URL}/ghim`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể sắp xếp tài liệu ghim");
  return data;
}

export async function searchInDocumentAPI(documentId: string, query: string) {
  const res = await fetch(
    `${API_URL}/doc-hieu/tai-lieu/${documentId}/tim-kiem?q=${encodeURIComponent(query)}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thực hiện truy vấn tìm kiếm toàn văn bản",
    );
  return data;
}

export async function clearReadingHistoryAPI() {
  const res = await fetch(`${API_URL}/doc-hieu/lich-su`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xóa bộ nhớ tạm lịch sử truy cập",
    );
  return data;
}

export async function deleteReadingHistoryItemAPI(documentId: string) {
  const res = await fetch(`${API_URL}/doc-hieu/lich-su/${documentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể xóa bản ghi lịch sử truy cập");
  return data;
}
