import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function getSystemStatsAPI() {
  const res = await fetch(`${API_URL}/giam-sat/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thống kê hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const res = await fetch(`${API_URL}/giam-sat/tinh-trang`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể kiểm tra sức khỏe hệ thống");
  return data;
}

export async function getAuditLogsAPI() {
  const res = await fetch(`${API_URL}/giam-sat/kiem-tra`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký hệ thống");
  return data;
}

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/giam-sat/hoat-dong`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải nhật ký hoạt động điều hành",
    );
  return data;
}
