import { API_URL, getToken } from "./auth.service";

export async function getAuthorRevenueAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/monetization/analytics/revenue/`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể tải số liệu doanh thu.");
  return await res.json();
}

// Alias for backward compatibility
export const getRevenueAPI = getAuthorRevenueAPI;

export async function setDocumentPricingAPI(documentId: string, price: number) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/monetization/documents/${documentId}/pricing/`,
    {
      method: "PUT",
      headers: {
        Authorization: "Bearer " + token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ price_dl: price }),
    },
  );
  if (!res.ok) throw new Error("Không thể cập nhật giá bán.");
  return await res.json();
}

export async function requestPayoutDetailedAPI(amount: number, bankInfo: any) {
  const token = getToken();
  const res = await fetch(`${API_URL}/payouts/`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ amount, bank_info: bankInfo }),
  });
  if (!res.ok) throw new Error("Yêu cầu rút tiền thất bại.");
  return await res.json();
}

export async function getMyPayoutsAPI() {
  const token = getToken();
  const res = await fetch(`${API_URL}/payouts/my/`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể tải danh sách yêu cầu rút tiền.");
  return await res.json();
}
