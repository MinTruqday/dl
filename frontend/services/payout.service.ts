import { API_URL, getAuthHeaders } from "./authentication.service";

export async function requestPayoutAPI(amount: number, bankInfo: any) {
  const res = await fetch(`${API_URL}/rut-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, bank_info: bankInfo }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Yêu cầu rút tiền thất bại");
  return data;
}

export async function getPayoutQueueAPI(status: string = "PENDING") {
  const res = await fetch(`${API_URL}/rut-tien/hang-doi?status=${status}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải hàng đợi thanh toán");
  return data;
}

export async function verifyPayoutAPI(payoutId: string, action: string) {
  const res = await fetch(`${API_URL}/rut-tien/${payoutId}/xac-thuc?action=${action}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xử lý thanh toán thất bại");
  return data;
}

export async function cancelPayoutAPI(payoutId: string) {
  const res = await fetch(`${API_URL}/rut-tien/${payoutId}/huy-bo`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Hủy yêu cầu rút tiền thất bại");
  return data;
}

export async function getMyPayoutsAPI() {
  const res = await fetch(`${API_URL}/rut-tien/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách yêu cầu rút tiền");
  return data;
}
