import { API_URL, getToken, getAuthHeaders } from "./auth.service";

export async function getFeaturedAuthorsAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/social/featured-authors?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách tác giả.");
  return await res.json();
}

export async function getFeedMe(offset: number = 0, limit: number = 10) {
  const headers = getAuthHeaders();
  const res = await fetch(
    `${API_URL}/social/feed?skip=${offset}&limit=${limit}`,
    {
      headers,
    },
  );
  if (!res.ok) return null;
  return await res.json();
}

export async function postQuoteAPI(
  documentId: string,
  quoteText: string,
  bgColor: string,
) {
  const token = getToken();
  if (!token) throw new Error("Không có quyền truy cập.");

  const res = await fetch(`${API_URL}/social/quotes`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id: documentId,
      quote_text: quoteText,
      background_color: bgColor,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Chia sẻ trích dẫn thất bại.");
  return data;
}

export const toggleReactionAPI = async (
  itemId: string,
  itemType: string,
  reactionType: string | null,
) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/reaction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ reaction_type: reactionType }),
  });
  if (!res.ok) throw new Error("Thả cảm xúc thất bại.");
  return res.json();
};

export const getFeedCommentsAPI = async (itemId: string, itemType: string) => {
  const token = getToken();
  const headers: any = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/comments`, {
    headers,
  });
  if (!res.ok) throw new Error("Lấy danh sách bình luận thất bại.");
  return res.json();
};

export const createFeedCommentAPI = async (
  itemId: string,
  itemType: string,
  content: string,
) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/comment`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error("Tạo bình luận thất bại.");
  return res.json();
};

export const toggleFeedBookmarkAPI = async (itemId: string) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/social/feed/${itemId}/bookmark`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
    },
  });
  if (!res.ok) throw new Error("Tải dữ liệu thất bại.");
  return res.json();
};

export async function uploadMediaAPI(formData: FormData) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác.");
  const res = await fetch(`${API_URL}/social/upload-media`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) throw new Error("Tải tệp tin lên thất bại.");
  return await res.json();
}

export async function getDiscussionsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/social/documents/${documentId}/discussions`,
  );
  if (!res.ok) throw new Error("Không thể tải thảo luận.");
  return await res.json();
}

export async function createDiscussionAPI(
  documentId: string,
  title: string,
  content: string,
) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/social/documents/${documentId}/discussions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: JSON.stringify({ title, content }),
    },
  );
  if (!res.ok) throw new Error("Tạo thảo luận thất bại.");
  return await res.json();
}
export async function getBannersAPI() {
  const res = await fetch(`${API_URL}/banners`);
  if (!res.ok) throw new Error("Không thể tải danh sách tiêu điểm.");
  return await res.json();
}

