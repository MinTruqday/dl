import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export interface WithdrawalBankInfo {
  bank_code?: string;
  bank_name: string;
  account_number: string;
  account_name: string;
}

export async function requestWithdrawalAPI(
  amount: number,
  bankInfo: WithdrawalBankInfo,
) {
  const res = await fetch(`${API_URL}/rut-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ amount, bank_info: bankInfo }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo yêu cầu rút tiền");
  return data;
}

export async function getWithdrawalQueueAPI(status: string = "PENDING") {
  const res = await fetch(`${API_URL}/rut-tien/hang-doi?status=${status}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải hàng đợi thanh toán");
  return data;
}

export async function verifyWithdrawalAPI(
  withdrawalId: string,
  action: string,
) {
  const res = await fetch(
    `${API_URL}/rut-tien/${withdrawalId}/xac-minh?action=${action}`,
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
