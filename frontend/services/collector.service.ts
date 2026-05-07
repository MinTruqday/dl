import { API_URL, getAuthHeaders } from "./authentication.service";

export async function triggerCollectionAPI(
  source: string,
  url: string,
  index_type: string,
  target_class: string,
) {
  const res = await fetch(`${API_URL}/thu-thap/kich-hoat`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ source, url, index_type, target_class }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể kích hoạt tiến trình thu thập");
  return data;
}

export async function getCollectorStatsAPI() {
  const res = await fetch(`${API_URL}/thu-thap/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải trạng thái thu thập");
  return data;
}
