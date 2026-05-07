import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getFeedAPI(
  tab: string,
  skip: number,
  limit: number,
  itemType?: string,
  sort?: string,
) {
  let url = `${API_URL}/cong-dong/bang-tin?tab=${tab}&skip=${skip}&limit=${limit}`;
  if (itemType) url += `&item_type=${itemType}`;
  if (sort) url += `&sort=${sort}`;
  
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải bảng tin");
  return data;
}

export async function getTrendingTagsAPI() {
  const res = await fetch(`${API_URL}/cong-dong/hashtag-xu-huong`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải xu hướng");
  return data;
}

export async function getSuggestedDocumentsAPI() {
  const res = await fetch(`${API_URL}/cong-dong/goi-y-tai-lieu`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải gợi ý tài liệu");
  return data;
}

export async function getIntersectionFriendsAPI() {
  const res = await fetch(`${API_URL}/cong-dong/goi-y-ket-noi`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải gợi ý kết nối");
  return data;
}

export async function getFeaturedAuthorsAPI(limit: number = 5) {
  const res = await fetch(`${API_URL}/cong-dong/tac-gia-noi-bat?limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách tác giả");
  return data;
}

export async function getSavedPostsAPI(skip: number = 0, limit: number = 20) {
  const res = await fetch(`${API_URL}/cong-dong/bai-viet-da-luu?skip=${skip}&limit=${limit}`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách bài viết đã lưu");
  return data;
}
