import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getDocumentReviewsAPI(documentId: string) {
  const res = await fetch(`${API_URL}/danh-gia/${documentId}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải đánh giá");
  return data;
}

export async function createDocumentReviewAPI(
  documentId: string,
  rating: number,
  comment: string,
) {
  const res = await fetch(`${API_URL}/danh-gia/${documentId}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ rating, comment }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi đánh giá thất bại");
  return data;
}
