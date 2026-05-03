import { API_URL, getToken } from "./auth.service";

export async function getPrivacySettingsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/profile/settings`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Không thể tải cài đặt riêng tư.");
  return await res.json();
}

export async function updatePrivacySettingsAPI(settings: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/profile/settings`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error("Cập nhật quyền riêng tư thất bại.");
  return await res.json();
}

export async function updateTypographyAPI(typography: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/read/typography`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(typography),
  });
  if (!res.ok) throw new Error("Cập nhật hiển thị thất bại.");
  return await res.json();
}

export async function updateGeneralSettingsAPI(settings: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/profile/settings`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error("Cập nhật cài đặt chung thất bại.");
  return await res.json();
}

export async function updateProfileAPI(data: any) {
  const token = getToken();
  const res = await fetch(`${API_URL}/profile/me`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) return null;
  return await res.json();
}

export async function applyAuthorAPI(data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/profile/author-application`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Gửi đơn đăng ký tác giả thất bại.");
  return await res.json();
}
