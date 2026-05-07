import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getDiscussionsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/cong-dong/tai-lieu/${documentId}/thao-luan`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải thảo luận");
  return data;
}

export async function createDiscussionAPI(
  documentId: string,
  title: string,
  content: string,
) {
  const res = await fetch(
    `${API_URL}/cong-dong/tai-lieu/${documentId}/thao-luan`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo thảo luận mới thành công");
  return data;
}

export async function replyDiscussionAPI(
  discussionId: string,
  content: string,
) {
  const res = await fetch(
    `${API_URL}/cong-dong/thao-luan/${discussionId}/phan-hoi`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Phản hồi thảo luận thất bại");
  return data;
}

export async function getDocumentReviewsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/danh-gia/${documentId}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải đánh giá");
  return data;
}

export async function createDocumentReviewAPI(
  documentId: string,
  rating: number,
  text: string,
) {
  const res = await fetch(`${API_URL}/danh-gia/${documentId}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ rating, comment: text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đánh giá thất bại");
  return data;
}
