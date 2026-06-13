import { API_URL, getAuthHeaders } from "./authentication.service";

export const getTrendingDocumentsAPI = async (limit: number = 5) => {
  const res = await fetch(`${API_URL}/discovery/xu-huong?limit=${limit}`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tài liệu xu hướng",
    );
  return data;
};

export const getTagsCategoriesAPI = async () => {
  const res = await fetch(`${API_URL}/discovery/the-va-danh-muc`);
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách thẻ và danh mục");
  return data;
};

export const smartSearchAPI = async (query: string, limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/discovery/tim-kiem-thong-minh?query=${encodeURIComponent(query)}&limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm kiếm thông minh thất bại");
  return data;
};

export const getAIRecommendationsAPI = async (limit: number = 10) => {
  const res = await fetch(`${API_URL}/discovery/goi-y/ai?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải gợi ý tài liệu từ AI");
  return data;
};

export const getTrendingTagsAPI = async (limit: number = 10) => {
  const res = await fetch(
    `${API_URL}/discovery/hashtag-xu-huong?limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách hashtag xu hướng");
  return data;
};
