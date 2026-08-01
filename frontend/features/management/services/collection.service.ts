import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function triggerCollectionAPI(source: string, pages: number | string) {
  const res = await fetch(`${API_URL}/thu-thap/kich-hoat`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ source, pages }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi khởi chạy tiến trình thu thập dữ liệu");
  return data;
}

export async function stopCollectionAPI() {
  const res = await fetch(`${API_URL}/thu-thap/tam-dung`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi tạm ngưng tiến trình thu thập dữ liệu");
  return data;
}

export async function getCollectorStatsAPI() {
  const res = await fetch(`${API_URL}/thu-thap/thong-ke`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải trạng thái luồng dữ liệu thu thập");
  return data;
}

export async function getCollectorLogsAPI() {
  const res = await fetch(`${API_URL}/thu-thap/nhat-ky`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải nhật ký tiến trình thu thập");
  return data;
}
