import {
  API_URL,
  getToken,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function saveDocumentDraftAPI(
  documentId: string,
  content: string,
  format: string,
) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập");

  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/noi-dung`, {
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
  if (!res.ok) throw new Error(data.detail || "Lưu bản nháp thất bại");
  return data;
}

export async function getDocumentDraftAPI(documentId: string) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập");

  const res = await fetch(`${API_URL}/tai-lieu/${documentId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Tải bản nháp thất bại");
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
  cursor?: string,
  limit: number = 50,
) {
  const token = getToken();
  let url = `${API_URL}/tai-lieu`;
  const params = new URLSearchParams();
  if (search) params.append("q", search);
  if (sortBy) params.append("sort_by", sortBy);
  if (category) params.append("category", category);
  if (tag) params.append("tag", tag);
  if (folder_id) params.append("folder_id", folder_id);
  if (is_starred) params.append("is_starred", "true");
  if (fmt && fmt !== "all") params.append("fmt", fmt);
  if (author_slug) params.append("author_slug", author_slug);
  if (cursor) params.append("cursor", cursor);
  params.append("limit", limit.toString());

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
    throw new Error("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau");
  return await res.json();
}

export async function getDocumentBySlugAPI(slug: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/d/${slug}`, {
    method: "GET",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  });

  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể truy xuất dữ liệu tài liệu");
  return data;
}

export async function getMyDocumentsAPI(
  search: string = "",
  cursor: string = "",
  limit: number = 50,
) {
  const token = getToken();
  const params = new URLSearchParams({ limit: limit.toString() });
  if (search) params.append("q", search);
  if (cursor) params.append("cursor", cursor);

  const res = await fetch(`${API_URL}/tai-lieu/ca-nhan?${params.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const json = await res.json();
  if (!res.ok)
    throw new Error(json.message || "Không thể lấy danh sách tài liệu của bạn");
  return json.data || json;
}

export async function createDocumentAPI(data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tai-lieu`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Không thể khởi tạo tài liệu mới");
  return result;
}

export async function updateDocumentAPI(id: string, data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể cập nhật tài liệu");
  return result;
}

export async function deleteAuthorDocumentAPI(docId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Không thể xóa tài liệu");
  return result;
}

export async function deleteAdminDocumentAPI(docId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Không thể xóa tài liệu hệ thống");
  return result;
}

export async function getTrashAPI() {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/thung-rac`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thùng rác");
  return data;
}

export async function restoreDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Khôi phục tài liệu thất bại");
  return data;
}

export async function softDeleteDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa tài liệu thất bại");
  return data;
}

export const getFoldersAPI = async (parent_id?: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const params = new URLSearchParams();
  if (parent_id) params.append("parent_id", parent_id);

  const res = await fetch(`${API_URL}/tai-lieu/thu-muc?${params.toString()}`, {
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách thư mục");
  return data;
};

export const createFolderAPI = async (
  name: string,
  parent_id: string | null = null,
) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/thu-muc`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, parent_id }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tạo thư mục mới");
  return data;
};

export const deleteFolderAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/thu-muc/${id}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể xóa thư mục");
  return data;
};

export const toggleStarDocumentAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/star`, {
    method: "PUT",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thao tác thất bại");
  return data;
};

export const lockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/protect`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Thiết lập mật khẩu thất bại");
  return data;
};

export const unlockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/mo-khoa`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mật mã không chính xác");
  return data;
};

export async function transferDocumentAPI(id: string, newOwnerId: string) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/tai-lieu/${id}/chuyen-nhuong?new_owner_id=${newOwnerId}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Chuyển nhượng quyền sở hữu thất bại");
  return data;
}

export async function getAuditLogsAPI(id: string) {
  if (!id || id === "undefined") return [];
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/activity-log`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getDocumentAnalyticsAPI(id: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/phan-tich`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.ok ? res.json() : null;
}

export async function getAcademicMetricsAPI(id: string) {
  const res = await fetch(`${API_URL}/tai-lieu/${id}/chi-so-hoc-thuat`);
  return res.ok ? res.json() : null;
}

export async function updateAuthorNoteAPI(
  documentId: string,
  chapterIndex: number,
  note: string,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/ghi-chu-tac-gia`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ chapter_index: chapterIndex, note }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Cập nhật ghi chú thất bại");
  return data;
}

export async function updateDRMSettingsAPI(
  documentId: string,
  settings: { disable_copy: boolean; hide_from_search: boolean },
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/drm`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Cập nhật DRM thất bại");
  return data;
}

export async function updateTagsAPI(documentId: string, tags: string[]) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/tags`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tags }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Cập nhật thẻ thất bại");
  return data;
}

export async function schedulePublishAPI(
  documentId: string,
  publishAt: string,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/len-lich`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ publish_at: publishAt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Lên lịch xuất bản thất bại");
  return data;
}

export async function updateChapterPaywallAPI(
  documentId: string,
  chapterIndex: number,
  isPremium: boolean,
) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/tai-lieu/${documentId}/chuong/${chapterIndex}/tra-phi`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ is_premium: isPremium }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Cập nhật trả phí thất bại");
  return data;
}

export async function compileDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/bien-dich`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Biên dịch tài liệu thất bại");
  return data;
}

export async function publishDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/xuat-ban`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Xuất bản tài liệu thất bại");
  return data;
}
