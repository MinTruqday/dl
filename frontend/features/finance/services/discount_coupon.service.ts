import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";


export async function getCouponsAPI() {
  const res = await fetch(`${API_URL}/ma-qua-tang`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách mã ưu đãi");
  return data;
}

export async function createCouponAPI(payload: any) {
  const res = await fetch(`${API_URL}/ma-qua-tang`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo mã ưu đãi thất bại");
  return data;
}


export async function deleteCouponAPI(couponId: string) {
  const res = await fetch(`${API_URL}/ma-qua-tang/${couponId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa mã ưu đãi thất bại");
  return data;
}
