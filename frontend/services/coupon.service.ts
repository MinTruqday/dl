import { API_URL, getAuthHeaders } from "./authentication.service";

export async function validateCouponAPI(code: string, amount: number) {
  const res = await fetch(`${API_URL}/ma-giam-gia/kiem-tra?code=${encodeURIComponent(code)}&amount=${amount}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mã giảm giá không hợp lệ");
  return data;
}

export async function getCouponsAPI() {
  const res = await fetch(`${API_URL}/ma-giam-gia`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách mã giảm giá");
  return data;
}

export async function createCouponAPI(payload: any) {
  const res = await fetch(`${API_URL}/ma-giam-gia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo mã giảm giá thất bại");
  return data;
}

export async function approveCouponAPI(couponId: string, action: "approve" | "reject") {
  const res = await fetch(`${API_URL}/ma-giam-gia/${couponId}/phe-duyet?action=${action}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý phê duyệt thất bại");
  return data;
}

export async function toggleCouponStatusAPI(couponId: string) {
  const res = await fetch(`${API_URL}/ma-giam-gia/${couponId}/trang-thai`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật trạng thái thất bại");
  return data;
}

export async function deleteCouponAPI(couponId: string) {
  const res = await fetch(`${API_URL}/ma-giam-gia/${couponId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa mã giảm giá thất bại");
  return data;
}
