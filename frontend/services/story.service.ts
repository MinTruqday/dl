import { API_URL, getAuthHeaders } from "./authentication.service";

export async function getStoriesAPI() {
  const res = await fetch(`${API_URL}/cau-chuyen`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tin mới");
  return data;
}

export async function createStoryAPI(payload: any) {
  const res = await fetch(`${API_URL}/cau-chuyen`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo tin thất bại");
  return data;
}

export async function getMyStoriesAPI() {
  const res = await fetch(`${API_URL}/cau-chuyen/ca-nhan`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách tin của bạn");
  return data;
}

export async function getArchivedStoriesAPI() {
  const res = await fetch(`${API_URL}/cau-chuyen/ca-nhan/luu-tru`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải kho lưu trữ tin");
  return data;
}

export async function viewStoryAPI(storyId: string) {
  const res = await fetch(`${API_URL}/cau-chuyen/${storyId}/xem`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Ghi nhận lượt xem thất bại");
  return data;
}

export async function getStoryViewersAPI(storyId: string) {
  const res = await fetch(`${API_URL}/cau-chuyen/${storyId}/nguoi-xem`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách người xem");
  return data;
}

export async function reactToStoryAPI(
  storyId: string,
  reactionType: string = "heart",
) {
  const res = await fetch(
    `${API_URL}/cau-chuyen/${storyId}/cam-xuc?reaction_type=${reactionType}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Phản hồi tin thất bại");
  return data;
}

export async function voteStoryPollAPI(storyId: string, optionIdx: number) {
  const res = await fetch(
    `${API_URL}/cau-chuyen/${storyId}/khao-sat/binh-chon?option_index=${optionIdx}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bình chọn thất bại");
  return data;
}

export async function answerStoryQuizAPI(storyId: string, optionIdx: number) {
  const res = await fetch(
    `${API_URL}/cau-chuyen/${storyId}/do-vui/tra-loi?option_index=${optionIdx}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Trả lời câu đố thất bại");
  return data;
}

export async function replyStoryAPI(storyId: string, message: string) {
  const res = await fetch(
    `${API_URL}/cau-chuyen/${storyId}/phan-hoi?message=${encodeURIComponent(message)}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi trả lời thất bại");
  return data;
}

export async function archiveStoryAPI(storyId: string) {
  const res = await fetch(`${API_URL}/cau-chuyen/${storyId}/luu-tru`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lưu trữ tin thất bại");
  return data;
}

export async function deleteStoryAPI(storyId: string) {
  const res = await fetch(`${API_URL}/cau-chuyen/${storyId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa tin thất bại");
  return data;
}
