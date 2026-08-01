import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function createDepositLinkAPI(amount: number) {
  const res = await fetch(`${API_URL}/nap-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, payment_method: "PAYOS" }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo phiên giao dịch nạp tiền");
  return data;
}

export async function verifyDepositAPI(orderCode: number) {
  const res = await fetch(`${API_URL}/nap-tien/kiem-tra/${orderCode}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi xác thực trạng thái giao dịch nạp tiền");
  return data;
}
