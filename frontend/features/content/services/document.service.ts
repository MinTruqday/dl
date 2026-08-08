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
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");

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
  if (!res.ok) throw new Error(data.detail || "Không thể lưu dữ liệu bản thảo");
  return data;
}

export async function getDocumentDraftAPI(documentId: string) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");

  const res = await fetch(`${API_URL}/tai-lieu/${documentId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Không thể tải dữ liệu bản thảo");
  return data;
}

export async function exportProtectedDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/thuy-an/${documentId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    let detail = "Không thể xuất tài liệu bảo vệ";
    try {
      const data = await res.json();
      detail = data.detail || data.message || detail;
    } catch {}
    throw new Error(detail);
  }
  return {
    blob: await res.blob(),
    contentDisposition: res.headers.get("content-disposition"),
  };
}

export async function getDocumentWithPasswordAPI(
  documentId: string,
  password?: string,
  shareToken?: string,
) {
  const token = getToken();
  const headers: Record<string, string> = token
    ? { Authorization: `Bearer ${token}` }
    : {};
  if (password) headers["x-document-password"] = password;
  const params = new URLSearchParams();
  if (shareToken) params.set("share_token", shareToken);
  const suffix = params.size ? `?${params.toString()}` : "";
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}${suffix}`, { headers });
  if (res.status === 401 || res.status === 403) {
    return { status: res.status, data: null };
  }
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tài liệu");
  return { status: res.status, data: data.data || data };
}

export async function getDocumentDecryptionKeyAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/khoa-giai-ma`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể xác thực tài liệu");
  return data.data?.key || data.key;
}

export async function getProtectedDocumentPageAPI(
  documentId: string,
  pageNumber: number,
  password?: string,
  shareToken?: string,
) {
  const headers = getAuthHeaders();
  if (password) headers["x-document-password"] = password;
  const params = new URLSearchParams();
  if (shareToken) params.set("share_token", shareToken);
  const suffix = params.size ? `?${params.toString()}` : "";
  const response = await fetch(
    `${API_URL}/tai-lieu/${documentId}/trang-bao-ve/${pageNumber}${suffix}`,
    { headers },
  );
  if (!response.ok) {
    let detail = "Không thể kết xuất trang tài liệu";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return {
    blob: await response.blob(),
    pageCount: Number(response.headers.get("x-page-count") || 1),
  };
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

  if (!res.ok) throw new Error("Lỗi kết nối cơ sở dữ liệu hệ thống");
  return await res.json();
}

export async function getDocumentBySlugAPI(slug: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/tai-lieu/${slug}`, {
    method: "GET",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  });

  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail || "Không thể tải thông tin siêu dữ liệu tài liệu",
    );
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
    throw new Error(json.message || "Không thể tải danh sách tài liệu cá nhân");
  return json.data || json;
}

export async function createDocumentAPI(data: any) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
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
    throw new Error(result.message || "Không thể tạo cấu trúc tài liệu mới");
  return result;
}

export async function importDocumentAPI(file: File) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_URL}/tai-lieu/import`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.message || "Không thể nhập tài liệu");
  return data;
}

export async function updateDocumentAPI(id: string, data: any) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(
      result.message || "Không thể cập nhật siêu dữ liệu tài liệu",
    );
  return result;
}

export async function deleteAuthorDocumentAPI(docId: string) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(result.message || "Không thể xóa bản ghi tài liệu");
  return result;
}

export async function deleteAdminDocumentAPI(docId: string) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/tai-lieu/${docId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const result = await res.json();
  if (!res.ok)
    throw new Error(
      result.message || "Không thể xóa bản ghi tài liệu cấp hệ thống",
    );
  return result;
}

export async function getTrashAPI() {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/thung-rac`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách thùng rác");
  return data;
}

export async function restoreDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể khôi phục bản ghi tài liệu");
  return data;
}

export async function softDeleteDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể lưu bản ghi tài liệu vào thùng rác",
    );
  return data;
}

export const getFoldersAPI = async (parent_id?: string) => {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const params = new URLSearchParams();
  if (parent_id) params.append("parent_id", parent_id);

  const res = await fetch(`${API_URL}/tai-lieu/thu-muc?${params.toString()}`, {
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cây cấu trúc thư mục");
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
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo cấu trúc thư mục mới");
  return data;
};

export const deleteFolderAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/thu-muc/${id}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể xóa cấu trúc thư mục");
  return data;
};

export const toggleStarDocumentAPI = async (id: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/danh-dau`, {
    method: "POST",
    headers: { Authorization: "Bearer " + token },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể cập nhật trạng thái lưu trữ");
  return data;
};

export const lockDocumentAPI = async (id: string, password: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/bao-ve`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể cấu hình mật mã bảo vệ");
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
  if (!res.ok) throw new Error(data.message || "Lỗi xác thực mật mã bảo vệ");
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
    throw new Error(data.detail || "Lỗi chuyển giao quyền sở hữu tài liệu");
  return data;
}

export async function getAuditLogsAPI(id: string) {
  if (!id || id === "undefined") return [];
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/nhat-ky-hoat-dong`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getDocumentAnalyticsAPI(id: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${id}/thong-ke`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.ok ? res.json() : null;
}

export async function getAcademicMetricsAPI(id: string) {
  const res = await fetch(`${API_URL}/tai-lieu/${id}/chi-so-hoc-thuat`);
  return res.ok ? res.json() : null;
}

export async function updateDRMSettingsAPI(
  documentId: string,
  settings: {
    disable_copy: boolean;
    disable_print: boolean;
    hide_from_search: boolean;
    watermark_enabled: boolean;
    allow_internal_ai: boolean;
    license_valid_days: number;
    max_open_count: number;
    ghost_font_enabled: boolean;
    ghost_font_exemption_scope:
      | "owner_only"
      | "private_link"
      | "selected_users"
      | "everyone";
    ghost_font_exempt_user_ids: string[];
  },
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/ban-quyen/${documentId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Không thể cấu hình cơ chế bảo mật DRM");
  return data;
}

export async function updateTagsAPI(documentId: string, tags: string[]) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/the`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tags }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail || "Không thể cập nhật danh sách thẻ phân loại",
    );
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
  if (!res.ok)
    throw new Error(data.detail || "Không thể cấu hình lịch trình xuất bản");
  return data;
}

export async function publishDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || "Lỗi khởi chạy tiến trình xuất bản");
  return data;
}
