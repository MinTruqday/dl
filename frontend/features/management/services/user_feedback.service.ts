import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

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
    throw new Error(data.message || "Lỗi khởi tạo yêu cầu báo cáo vi phạm");
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
    throw new Error(data.message || "Lỗi ghi nhận báo cáo lỗi chính tả");
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
    throw new Error(data.message || "Lỗi trích xuất danh sách báo cáo lỗi");
  return data;
}
