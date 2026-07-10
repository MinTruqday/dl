import { getToken as getAuthToken } from "@/features/authentication/services/session.service";
import { API_URL } from "@/features/authentication/services/session.service";

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
  created_at: string;
  updated_at: string;
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
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo cấu trúc thư mục lưu trữ");
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
  if (!res.ok) throw new Error(data.message || "Lỗi trích xuất danh sách thực thể lưu trữ");
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
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật siêu dữ liệu thực thể lưu trữ");
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
  if (!res.ok) throw new Error(data.message || "Lỗi xóa bỏ thực thể lưu trữ");
  return data.data;
};

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
    throw new Error(uploadData.message || "Lỗi đẩy dữ liệu lên máy chủ lưu trữ phân tán");

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
    throw new Error(fileData.message || "Lỗi đăng ký bản ghi dữ liệu vào hệ thống");

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
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi truy vấn tìm kiếm thực thể");
  return data.data.map(mapItem) as StorageItem[];
};

export const getRecentStorageItemsAPI = async (limit: number = 20) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/gan-day?limit=${limit}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi trích xuất danh sách truy cập gần đây");
  return data.data.map(mapItem) as StorageItem[];
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
  if (!res.ok) throw new Error(uploadData.message || "Lỗi đẩy dữ liệu lên máy chủ lưu trữ phân tán");

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
    throw new Error(versionData.message || "Lỗi khởi tạo siêu dữ liệu phiên bản mới");
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
  if (!res.ok) throw new Error(data.message || "Lỗi phân quyền truy cập thực thể lưu trữ");
  return data.data;
};

export const getStorageQuotaAPI = async () => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/han-muc`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi trích xuất thông số dung lượng khả dụng");
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
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo liên kết tham chiếu (Shortcut)");
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
    throw new Error(errorData.message || "Lỗi khởi chạy tiến trình nén và kết xuất dữ liệu (Zip)");
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

export const translateStorageDocumentAPI = async (
  id: string,
  target_lang: string = "vi",
) => {
  const token = getAuthToken();
  const res = await fetch(
    `${API_URL}/suy-luan/phan-tich-tai-lieu/${id}/dich-thuat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ target_lang }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi gọi API dịch thuật văn bản");
  return data.data;
};

export const getRelatedStorageItemsAPI = async (id: string) => {
  const token = getAuthToken();
  const res = await fetch(
    `${API_URL}/suy-luan/phan-tich-tai-lieu/${id}/lien-quan`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy xuất bộ dữ liệu tài liệu liên quan");
  return data.data.map(mapItem) as StorageItem[];
};
