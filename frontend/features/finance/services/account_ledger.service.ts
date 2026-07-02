import {
  API_URL,
  getAuthHeaders,
} from "@/features/auth/services/user_authentication.service";

export async function getWalletBalanceAPI() {
  const res = await fetch(`${API_URL}/vi-tien/so-du`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải số dư ví");
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
    throw new Error(data.message || "Không thể tải lịch sử chi tiết");
  return data;
}

export async function redeemVoucherAPI(code: string) {
  const res = await fetch(`${API_URL}/vi-tien/doi-ma-qua-tang`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đổi mã quà tặng");
  return data;
}
