import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getSystemStatsAPI() {
  const res = await fetch(`${API_URL}/giam-sat/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải số liệu thống kê hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const res = await fetch(`${API_URL}/giam-sat/tinh-trang`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi giám sát trạng thái sức khỏe hệ thống",
    );
  return data;
}

export async function getAuditLogsAPI() {
  const res = await fetch(`${API_URL}/giam-sat/kiem-tra`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký hoạt động hệ thống");
  return data;
}

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/giam-sat/hoat-dong`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải nhật ký hoạt động kiểm duyệt",
    );
  return data;
}
