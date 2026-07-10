import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function publishDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi chạy tiến trình xuất bản");
  return data;
}

export async function schedulePublishAPI(
  documentId: string,
  publishAt: string,
) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}/len-lich`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ publish_at: publishAt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cấu hình lịch trình xuất bản");
  return data;
}

export async function configPremiumAPI(
  documentId: string,
  premiumChapters: string[],
) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}/dinh-gia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ premium_chapters: premiumChapters }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi thiết lập cơ chế kiểm soát truy cập thu phí");
  return data;
}

export async function setFreePreviewAPI(
  documentId: string,
  chapterIds: string[],
) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}/xem-truoc`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(chapterIds),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi cấp quyền truy cập công khai cục bộ");
  return data;
}

export async function updateSeoMetadataAPI(
  documentId: string,
  metadata: {
    tags?: string[];
    keywords?: string[];
    slug?: string;
    description?: string;
  },
) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}/seo`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(metadata),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi cập nhật cấu trúc siêu dữ liệu tối ưu hóa tìm kiếm (SEO)");
  return data;
}

export async function getReadabilityScoreAPI(documentId: string) {
  const res = await fetch(`${API_URL}/xuat-ban/${documentId}/doc-hieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất chỉ số đo lường khả năng đọc hiểu");
  return data;
}
