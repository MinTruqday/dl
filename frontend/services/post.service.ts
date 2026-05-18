import { API_URL, getAuthHeaders, getToken } from "./authentication.service";

export async function createPostAPI(payload: any) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đăng bài thất bại");
  return data;
}

export async function updatePostAPI(postId: string, content: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật bài viết thất bại");
  return data;
}

export async function deletePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa bài viết thất bại");
  return data;
}

export async function repostPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/chia-se-lai`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chia sẻ lại thất bại");
  return data;
}

export async function savePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/luu-lai`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lưu bài viết thất bại");
  return data;
}

export async function pinPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/ghim`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghim bài viết thất bại");
  return data;
}

export async function hidePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/an`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ẩn bài viết thất bại");
  return data;
}

export async function reportPostAPI(postId: string, reason: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/bao-cao`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Báo cáo bài viết thất bại");
  return data;
}

export async function recordPostViewAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/luot-xem`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghi nhận lượt xem thất bại");
  return data;
}

export const toggleReactionAPI = async (
  itemId: string,
  itemType: string,
  reactionType: string | null,
) => {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${itemId}/cam-xuc?reaction_type=${reactionType || "like"}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thả cảm xúc thất bại");
  return data;
};

export async function votePostAPI(postId: string, amount: number) {
  const res = await fetch(`${API_URL}/vi-tien/binh-chon`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: postId, item_type: "post", amount }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bình chọn/Tặng thưởng thất bại");
  return data;
}

export async function postQuoteAPI(
  documentId: string,
  quoteText: string,
  bgColor: string,
) {
  const res = await fetch(`${API_URL}/cong-dong/chia-se-trich-doan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      text: quoteText,
      bg_color: bgColor,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Chia sẻ trích dẫn thất bại");
  return data;
}
