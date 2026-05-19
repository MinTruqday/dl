import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getAIFeedSummaryAPI() {
  const res = await fetch(`${API_URL}/ai/cong-dong/tom-tat-bang-tin`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tóm tắt bảng tin");
  return data;
}

export async function getFriendSuggestionsAPI() {
  const res = await fetch(`${API_URL}/cong-dong/goi-y-ket-noi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải gợi ý kết nối");
  return data;
}

export async function getFeedAPI(
  tab: string = "foryou",
  skip: number = 0,
  limit: number = 20,
  itemType?: string,
  sort?: string,
) {
  let url = `${API_URL}/cong-dong/bang-tin?tab=${tab}&skip=${skip}&limit=${limit}`;
  if (itemType) url += `&item_type=${itemType}`;
  if (sort) url += `&sort=${sort}`;
  
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng tin");
  return data;
}

export async function createPostAPI(payload: any) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đăng bài viết thất bại");
  return data;
}

export async function toggleReactionAPI(
  postId: string,
  reactionType: string = "like",
) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/cam-xuc?reaction_type=${reactionType}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thao tác cảm xúc thất bại");
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

export async function togglePinPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/ghim`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật trạng thái ghim thất bại");
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

export async function toggleFollowUserAPI(userId: string) {
  const res = await fetch(`${API_URL}/cong-dong/nguoi-dung/${userId}/nguoi-theo-doi`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật theo dõi thất bại");
  return data;
}

export async function uploadMediaAPI(formData: FormData) {
  const res = await fetch(`${API_URL}/cong-dong/luu-tru`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tải lên tệp tin thất bại");
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

export async function getTrendingTagsAPI(limit: number = 10) {
  const res = await fetch(`${API_URL}/cong-dong/hashtag-xu-huong?limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải xu hướng hashtag");
  return data;
}

export async function getSuggestedDocumentsAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/cong-dong/goi-y-tai-lieu?limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải gợi ý tài liệu");
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

export async function savePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet/${postId}/luu-lai`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lưu bài viết thất bại");
  return data;
}

export async function getSavedPostsAPI(skip: number = 0, limit: number = 20) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet-da-luu?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bài viết đã lưu");
  return data;
}

export async function searchUsersAPI(query: string, limit: number = 10) {
  const res = await fetch(`${API_URL}/cong-dong/tim-kiem-nguoi-dung?q=${encodeURIComponent(query)}&limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm kiếm người dùng thất bại");
  return data;
}

export async function votePollAPI(postId: string, optionId: string) {
  const res = await fetch(`${API_URL}/cong-dong/khao-sat/${postId}/binh-chon/${optionId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bình chọn thất bại");
  return data;
}

export async function shareExcerptAPI(data: any) {
  const res = await fetch(`${API_URL}/cong-dong/chia-se-trich-doan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.message || "Chia sẻ trích đoạn thất bại");
  return json;
}

export async function getNestedCommentsAPI(itemId: string) {
  const res = await fetch(`${API_URL}/binh-luan/doi-tuong/${itemId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách bình luận");
  return data;
}

export async function createNestedCommentAPI(
  itemId: string,
  payload: {
    text: string;
    parent_id?: string | null;
    item_type: string;
  }
) {
  const res = await fetch(`${API_URL}/binh-luan/doi-tuong/${itemId}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      item_id: itemId,
      item_type: payload.item_type,
      content: payload.text,
      parent_id: payload.parent_id || null,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi bình luận thất bại");
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


