import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function setDocumentPricingAPI(
  documentId: string,
  priceDl: number,
  isDrmProtected: boolean = true,
) {
  const res = await fetch(
    `${API_URL}/kiem-tien/tai-lieu/${documentId}/gia-ban`,
    {
      method: "PUT",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        price_dl: priceDl,
        is_drm_protected: isDrmProtected,
      }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật giá bán thất bại");
  return data;
}

export async function getAuthorRevenueAPI() {
  const res = await fetch(`${API_URL}/kiem-tien/thong-ke/doanh-thu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải số liệu doanh thu");
  return data;
}

export async function buyMembershipAPI(tier: "PRO" | "PREMIUM") {
  const res = await fetch(`${API_URL}/finance/monetization/membership`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ tier }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Failed to upgrade membership plan");
  }
  return data;
}
