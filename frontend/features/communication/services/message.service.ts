import { API_URL, getToken } from "@/features/auth/services/authentication.service";

export const getConversationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/conversation`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách hội thoại");
  return data;
};

export const getMessagesAPI = async (
  otherUserId: string,
  limit: number = 50,
  cursor?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  let url = `${API_URL}/message/message/${otherUserId}?limit=${limit}`;
  if (cursor) {
    url += `&cursor=${cursor}`;
  }
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử tin nhắn");
  return data;
};

export const sendMessageAPI = async (
  receiverId: string,
  content: string,
  imageUrl?: string,
  replyToId?: string,
  audioUrl?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      receiver_id: receiverId,
      content,
      image_url: imageUrl,
      audio_url: audioUrl,
      reply_to_id: replyToId,
      client_msg_id: crypto.randomUUID(),
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Gửi tin nhắn thất bại");
  return data;
};

export const togglePinAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/highlight/${messageId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể thực hiện ghim");
  return data;
};

export const editMessageAPI = async (messageId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/edit/${messageId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể chỉnh sửa tin nhắn");
  return data;
};

export const recallMessageAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/message/${messageId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể thu hồi tin nhắn");
  return data;
};

export const searchMessagesAPI = async (otherUserId: string, q: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/message/search/${otherUserId}?q=${encodeURIComponent(q)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tìm kiếm tin nhắn");
  return data;
};

export const addReactionAPI = async (messageId: string, reaction: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/message/${messageId}/reaction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reaction }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể thực hiện bày tỏ cảm xúc");
  return data;
};

export const markAsReadAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/read-message/${otherUserId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể đánh dấu đã xem");
  return data;
};

export const shareDocumentAPI = async (
  receiverId: string,
  documentId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/share-document/${receiverId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ document_id: documentId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chia sẻ tài liệu thất bại");
  return data;
};

export const getSharedAttachmentsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/message/tai-lieu-share/${otherUserId}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải tệp tin chia sẻ");
  return data;
};

export const blockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/block/${otherUserId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Chặn người dùng thất bại");
  return data;
};

export const unblockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/unblock/${otherUserId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Bỏ chặn thất bại");
  return data;
};

export const getBlockedStatusAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/block-status/${otherUserId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tải trạng thái chặn");
  return data;
};

export const togglePinConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/ghim-conversation/${otherUserId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể ghim hội thoại");
  return data;
};

export const translateMessageAPI = async (
  messageId: string,
  targetLang: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/translate/${messageId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi dịch tin nhắn");
  return data;
};

export const createGroupAPI = async (
  groupName: string,
  memberIds: string[],
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/group`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ group_name: groupName, member_ids: memberIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo nhóm thất bại");
  return data;
};

export const saveDraftAPI = async (otherUserId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/type-message/${otherUserId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lưu tin nhắn nháp thất bại");
  return data;
};

export const getDraftAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/type-message/${otherUserId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tải tin nhắn nháp thất bại");
  return data;
};

export const toggleSelfDestructAPI = async (
  otherUserId: string,
  seconds: number,
) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/self-destruct/${otherUserId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ seconds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Cập nhật tự hủy thất bại");
  return data;
};

export const toggleMuteAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/mute/${otherUserId}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tắt âm hội thoại thất bại");
  return data;
};

export const getConversationSettingsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/settings/${otherUserId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lấy cài đặt thất bại");
  return data;
};
export const deleteConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/message/conversation/${otherUserId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Xóa cuộc hội thoại thất bại");
  return data;
};
