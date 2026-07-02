import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export async function getPrivacySettingsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/ho-so/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cài đặt riêng tư");
  return data;
}

export async function updatePrivacySettingsAPI(settings: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
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
    throw new Error(data.message || "Cập nhật quyền riêng tư thất bại");
  return data;
}

export async function updateTypographyAPI(typography: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/doc-hieu/giao-dien`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(typography),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật hiển thị thất bại");
  return data;
}

export async function updateGeneralSettingsAPI(settings: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
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
    throw new Error(data.message || "Cập nhật cài đặt chung thất bại");
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
