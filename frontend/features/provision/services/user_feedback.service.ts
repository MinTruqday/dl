import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function submitReportAPI(payload: {
  item_type: string;
  item_id: string;
  reason: string;
  description?: string;
}) {
  const res = await fetch(`${API_URL}/phan-hoi/bao-cao`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Gửi báo cáo nội dung vi phạm thất bại");
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
    `${API_URL}/phan-hoi/tai-lieu/${documentId}/loi-chinh-ta`,
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
    `${API_URL}/phan-hoi/tai-lieu/${documentId}/loi-chinh-ta`,
    {
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách báo cáo lỗi");
  return data;
}
