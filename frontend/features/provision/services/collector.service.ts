import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function triggerCollectionAPI(source: string, pages: number) {
  const res = await fetch(`${API_URL}/collect/noi-bo/kich-hoat`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ source, pages }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể kích hoạt tiến trình thu thập");
  return data;
}

export async function stopCollectionAPI() {
  const res = await fetch(`${API_URL}/collect/dung`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể dừng tiến trình thu thập");
  return data;
}

export async function getCollectorStatsAPI() {
  const res = await fetch(`${API_URL}/collect/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải trạng thái thu thập");
  return data;
}

export async function getCollectorLogsAPI() {
  const res = await fetch(`${API_URL}/collect/logs`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải log tiến trình");
  return data;
}
