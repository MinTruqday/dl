import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getSystemStatsAPI() {
  const res = await fetch(`${API_URL}/telemetry/statistics`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thống kê hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const res = await fetch(`${API_URL}/telemetry/health`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể kiểm tra sức khỏe hệ thống");
  return data;
}

export async function getAuditLogsAPI() {
  const res = await fetch(`${API_URL}/telemetry/check`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký hệ thống");
  return data;
}

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/telemetry/activity`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải nhật ký hoạt động điều hành",
    );
  return data;
}
