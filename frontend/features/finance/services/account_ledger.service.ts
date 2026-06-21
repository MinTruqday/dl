import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function getWalletBalanceAPI() {
  const res = await fetch(`${API_URL}/vi-tien/so-du`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải số dư ví");
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
  const res = await fetch(`${API_URL}/vi-tien/lich-su?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử chi tiết");
  return data;
}

export async function redeemVoucherAPI(code: string) {
  const res = await fetch(`${API_URL}/vi-tien/doi-ma-qua-tang`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đổi mã quà tặng");
  return data;
}


export async function unlockPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/vi-tien/mo-khoa`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ post_id: postId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mở khóa bài viết thất bại");
  return data;
}

export async function getAuthorStatsAPI() {
  const res = await fetch(`${API_URL}/vi-tien/doanh-thu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải số liệu doanh thu");
  return data;
}

export async function purchaseDocumentAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/vi-tien/mua-hang/tai-lieu/${documentId}`,
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
    `${API_URL}/vi-tien/mua-hang/tai-lieu/${documentId}/chuong/${chapterId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mua chương thất bại");
  return data;
}
