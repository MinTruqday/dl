import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function submitReportAPI(payload: {
  item_type: string;
  item_id: string;
  reason: string;
  description?: string;
}) {
  const res = await fetch(`${API_URL}/feedback/report`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Gửi báo cáo nội dung vi phạm thất bại");
  return data;
}

export async function rateDocumentAPI(
  documentId: string,
  rating: number,
  reviewText?: string,
) {
  const res = await fetch(`${API_URL}/feedback/document/${documentId}/review`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ rating, review_text: reviewText }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đánh giá tài liệu thất bại");
  return data;
}

export async function rateChapterAPI(
  documentId: string,
  chapterSlug: string,
  rating: number,
) {
  const res = await fetch(
    `${API_URL}/feedback/document/${documentId}/chapter/review`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ chapter_slug: chapterSlug, rating }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Đánh giá chương thất bại");
  return data;
}

export async function reportTypoAPI(
  documentId: string,
  payload: {
    chapter_slug: string;
    text_excerpt: string;
    description?: string;
  },
) {
  const res = await fetch(
    `${API_URL}/feedback/document/${documentId}/loi-chinh-ta`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Gửi báo cáo lỗi chính tả thất bại");
  return data;
}

export async function getTypoReportsAPI(documentId: string) {
  const res = await fetch(
    `${API_URL}/feedback/document/${documentId}/loi-chinh-ta`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách báo cáo lỗi");
  return data;
}
