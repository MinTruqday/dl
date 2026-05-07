import { API_URL, getAuthHeaders } from "./authentication.service";

export async function validateCouponAPI(code: string, amount: number) {
  const res = await fetch(`${API_URL}/ma-giam-gia/kiem-tra?code=${encodeURIComponent(code)}&amount=${amount}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mã giảm giá không hợp lệ");
  return data;
}

export async function getMyCouponsAPI() {
  const res = await fetch(`${API_URL}/ma-giam-gia/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách mã giảm giá");
  return data;
}
