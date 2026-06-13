import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function createSubscriptionPlanAPI(data: {
  name: string;
  description: string;
  price_dl: number;
  benefits: string[];
}) {
  const res = await fetch(`${API_URL}/kiem-tien/goi-thanh-vien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo gói hội viên thất bại");
  return result;
}

export async function getAuthorPlansAPI(authorId: string) {
  const res = await fetch(`${API_URL}/kiem-tien/goi-thanh-vien/${authorId}`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách gói hội viên");
  return data;
}

export async function subscribeToAuthorAPI(planId: string) {
  const res = await fetch(`${API_URL}/kiem-tien/register/${planId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đăng ký hội viên thất bại");
  return data;
}

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

export async function buyAITierAPI(tier: "PRO" | "PREMIUM") {
  const res = await fetch(`${API_URL}/finance/kiem-tien/ai-tier`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ tier }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || errorData?.message || "Nâng cấp gói AI thất bại");
  }
  return await res.json();
}
