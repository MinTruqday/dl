import {
  API_URL,
  getToken,
  getAuthHeaders,
} from "@/shared/services/api-client";

export const getAnnouncementsAPI = async () => {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/thong-bao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(resultData.message || "Không thể tải dữ liệu thông báo");
  return resultData;
};

export const markAnnouncementReadAPI = async (id: string) => {
  const res = await fetch(`${API_URL}/thong-bao/${id}/doc-hieu`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(
      resultData.message || "Không thể cập nhật trạng thái thông báo",
    );
  return resultData;
};

export const markAllAnnouncementsReadAPI = async () => {
  const res = await fetch(`${API_URL}/thong-bao/doc-tat-ca`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(
      resultData.message || "Không thể cập nhật trạng thái hàng loạt",
    );
  return resultData;
};

export const deleteAnnouncementAPI = async (id: string) => {
  const res = await fetch(`${API_URL}/thong-bao/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const resultData = await res.json();
  if (!res.ok)
    throw new Error(resultData.message || "Không thể xóa thông báo");
  return resultData;
};

export const getAnnouncementSettingsAPI = async () => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể tải cấu hình hệ thống thông báo");
  return await res.json();
};

export const updateAnnouncementSettingsAPI = async (settings: any) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/thong-bao/cai-dat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error("Không thể lưu cấu hình hệ thống thông báo");
  return await res.json();
};
