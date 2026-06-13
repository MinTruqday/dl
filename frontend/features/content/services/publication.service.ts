import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function publishDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/publication/${documentId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xuất bản tài liệu thất bại");
  return data;
}

export async function schedulePublishAPI(
  documentId: string,
  publishAt: string,
) {
  const res = await fetch(`${API_URL}/publication/${documentId}/len-lich`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ publish_at: publishAt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lên lịch xuất bản thất bại");
  return data;
}

export async function configPremiumAPI(
  documentId: string,
  premiumChapters: string[],
) {
  const res = await fetch(`${API_URL}/publication/${documentId}/tinh-phi`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ premium_chapters: premiumChapters }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Thiết lập chương tính phí thất bại");
  return data;
}

export async function setFreePreviewAPI(
  documentId: string,
  chapterIds: string[],
) {
  const res = await fetch(`${API_URL}/publication/${documentId}/doc-thu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(chapterIds),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Thiết lập chương đọc thử thất bại");
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
  const res = await fetch(`${API_URL}/publication/${documentId}/seo`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(metadata),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Cập nhật thông tin SEO thất bại");
  return data;
}

export async function getReadabilityScoreAPI(documentId: string) {
  const res = await fetch(`${API_URL}/publication/${documentId}/doc-hieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể lấy điểm độ đọc hiểu");
  return data;
}
