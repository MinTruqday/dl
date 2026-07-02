import {
  API_URL,
  getAuthHeaders,
} from "@/features/auth/services/user_authentication.service";

export async function createDepositLinkAPI(amount: number) {
  const res = await fetch(`${API_URL}/nap-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, method: "payos" }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Khởi tạo liên kết nạp tiền thất bại");
  return data;
}

export async function verifyDepositAPI(orderCode: number) {
  const res = await fetch(`${API_URL}/nap-tien/kiem-tra/${orderCode}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể kiểm tra trạng thái nạp tiền");
  return data;
}
