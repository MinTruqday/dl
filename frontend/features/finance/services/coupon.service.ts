import { API_URL, getAuthHeaders } from "./authentication.service";

export async function validateCouponAPI(code: string, documentId?: string) {
  const url =
    `${API_URL}/coupon/kiem-tra?code=${encodeURIComponent(code)}` +
    (documentId ? `&document_id=${documentId}` : "");
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mã ưu đãi không hợp lệ");
  return data;
}

export async function getCouponsAPI() {
  const res = await fetch(`${API_URL}/coupon`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách mã ưu đãi");
  return data;
}

export async function createCouponAPI(payload: any) {
  const res = await fetch(`${API_URL}/coupon`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo mã ưu đãi thất bại");
  return data;
}

export async function approveCouponAPI(
  couponId: string,
  action: "approve" | "reject",
) {
  const res = await fetch(
    `${API_URL}/coupon/${couponId}/phe-duyet?action=${action}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý phê duyệt thất bại");
  return data;
}

export async function toggleCouponStatusAPI(couponId: string) {
  const res = await fetch(`${API_URL}/coupon/${couponId}/trang-thai`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật trạng thái thất bại");
  return data;
}

export async function deleteCouponAPI(couponId: string) {
  const res = await fetch(`${API_URL}/coupon/${couponId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa mã ưu đãi thất bại");
  return data;
}
