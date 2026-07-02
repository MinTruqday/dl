import {
  API_URL,
  getAuthHeaders,
} from "@/features/auth/services/user_authentication.service";

export interface QuotaUsage {
  limit_requests: number;
  limit_tokens: number;
  used_requests: number;
  used_tokens: number;
  remaining_requests: number;
  remaining_tokens: number;
}

export async function getMyQuotaAPI(): Promise<QuotaUsage> {
  const res = await fetch(`${API_URL}/han-muc/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể lấy thông tin hạn mức");
  return data.data;
}

export async function updateRoleQuotaAPI(role: string, limits: any) {
  const res = await fetch(`${API_URL}/han-muc/cai-dat/${role}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(limits),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật cấu hình thất bại");
  return data;
}

export async function getGlobalQuotaConfigAPI() {
  const res = await fetch(`${API_URL}/han-muc/cai-dat`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lấy cấu hình thất bại");
  return data.data;
}
