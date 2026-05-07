import { API_URL, getAuthHeaders } from "./authentication.service";

export async function createPaymentSessionAPI(amount: number, method: string = "momo") {
  const res = await fetch(`${API_URL}/cong-thanh-toan/phien-thanh-toan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, method }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Khởi tạo phiên thanh toán thất bại");
  return data;
}

export async function checkPaymentStatusAPI(sessionId: string) {
  const res = await fetch(`${API_URL}/cong-thanh/kiem-tra/${sessionId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể kiểm tra trạng thái thanh toán");
  return data;
}
