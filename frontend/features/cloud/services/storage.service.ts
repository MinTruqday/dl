import { getToken as getAuthToken } from "@/shared/services/api-client";
import { API_URL } from "@/shared/services/api-client";

export interface StorageItem {
  _id: string;
  name: string;
  is_folder: boolean;
  size: number;
  mime_type?: string;
  url?: string;
  is_trashed: boolean;
  is_starred: boolean;
  is_public: boolean;
  share_token?: string;
  versions?: any[];
  parent_id?: string;
  description?: string;
  tags?: string[];
  shared_with?: Array<{ user_id: string; role: string }>;
  is_shortcut?: boolean;
  target_id?: string;
  color?: string;
  is_duplicate?: boolean;
  duplicate_of?: string;
  environment_ready?: boolean;
  ai_processed?: boolean;
  entities?: {
    people?: string[];
    organizations?: string[];
    dates?: string[];
    amounts?: string[];
  };
  broken_links?: string[];
  is_locked?: boolean;
  locked_by?: string;
  locked_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ProtectedShareResult {
  share_token: string;
  has_password: boolean;
  expires_at: string;
}

export interface SharedStorageItem extends StorageItem {
  download_url?: string;
}

const mapItem = (item: any) => {
  if (!item) return item;
  return { ...item, _id: item._id || item.id };
};

export const createFolderAPI = async (name: string, parent_id?: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/thu-muc`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name, parent_id }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo cấu trúc thư mục lưu trữ");
  return mapItem(data.data);
};

export const listStorageItemsAPI = async (
  parent_id?: string,
  is_trashed: boolean = false,
) => {
  const token = getAuthToken();
  const query = new URLSearchParams();
  if (parent_id) query.append("parent_id", parent_id);
  if (is_trashed) query.append("is_trashed", "true");

  const res = await fetch(`${API_URL}/luu-tru/danh-sach?${query.toString()}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách thực thể lưu trữ");
  return data.data.map(mapItem) as StorageItem[];
};

export const updateStorageItemAPI = async (
  id: string,
  updates: Partial<StorageItem>,
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật siêu dữ liệu thực thể lưu trữ",
    );
  return mapItem(data.data);
};

export const deleteStorageItemAPI = async (
  id: string,
  hard_delete: boolean = false,
) => {
  const token = getAuthToken();
  const res = await fetch(
    `${API_URL}/luu-tru/tap-tin/${id}?hard_delete=${hard_delete}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể xóa thực thể lưu trữ");
  return data.data;
};

export const moveToTrashAPI = async (id: string) => deleteStorageItemAPI(id, false);


export const uploadStorageFileAPI = async (file: File, parent_id?: string) => {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/tai-len/tap-tin`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
  const uploadData = await res.json();
  if (!res.ok)
    throw new Error(
      uploadData.message || "Lỗi đẩy dữ liệu lên máy chủ lưu trữ phân tán",
    );

  const fileUrl = uploadData.data?.url || uploadData.data?.filename;

  const registerRes = await fetch(`${API_URL}/luu-tru/tap-tin`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      name: file.name,
      parent_id: parent_id,
      size: file.size,
      mime_type: file.type,
      url: fileUrl,
    }),
  });

  const fileData = await registerRes.json();
  if (!registerRes.ok)
    throw new Error(
      fileData.message || "Lỗi đăng ký bản ghi dữ liệu vào hệ thống",
    );

  return fileData.data;
};

export const searchStorageItemsAPI = async (q: string, type?: string) => {
  const token = getAuthToken();
  const query = new URLSearchParams();
  query.append("q", q);
  if (type) query.append("type", type);

  const res = await fetch(`${API_URL}/luu-tru/tim-kiem?${query.toString()}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thực hiện truy vấn tìm kiếm thực thể",
    );
  return data.data.map(mapItem) as StorageItem[];
};

export type StorageSearchFilters = {
  q?: string;
  mime_type?: string;
  extension?: string;
  min_size_mb?: number;
  max_size_mb?: number;
};

export const advancedSearchStorageItemsAPI = async (
  filters: StorageSearchFilters,
) => {
  const token = getAuthToken();
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  const res = await fetch(
    `${API_URL}/tim-kiem/luu-tru?${query.toString()}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tìm kiếm tệp nâng cao");
  return data.data.map(mapItem) as StorageItem[];
};

export const getRecentStorageItemsAPI = async (limit: number = 20) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/gan-day?limit=${limit}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách truy cập gần đây");
  return data.data.map(mapItem) as StorageItem[];
};

