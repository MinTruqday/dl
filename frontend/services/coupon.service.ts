import { API_URL, getToken } from "./auth.service";

export async function getAuthorCouponsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/coupons`, {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể tải danh sách mã giảm giá.");
  return await res.json();
}

export async function createAuthorCouponAPI(data: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/coupons`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Không thể tạo mã giảm giá mới.");
  return await res.json();
}

export async function toggleCouponStatusAPI(couponId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/coupons/${couponId}/toggle`, {
    method: "PATCH",
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể cập nhật trạng thái mã giảm giá.");
  return await res.json();
}

export async function deleteCouponAPI(couponId: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/coupons/${couponId}`, {
    method: "DELETE",
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("Không thể xóa mã giảm giá.");
  return await res.json();
}