export async function replyDiscussionAPI(
  discussionId: string,
  content: string,
) {
  const token = getToken();
  const res = await fetch(
    `${API_URL}/social/discussions/${discussionId}/reply`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: JSON.stringify({ content }),
    },
  );
  if (!res.ok) throw new Error("Gửi trả lời thất bại.");
  return await res.json();
}
export const getNestedCommentsAPI = async (itemId: string) => {
  const token = getToken();
  const headers: any = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_URL}/items/${itemId}/comments`, { headers });
  if (!res.ok) throw new Error("Không thể tải thảo luận cộng đồng.");
  return await res.json();
};

export const createNestedCommentAPI = async (
  itemId: string,
  payload: { text: string; parent_id?: string | null; item_type?: string },
) => {
  const token = getToken();
  const res = await fetch(`${API_URL}/items/${itemId}/comments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Gửi thảo luận thất bại.");
  return await res.json();
};
export async function getStoriesAPI() {
  const res = await fetch(`${API_URL}/social/stories`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải tin mới.");
  return await res.json();
}

export async function viewStoryAPI(storyId: string) {
  const res = await fetch(`${API_URL}/social/stories/${storyId}/view`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Ghi nhận lượt xem thất bại.");
  return await res.json();
}

export async function reactToStoryAPI(
  storyId: string,
  reactionType: string = "heart",
) {
  const res = await fetch(
    `${API_URL}/social/stories/${storyId}/react?reaction_type=${reactionType}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Phản hồi tin thất bại.");
  return await res.json();
}

export async function getStoryViewersAPI(storyId: string) {
  const res = await fetch(`${API_URL}/social/stories/${storyId}/viewers`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải danh sách người xem.");
  return await res.json();
}

export async function voteStoryPollAPI(storyId: string, optionIdx: number) {
  const res = await fetch(
    `${API_URL}/social/stories/${storyId}/poll/vote?option_index=${optionIdx}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Bình chọn thất bại.");
  return await res.json();
}

export async function answerStoryQuizAPI(storyId: string, optionIdx: number) {
  const res = await fetch(
    `${API_URL}/social/stories/${storyId}/quiz/answer?option_index=${optionIdx}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Trả lời quiz thất bại.");
  return await res.json();
}

export async function replyStoryAPI(storyId: string, message: string) {
  const res = await fetch(
    `${API_URL}/social/stories/${storyId}/reply?message=${encodeURIComponent(message)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Gửi trả lời thất bại.");
  return await res.json();
}

export async function createStoryAPI(payload: any) {
  const res = await fetch(`${API_URL}/social/stories`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Tạo tin thất bại.");
  return await res.json();
}

export async function deleteStoryAPI(storyId: string) {
  const res = await fetch(`${API_URL}/social/stories/${storyId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Xóa tin thất bại.");
  return await res.json();
}

export async function getArchivedStoriesAPI() {
  const res = await fetch(`${API_URL}/social/stories/me/archive`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải kho lưu trữ tin.");
  return await res.json();
}

export async function getSocialRankingAPI() {
  const res = await fetch(`${API_URL}/social/ranking`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải bảng xếp hạng.");
  return await res.json();
}

export async function getReaderRankingAPI() {
  const res = await fetch(`${API_URL}/social/reader-ranking`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải bảng xếp hạng độc giả.");
  return await res.json();
}

export async function getIntersectionFriendsAPI() {
  const res = await fetch(`${API_URL}/social/intersection-friends`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải gợi ý kết nối.");
  return await res.json();
}

export async function getTrendingTagsAPI() {
  const res = await fetch(`${API_URL}/social/trending-tags`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải xu hướng.");
  return await res.json();
}

export async function getSuggestedDocumentsAPI() {
  const res = await fetch(`${API_URL}/social/suggested-documents`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải gợi ý tài liệu.");
  return await res.json();
}

export async function createPostAPI(payload: any) {
  const res = await fetch(`${API_URL}/social/posts`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Đăng bài thất bại.");
  return await res.json();
}

export async function updatePostAPI(postId: string, content: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error("Cập nhật bài viết thất bại.");
  return await res.json();
}

export async function deletePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Xóa bài viết thất bại.");
  return await res.json();
}

export async function repostPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}/repost`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Chia sẻ lại thất bại.");
  return await res.json();
}

export async function savePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}/save`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Lưu bài viết thất bại.");
  return await res.json();
}

export async function pinPostAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}/pin`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Ghim bài viết thất bại.");
  return await res.json();
}

export async function hidePostAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}/hide`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Ẩn bài viết thất bại.");
  return await res.json();
}

export async function reportPostAPI(postId: string, reason: string) {
  const res = await fetch(
    `${API_URL}/social/posts/${postId}/report?reason=${encodeURIComponent(reason)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Báo cáo bài viết thất bại.");
  return await res.json();
}

export async function followUserAPI(userId: string) {
  const res = await fetch(`${API_URL}/social/users/${userId}/follow`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Theo dõi người dùng thất bại.");
  return await res.json();
}

export async function votePostAPI(postId: string, amount: number) {
  const res = await fetch(`${API_URL}/wallet/vote`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: postId, item_type: "post", amount }),
  });
  if (!res.ok) throw new Error("Bình chọn/Tặng thưởng thất bại.");
  return await res.json();
}

export async function submitPollVoteAPI(postId: string, optionId: string) {
  const res = await fetch(
    `${API_URL}/social/polls/${postId}/vote/${optionId}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  if (!res.ok) throw new Error("Bình chọn thất bại.");
  return await res.json();
}

export async function getFeedCommentsAPI_V2(itemId: string, itemType: string) {
  const res = await fetch(`${API_URL}/social/${itemType}/${itemId}/comments`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải bình luận.");
  return await res.json();
}

export async function createCommentAPI(payload: any) {
  const res = await fetch(`${API_URL}/comments`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Gửi bình luận thất bại.");
  return await res.json();
}

export async function getFeedAPI(
  tab: string,
  skip: number,
  limit: number,
  itemType?: string,
  sort?: string,
) {
  let url = `${API_URL}/social/feed?tab=${tab}&skip=${skip}&limit=${limit}`;
  if (itemType) url += `&item_type=${itemType}`;
  if (sort) url += `&sort=${sort}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Không thể tải bảng tin.");
  return await res.json();
}

export async function recordPostViewAPI(postId: string) {
  const res = await fetch(`${API_URL}/social/posts/${postId}/view`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Ghi nhận lượt xem thất bại.");
  return await res.json();
}

export async function getUserProfileAPI(slug: string) {
  const res = await fetch(`${API_URL}/social/users/${slug}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Không thể tải thông tin người dùng.");
  return await res.json();
}

export const searchUsersAPI = async (query: string, limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/social/search-users?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
  if (!res.ok) throw new Error("Không thể tìm kiếm người dùng.");
  return await res.json();
};

export async function getDocumentReviewsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/reading/${documentId}/reviews`);
  if (!res.ok) throw new Error("Không thể tải đánh giá.");
  return await res.json();
}

export async function createDocumentReviewAPI(
  documentId: string,
  rating: number,
  text: string,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/reading/${documentId}/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: JSON.stringify({ rating, comment: text }),
  });
  if (!res.ok) throw new Error("Đánh giá thất bại.");
  return await res.json();
}
