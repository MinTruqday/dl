import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getWalletBalanceAPI() {
  const res = await fetch(`${API_URL}/vi-tien/so-du`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thông tin số dư ví điện tử");
  return data;
}

export async function getWalletHistoryAPI() {
  const res = await fetch(`${API_URL}/vi-tien/lich-su`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử giao dịch");
  return data;
}

export async function getDetailedHistoryAPI(
  skip: number = 0,
  limit: number = 30,
) {
  const res = await fetch(`${API_URL}/vi-tien/lich-su?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký giao dịch chi tiết");
  return data;
}