export const getArchiveTreeAPI = async (fileUrl: string) => {
  const res = await fetch(
    `${API_URL}/doc-hieu/luu-tru/cay-thu-muc?file_url=${encodeURIComponent(fileUrl)}`,
    { headers: { Authorization: `Bearer ${getAuthToken()}` } },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể đọc cấu trúc tệp nén");
  return data.data || [];
};

export const getArchiveContentAPI = async (fileUrl: string, path: string) => {
  const res = await fetch(
    `${API_URL}/doc-hieu/luu-tru/noi-dung?file_url=${encodeURIComponent(fileUrl)}&path=${encodeURIComponent(path)}`,
    { headers: { Authorization: `Bearer ${getAuthToken()}` } },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể đọc tệp trong kho lưu trữ");
  return data.data || data;
};

export const copyStorageItemAPI = async (
  id: string,
  target_parent_id?: string,
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/sao-chep`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_parent_id }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi nhân bản thực thể lưu trữ");
  return mapItem(data.data);
};

export const uploadFileVersionAPI = async (id: string, file: File) => {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/tai-len/tap-tin`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const uploadData = await res.json();
  if (!res.ok)
    throw new Error(
      uploadData.message || "Lỗi đẩy dữ liệu lên máy chủ lưu trữ phân tán",
    );

  const fileUrl = uploadData.data?.url || uploadData.data?.filename;

  const versionRes = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/phien-ban`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      url: fileUrl,
      size: file.size,
    }),
  });

  const versionData = await versionRes.json();
  if (!versionRes.ok)
    throw new Error(
      versionData.message || "Không thể tạo siêu dữ liệu phiên bản mới",
    );
  return versionData.data;
};

export const shareStorageItemAPI = async (
  id: string,
  email: string,
  role: string = "viewer",
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/chia-se`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email, role }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi phân quyền truy cập thực thể lưu trữ");
  return data.data;
};

export const getStorageQuotaAPI = async () => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/han-muc`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải thông số dung lượng khả dụng",
    );
  return data.data as { used: number; limit: number };
};

export const createShortcutAPI = async (
  id: string,
  target_parent_id?: string,
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/loi-tat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_parent_id }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo liên kết tham chiếu (Shortcut)",
    );
  return mapItem(data.data) as StorageItem;
};

export const downloadZipAPI = async (ids: string[]) => {
  const token = getAuthToken();
  const query = ids.join(",");
  const url = `${API_URL}/luu-tru/tai-xuong-zip?ids=${query}`;

  const res = await fetch(url, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(
      errorData.message ||
        "Lỗi khởi chạy tiến trình nén và kết xuất dữ liệu (Zip)",
    );
  }

  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = "storage_download.zip";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
};

export const createProtectedShareLinkAPI = async (
  item_id: string,
  password?: string,
  expires_in_hours: number = 24,
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/link-chia-se/tao`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ item_id, password, expires_in_hours }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi tạo đường dẫn chia sẻ bảo mật");
  return data.data as ProtectedShareResult;
};

export const validateProtectedShareLinkAPI = async (
  shareToken: string,
  password?: string,
) => {
  const query = new URLSearchParams();
  if (password) query.set("password", password);
  const suffix = query.size ? `?${query.toString()}` : "";
  const res = await fetch(
    `${API_URL}/luu-tru/link-chia-se/xac-thuc/${encodeURIComponent(shareToken)}${suffix}`,
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.detail || data.message || "Không thể mở liên kết chia sẻ");
  return data.data as { item: SharedStorageItem; access_granted: boolean };
};

export const getPublicSharedStorageItemAPI = async (shareToken: string) => {
  const res = await fetch(
    `${API_URL}/luu-tru/chia-se/${encodeURIComponent(shareToken)}`,
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.detail || data.message || "Không thể mở liên kết chia sẻ",
    );
  return data.data as SharedStorageItem;
};

export const toggleStarItemAPI = async (id: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/danh-dau-sao/${id}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật trạng thái gắn sao");
  return data.data;
};

export const getStarredItemsAPI = async () => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/danh-dau-sao/danh-sach`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách gắn sao");
  return data.data.map(mapItem) as StorageItem[];
};

export const analyzeStorageQuotaAPI = async () => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/dung-luong/phan-tich`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải phân tích dung lượng");
  return data.data;
};

export const duplicateItemAPI = async (id: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/nhan-ban/${id}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi nhân bản tệp tin");
  return mapItem(data.data) as StorageItem;
};

export const setFolderColorAPI = async (
  folder_id: string,
  color_hex: string,
) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/thu-muc/${folder_id}/mau-sac`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ color_hex }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật màu sắc thư mục");
  return data.data;
};

export const updateItemTagsAPI = async (item_id: string, tags: string[]) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/phieu-tag/${item_id}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ tags }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật thẻ nhãn tệp");
  return data.data;
};

export const getPreviewPayloadAPI = async (item_id: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/tim-kiem/xem-truoc/${item_id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải dữ liệu xem trước");
  return data.data;
};

export interface FileVersionItem {
  version_id: string;
  url: string;
  size: number;
  created_at: string;
  is_active: boolean;
}

export interface QuotaAnalyticsData {
  total_quota_bytes: number;
  used_quota_bytes: number;
  free_quota_bytes: number;
  usage_percentage: number;
  total_files_count: number;
  total_folders_count: number;
  trashed_files_count: number;
  trashed_bytes: number;
  breakdown: Record<
    string,
    {
      count: number;
      size: number;
      percentage: number;
    }
  >;
}

export const getFileVersionsAPI = async (itemId: string): Promise<FileVersionItem[]> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/phien-ban`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử phiên bản");
  return data.data;
};

