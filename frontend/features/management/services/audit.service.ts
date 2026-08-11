import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export interface AuditQueryParams {
  page?: number;
  page_size?: number;
  module?: string;
  severity?: string;
  status?: string;
  action?: string;
  actor_id?: string;
  search?: string;
  from_date?: string;
  to_date?: string;
  format?: string;
}

export async function getAuditRecordsAPI(params: AuditQueryParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });

  const queryStr = searchParams.toString();
  const url = `${API_URL}/kiem-toan/nhat-ky${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.message || "Không thể tải dữ liệu kiểm toán");
  }
  return data;
}

export async function getAuditStatsAPI() {
  const res = await fetch(`${API_URL}/kiem-toan/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.message || "Không thể tải dữ liệu thống kê kiểm toán");
  }
  return data;
}

export async function exportAuditRecordsAPI(params: AuditQueryParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });

  const queryStr = searchParams.toString();
  const url = `${API_URL}/kiem-toan/ket-xuat${queryStr ? `?${queryStr}` : ""}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.message || "Không thể kết xuất báo cáo kiểm toán");
  }
  return data;
}

export async function verifyAuditIntegrityAPI(logId?: string) {
  const url = `${API_URL}/kiem-toan/kiem-tra-toan-ven${logId ? `?log_id=${logId}` : ""}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.message || "Không thể kiểm tra tính toàn vẹn dữ liệu");
  }
  return data;
}

export async function getModeratorActivityAPI() {
  const res = await fetch(`${API_URL}/kiem-toan/logs`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) return { data: [] };
  return data;
}
