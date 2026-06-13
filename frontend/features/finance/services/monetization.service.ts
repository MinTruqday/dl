import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function createSubscriptionPlanAPI(data: {
  name: string;
  description: string;
  price_dl: number;
  benefits: string[];
}) {
  const res = await fetch(`${API_URL}/monetization/goi-hoi-vien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const result = await res.json();
  if (!res.ok) throw new Error(result.message || "Tạo gói hội viên thất bại");
  return result;
}

export async function getAuthorPlansAPI(authorId: string) {
  const res = await fetch(`${API_URL}/monetization/goi-hoi-vien/${authorId}`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách gói hội viên");
  return data;
}

export async function subscribeToAuthorAPI(planId: string) {
  const res = await fetch(`${API_URL}/monetization/register/${planId}`, {
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
    `${API_URL}/monetization/document/${documentId}/gia-ban`,
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
  const res = await fetch(`${API_URL}/monetization/thong-ke/doanh-thu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải số liệu doanh thu");
  return data;
}
