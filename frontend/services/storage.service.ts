import { getToken as getAuthToken } from "@/services/authentication.service";
import { API_URL } from "@/services/authentication.service";

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
  shared_with?: Array<{user_id: string; role: string}>;
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
  if (!res.ok) throw new Error(data.message || "Failed to create folder");
  return data.data;
};

export const listStorageItemsAPI = async (parent_id?: string, is_trashed: boolean = false) => {
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
  if (!res.ok) throw new Error(data.message || "Failed to fetch storage items");
  return data.data as StorageItem[];
};

export const updateStorageItemAPI = async (id: string, updates: Partial<StorageItem>) => {
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
  if (!res.ok) throw new Error(data.message || "Failed to update item");
  return data.data;
};

export const deleteStorageItemAPI = async (id: string, hard_delete: boolean = false) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}?hard_delete=${hard_delete}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to delete item");
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
  if (!res.ok) throw new Error(uploadData.message || "Failed to upload file to storage");
  
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
  if (!registerRes.ok) throw new Error(fileData.message || "Failed to register file");
  
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
  if (!res.ok) throw new Error(data.message || "Failed to search items");
  return data.data as StorageItem[];
};

export const getRecentStorageItemsAPI = async (limit: number = 20) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/gan-day?limit=${limit}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to fetch recent items");
  return data.data as StorageItem[];
};

export const copyStorageItemAPI = async (id: string, target_parent_id?: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/copy`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}` 
    },
    body: JSON.stringify({ target_parent_id }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to copy item");
  return data.data;
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
  if (!res.ok) throw new Error(uploadData.message || "Failed to upload file");
  
  const fileUrl = uploadData.data?.url || uploadData.data?.filename;
  
  const versionRes = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/version`, {
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
  if (!versionRes.ok) throw new Error(versionData.message || "Failed to add version");
  return versionData.data;
};

export const shareStorageItemAPI = async (id: string, email: string, role: string = "viewer") => {
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
  if (!res.ok) throw new Error(data.message || "Failed to share item");
  return data.data;
};

export const getStorageQuotaAPI = async () => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/quota`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to get quota");
  return data.data as { used: number; limit: number };
};

export const createShortcutAPI = async (id: string, target_parent_id?: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/luu-tru/tap-tin/${id}/shortcut`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_parent_id }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to create shortcut");
  return data.data as StorageItem;
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
    throw new Error(errorData.message || "Failed to download zip");
  }
  
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = "storage_download.zip";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
};

export const translateStorageDocumentAPI = async (id: string, target_lang: string = "vi") => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/ai/tai-lieu-luu-tru/${id}/dich`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_lang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to translate document");
  return data.data;
};

export const getRelatedStorageItemsAPI = async (id: string) => {
  const token = getAuthToken();
  const res = await fetch(`${API_URL}/ai/tai-lieu-luu-tru/${id}/lien-quan`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Failed to get related documents");
  return data.data as StorageItem[];
};
