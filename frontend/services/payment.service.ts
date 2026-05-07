import { API_URL, getAuthHeaders } from "./authentication.service";

export const depositDLAPI = async (amountVnd: number) => {
  const res = await fetch(`${API_URL}/thanh-toan/nap-tien?amount_vnd=${amountVnd}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể khởi tạo giao dịch nạp tiền");
  return data;
}
