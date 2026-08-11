import {
  API_URL,
  getToken,
} from "@/shared/services/api-client";

export async function getPrivacySettingsAPI() {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu hình quyền riêng tư");
  return data;
}

export async function updatePrivacySettingsAPI(settings: any) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật cấu hình quyền riêng tư",
    );
  return data;
}

export async function updateTypographyAPI(typography: any) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(typography),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật cấu hình giao diện hiển thị",
    );
  return data;
}

export async function updateGeneralSettingsAPI(settings: any) {
  const token = getToken();
  if (!token)
    throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật cấu hình hệ thống");
  return data;
}

export async function updateProfileAPI(data: any) {
  const token = getToken();
  const res = await fetch(`${API_URL}/ho-so/ca-nhan`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) return null;
  return result;
}