export const rollbackFileVersionAPI = async (itemId: string, versionId: string): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/phien-ban/${versionId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể khôi phục phiên bản");
  return mapItem(data.data);
};

export const setStarredAPI = async (itemId: string, isStarred: boolean): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/yeu-thich`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_starred: isStarred }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể cập nhật trạng thái yêu thích");
  return mapItem(data.data);
};

export const setTagsAndColorAPI = async (
  itemId: string,
  tags?: string[],
  color?: string
): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/nhan-dan`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ tags, color }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể cập nhật nhãn dán và màu");
  return mapItem(data.data);
};

export const getTrashedItemsAPI = async (): Promise<StorageItem[]> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/thung-rac`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách thùng rác");
  return data.data.map(mapItem);
};

export const restoreFromTrashAPI = async (itemId: string): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/thung-rac/${itemId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể khôi phục tệp");
  return mapItem(data.data);
};

export const emptyTrashAPI = async (): Promise<{ deleted_count: number }> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/thung-rac/don-sach`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể dọn sạch thùng rác");
  return data.data;
};

export const getStorageQuotaAnalyticsAPI = async (): Promise<QuotaAnalyticsData> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/dung-luong/phan-tich`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải phân tích dung lượng");
  return data.data;
};

export const shareInternalAPI = async (
  itemId: string,
  email: string,
  role: string = "viewer"
): Promise<{ message: string }> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/chia-se-noi-bo`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email, role }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể chia sẻ tệp");
  return data;
};

export const revokeInternalShareAPI = async (
  itemId: string,
  targetUserId: string
): Promise<void> => {
  const token = getAuthToken();
  const res = await fetch(
    `${API_URL}/luu-tru/tap-tin/${itemId}/chia-se-noi-bo/${targetUserId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể thu hồi quyền chia sẻ");
};

export const getSharedWithMeAPI = async (): Promise<StorageItem[]> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/duoc-chia-se-voi-toi`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tệp được chia sẻ");
  return data.data.map(mapItem);
};

export const lockStorageItemAPI = async (itemId: string): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/khoa`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể khóa tệp");
  return mapItem(data.data);
};

export const unlockStorageItemAPI = async (itemId: string): Promise<StorageItem> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/mo-khoa`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể mở khóa tệp");
  return mapItem(data.data);
};

export const getInlinePreviewUrlAPI = async (itemId: string): Promise<string> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/xem-truoc`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể lấy liên kết xem trước");
  return data.data.preview_url;
};

export const getSystemFilePreviewUrlAPI = async (
  filePath: string,
): Promise<string> => {
  const path = filePath
    .split("/")
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const res = await fetch(`${API_URL}/tai-len/luu-tru/xem-truoc/${path}`, {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo liên kết xem trước tệp");
  return data.data.preview_url;
};

export const getItemActivitiesAPI = async (itemId: string): Promise<any[]> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${itemId}/nhat-ky`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải nhật ký hoạt động");
  return data.data;
};

export const autoPurgeTrashAPI = async (
  days: number = 30
): Promise<{ purged_count: number; message: string }> => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/thung-rac/tu-dong-don?days=${days}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tự động dọn dẹp Thùng rác");
  return data.data;
};

export const uploadFileChunkedAPI = async (
  file: File,
  parentId?: string,
  onProgress?: (percent: number) => void
): Promise<StorageItem> => {
  const CHUNK_SIZE = 2 * 1024 * 1024;
  if (file.size <= CHUNK_SIZE) {
    const res = await uploadStorageFileAPI(file, parentId);
    if (onProgress) onProgress(100);
    return res;
  }

  const token = getAuthToken();
  const uploadId = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });

  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
  let lastData: any = null;

  for (let i = 0; i < totalChunks; i++) {
    const start = i * CHUNK_SIZE;
    const end = Math.min(file.size, start + CHUNK_SIZE);
    const chunkBlob = file.slice(start, end);

    const formData = new FormData();
    formData.append("file", chunkBlob, file.name);
    formData.append("upload_id", uploadId);
    formData.append("chunk_index", i.toString());
    formData.append("total_chunks", totalChunks.toString());
    formData.append("filename", file.name);

    const res = await fetch(`${API_URL}/tai-len/phan-doan`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || `Lỗi tải lên phân đoạn ${i + 1}/${totalChunks}`);
    }

    lastData = data.data;
    if (onProgress) {
      onProgress(Math.round(((i + 1) / totalChunks) * 100));
    }
  }

  return mapItem(lastData);
};
