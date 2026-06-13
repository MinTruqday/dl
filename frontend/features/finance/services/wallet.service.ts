import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getWalletBalanceAPI() {
  const res = await fetch(`${API_URL}/wallet/balance`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải số dư ví");
  return data;
}

export async function getWalletHistoryAPI() {
  const res = await fetch(`${API_URL}/wallet/history`, {
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
  const res = await fetch(`${API_URL}/wallet/history?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử chi tiết");
  return data;
}

export async function redeemVoucherAPI(code: string) {
  const res = await fetch(`${API_URL}/wallet/coupon-code/redeem`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đổi mã quà tặng");
  return data;
}


export async function unlockPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/wallet/unlock`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: postId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mở khóa bài viết thất bại");
  return data;
}

export async function getAuthorStatsAPI() {
  const res = await fetch(`${API_URL}/wallet/revenue`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải số liệu doanh thu");
  return data;
}

export async function purchaseDocumentAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/wallet/purchase/document/${documentId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mua tài liệu thất bại");
  return data;
}

export async function purchaseChapterAPI(
  documentId: string,
  chapterId: string,
) {
  const res = await fetch(
    `${API_URL}/wallet/purchase/document/${documentId}/chapter/${chapterId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mua chương thất bại");
  return data;
}
