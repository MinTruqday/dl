import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export async function getWalletBalanceAPI() {
  const res = await fetch(`${API_URL}/vi-tien/so-du`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thông tin số dư ví điện tử");
  return data;
}

export async function getWalletHistoryAPI() {
  const res = await fetch(`${API_URL}/vi-tien/lich-su`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử giao dịch");
  return data;
}

export async function getDetailedHistoryAPI(
  skip: number = 0,
  limit: number = 30,
) {
  const res = await fetch(
    `${API_URL}/vi-tien/lich-su?offset=${skip}&limit=${limit}`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký giao dịch chi tiết");
  return data;
}

export type TransferRecipient = {
  recipient_id: string;
  full_name: string;
  email: string;
  slug: string;
  account_number: string;
};

export async function verifyTransferRecipientAPI(recipientIdentifier: string) {
  const res = await fetch(`${API_URL}/vi-tien/xac-minh-nguoi-nhan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ recipient_identifier: recipientIdentifier }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không tìm thấy người nhận");
  return data as { data: TransferRecipient };
}

export async function transferFundsAPI(input: {
  recipient_identifier: string;
  amount: number;
  note: string;
  idempotency_key: string;
}) {
  const res = await fetch(`${API_URL}/vi-tien/chuyen-tien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể chuyển tiền");
  return data;
}
