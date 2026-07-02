import {
  API_URL,
  getAuthHeaders,
} from "@/features/auth/services/user_authentication.service";

export async function createCommentAPI(payload: {
  item_id: string;
  item_type: string;
  content: string;
  parent_id?: string | null;
}) {
  const res = await fetch(`${API_URL}/cong-tac/binh-luan`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đăng bình luận thất bại");
  return data;
}

export async function getCommentsByItemAPI(itemId: string) {
  const res = await fetch(`${API_URL}/cong-tac/binh-luan/muc-tieu/${itemId}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách bình luận");
  return data;
}

export async function editCommentAPI(commentId: string, content: string) {
  const res = await fetch(`${API_URL}/cong-tac/binh-luan/${commentId}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chỉnh sửa bình luận thất bại");
  return data;
}

export async function deleteCommentAPI(commentId: string) {
  const res = await fetch(
    `${API_URL}/cong-tac/binh-luan/muc-tieu/${commentId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa bình luận thất bại");
  return data;
}
