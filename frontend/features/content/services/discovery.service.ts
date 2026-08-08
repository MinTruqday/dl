import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export const getTagsCategoriesAPI = async () => {
  const res = await fetch(`${API_URL}/kham-pha/the-loai`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải cây cấu trúc thẻ và danh mục",
    );
  return data;
};

export const smartSearchAPI = async (query: string, limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/tim-kiem/thong-minh?q=${encodeURIComponent(query)}&limit=${limit}`,
    { headers: getAuthHeaders() },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thực hiện truy vấn tìm kiếm ngữ nghĩa",
    );
  return data;
};

export const getPersonalizedRecommendationsAPI = async (limit: number = 10) => {
  const res = await fetch(`${API_URL}/kham-pha/goi-y-ca-nhan?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải bộ dữ liệu khuyến nghị cá nhân hóa",
    );
  return data;
};
