import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function requestWithdrawalAPI(amount: number, bankInfo: any) {
  const res = await fetch(`${API_URL}/rut-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, bank_info: bankInfo }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo yêu cầu rút tiền");
  return data;
}

export async function getWithdrawalQueueAPI(status: string = "PENDING") {
  const res = await fetch(`${API_URL}/rut-tien/hang-doi?status=${status}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất hàng đợi thanh toán");
  return data;
}

export async function verifyWithdrawalAPI(
  withdrawalId: string,
  action: string,
) {
  const res = await fetch(
    `${API_URL}/rut-tien/${withdrawalId}/auth?action=${action}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xử lý luồng thanh toán");
  return data;
}

export async function cancelWithdrawalAPI(withdrawalId: string) {
  const res = await fetch(`${API_URL}/rut-tien/${withdrawalId}/huy`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi hủy bỏ yêu cầu rút tiền");
  return data;
}

export async function getMyWithdrawalsAPI() {
  const res = await fetch(`${API_URL}/rut-tien/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất danh sách yêu cầu rút tiền");
  return data;
}
