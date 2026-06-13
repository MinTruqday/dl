import { API_URL, getAuthHeaders } from "./authentication.service";

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
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử giao dịch");
  return data;
}

export async function getDetailedHistoryAPI(skip: number = 0, limit: number = 30) {
  const res = await fetch(`${API_URL}/vi-tien/lich-su?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải lịch sử chi tiết");
  return data;
}

export async function redeemVoucherAPI(code: string) {
  const res = await fetch(`${API_URL}/vi-tien/ma-qua-tang/doi-ma`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đổi mã quà tặng");
  return data;
}

export async function voteItemAPI(itemId: string, itemType: string, amount: number) {
  const res = await fetch(`${API_URL}/vi-tien/binh-chon`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId, item_type: itemType, amount }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bình chọn thất bại");
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
  if (!res.ok) throw new Error(data.message || "Không thể tải số liệu doanh thu");
  return data;
}

export async function purchaseDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/vi-tien/giao-dich-mua/tai-lieu/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mua tài liệu thất bại");
  return data;
}

export async function purchaseChapterAPI(documentId: string, chapterId: string) {
  const res = await fetch(`${API_URL}/vi-tien/giao-dich-mua/tai-lieu/${documentId}/chuong/${chapterId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Mua chương thất bại");
  return data;
}


