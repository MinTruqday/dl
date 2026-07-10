import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export const getTagsCategoriesAPI = async () => {
  const res = await fetch(`${API_URL}/kham-pha/the-loai`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất cây cấu trúc thẻ và danh mục");
  return data;
};

export const smartSearchAPI = async (query: string, limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/kham-pha/tim-kiem-thong-minh?query=${encodeURIComponent(query)}&limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi truy vấn tìm kiếm ngữ nghĩa");
  return data;
};

export const getAIRecommendationsAPI = async (limit: number = 10) => {
  const res = await fetch(`${API_URL}/kham-pha/goi-y-ai?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy xuất bộ dữ liệu khuyến nghị cá nhân hóa");
  return data;
};

