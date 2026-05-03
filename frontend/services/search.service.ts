import { API_URL, getToken } from "./auth.service";

export async function semanticSearchAPI(query: string) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để sử dụng tính năng này.");
  const res = await fetch(
    `${API_URL}/ai/search?q=${encodeURIComponent(query)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) throw new Error("Hệ thống AI đang bận, vui lòng thử lại sau.");
  return await res.json();
}
