import { API_URL, getToken, getAuthHeaders } from "./auth.service";

export async function saveDocumentDraftAPI(
  documentId: string,
  content: string,
  format: string,
) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(`${API_URL}/documents/${documentId}/content`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      content: content,
      content_format: format,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Lưu bản nháp thất bại.");
  return data;
}

export async function publishDocumentAPI(documentId: string) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(`${API_URL}/documents/${documentId}/publish`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Xuất bản thất bại.");
  return data;
}

export async function getDocumentDraftAPI(documentId: string) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(`${API_URL}/documents/${documentId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Tải bản nháp thất bại.");
  return data;
}

export async function compileDocumentAPI(documentId: string) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(`${API_URL}/documents/${documentId}/compile`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Biên dịch tài liệu thất bại.");
  return data;
}

export async function getDocumentsAPI(
  search?: string,
  sortBy?: string,
  category?: string,
  tag?: string,
  folder_id?: string,
  is_starred?: boolean,
  fmt?: string,
  author_slug?: string,
) {
  const token = getToken();
  let url = `${API_URL}/documents/`;
  const params = new URLSearchParams();
  if (search) params.append("q", search);
  if (sortBy) params.append("sort_by", sortBy);
  if (category) params.append("category", category);
  if (tag) params.append("tag", tag);
  if (folder_id) params.append("folder_id", folder_id);
  if (is_starred) params.append("is_starred", "true");
  if (fmt && fmt !== "all") params.append("fmt", fmt);
  if (author_slug) params.append("author_slug", author_slug);

  if (params.toString()) url += `?${params.toString()}`;

  const res = await fetch(url, {
    method: "GET",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  });

  if (!res.ok)
    throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
  return await res.json();
}

export async function getDocumentBySlugAPI(slug: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/s/${slug}`, {
    method: "GET",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  });

  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể truy xuất dữ liệu tài liệu.");
  return data;
}

export async function getMyDocumentsAPI(skip: number = 0, limit: number = 50) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/documents/me?skip=${skip}&limit=${limit}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  const json = await res.json();
  if (!res.ok)
    throw new Error(
      json.message || "Không thể lấy danh sách tài liệu của bạn.",
    );
  return json.data || json;
}

export const getTrendingDocumentsAPI = async (limit: number = 3) => {
  const res = await fetch(`${API_URL}/discovery/trending?limit=${limit}`);
  if (!res.ok) throw new Error("Không thể tải xu hướng.");
  return await res.json();
};

export const getTagsCategoriesAPI = async () => {
  const res = await fetch(`${API_URL}/discovery/tags-and-categories`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh mục.");
  return await res.json();
};

export async function createDocumentAPI(data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/documents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Không thể khởi tạo tài liệu mới.");
  return await res.json();
}

export async function updateDocumentAPI(id: string, data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/documents/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Không thể cập nhật tài liệu.");
  return await res.json();
}

export async function deleteAuthorDocumentAPI(docId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/documents/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể xóa tài liệu.");
  return await res.json();
}

export async function deleteAdminDocumentAPI(docId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/documents/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể xóa tài liệu hệ thống.");
  return await res.json();
}

export const getAIRecommendationsAPI = async (limit: number = 4) => {
  const res = await fetch(
    `${API_URL}/discovery/recommendations/ai?limit=${limit}`,
    { headers: getAuthHeaders() },
  );
  if (!res.ok) throw new Error("Không thể tải gợi ý từ AI.");
  return await res.json();
};

export async function getDocumentVersionsAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${documentId}/versions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể tải danh sách phiên bản.");
  return await res.json();
}

export async function restoreVersionAPI(versionId: string) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/documents/versions/${versionId}/restore`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) throw new Error("Khôi phục phiên bản thất bại.");
  return await res.json();
}

export async function getTrashAPI() {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/trash`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể tải thùng rác.");
  return await res.json();
}

export async function restoreDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${documentId}/restoration`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Khôi phục tài liệu thất bại.");
  return await res.json();
}

export async function softDeleteDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${documentId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Xóa tài liệu thất bại.");
  return await res.json();
}

export const getFoldersAPI = async (parent_id?: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const params = new URLSearchParams();
  if (parent_id) params.append("parent_id", parent_id);

  const res = await fetch(`${API_URL}/documents/folders?${params.toString()}`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể tải danh sách thư mục.");
  return res.json();
};

export const createFolderAPI = async (
  name: string,
  parent_id: string | null = null,
) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/folders`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, parent_id }),
  });
  if (!res.ok) throw new Error("Không thể tạo thư mục mới.");
  return res.json();
};

export const deleteFolderAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/folders/${id}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể xóa thư mục.");
  return res.json();
};

export const toggleStarDocumentAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/toggle-star`, {
    method: "PUT",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thao tác thất bại.");
  return data;
};

export const lockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/protection`, {
    method: "POST",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thiết lập mật khẩu thất bại.");
  return data;
};

export const unlockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/unlock`, {
    method: "POST",
    body: password,
    headers: { Authorization: "Bearer " + token, "Content-Type": "text/plain" },
  });
  if (!res.ok) throw new Error("Mật mã không chính xác.");
  return res.json();
};

export async function monetizeDocumentAPI(id: string, price: number) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/documents/${id}/monetize?price=${price}`,
    {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Thiết lập giá trị giao dịch thất bại.");
  return data;
}

export async function transferDocumentAPI(id: string, newOwnerId: string) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/documents/${id}/transfer?new_owner_id=${newOwnerId}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Chuyển nhượng quyền sở hữu thất bại.");
  return data;
}

export async function getAuditLogsAPI(id: string) {
  if (!id || id === "undefined") return [];
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/audit-logs`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function shareToFeedAPI(id: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/share-feed`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

export async function getDocumentAnalyticsAPI(id: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/${id}/analytics`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.ok ? res.json() : null;
}

export async function getAcademicMetricsAPI(id: string) {
  const res = await fetch(`${API_URL}/documents/${id}/metrics`);
  return res.ok ? res.json() : null;
}

export async function purchaseDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/wallet/purchases/documents/${documentId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(
      err.message || "Không thể thực hiện giao dịch mua tài liệu.",
    );
  }
  return await res.json();
}

export async function uploadDocumentAPI(file: File) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/upload/document`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tải tài liệu.");
  return data;
}
