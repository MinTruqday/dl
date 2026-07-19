import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export const getConversationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/cuoc-tro-chuyen`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy xuất bộ sưu tập luồng hội thoại");
  return data;
};

export const getMessagesAPI = async (
  otherUserId: string,
  limit: number = 50,
  cursor?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  let url = `${API_URL}/tin-nhan/${otherUserId}?limit=${limit}`;
  if (cursor) {
    url += `&cursor=${cursor}`;
  }
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy xuất dữ liệu lịch sử hội thoại");
  return data;
};

export const sendMessageAPI = async (
  receiverId: string,
  content: string,
  imageUrl?: string,
  replyToId?: string,
  audioUrl?: string,
  selfDestructIn?: number,
  documentUrl?: string,
  documentName?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/`, {
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
      self_destruct_in: selfDestructIn,
      attachments: documentUrl ? [{ url: documentUrl, name: documentName }] : [],
      client_msg_id: crypto.randomUUID(),
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi luồng chuyển tiếp dữ liệu thông điệp");
  return data;
};

export const togglePinAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/ghim`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật trạng thái dữ liệu ghim");
  return data;
};

export const editMessageAPI = async (messageId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/chinh-sua`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật cấu trúc dữ liệu thông điệp");
  return data;
};

export const recallMessageAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi hoàn tác trạng thái dữ liệu thông điệp");
  return data;
};

export const deleteMessageForMeAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/xoa-phia-toi`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa bỏ bản ghi dữ liệu cục bộ");
  return data;
};

export const restoreMessageAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi phục hồi bản ghi dữ liệu thông điệp");
  return data;
};

export const searchMessagesAPI = async (otherUserId: string, q: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tim-kiem?q=${encodeURIComponent(q)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy vấn cơ sở dữ liệu thông điệp");
  return data;
};

export const addReactionAPI = async (messageId: string, reaction: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/bay-to-cam-xuc`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reaction }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi cập nhật trường dữ liệu tương tác biểu tượng");
  return data;
};

export const markAsReadAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/doc-hieu`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật trạng thái đọc của người dùng");
  return data;
};

export const shareDocumentAPI = async (
  receiverId: string,
  documentId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/${receiverId}/tai-lieu/chia-se`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ document_id: documentId }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thiết lập quyền truy cập tài liệu liên kết");
  return data;
};

export const getSharedAttachmentsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tai-lieu/da-chia-se`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy xuất danh sách tập tin đính kèm chia sẻ");
  return data;
};

export const blockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/chan`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thiết lập quy tắc hạn chế người dùng");
  return data;
};

export const unblockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/bo-chan`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa bỏ quy tắc hạn chế người dùng");
  return data;
};

export const getBlockedStatusAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/trang-thai-chan`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy xuất trạng thái quy tắc hạn chế");
  return data;
};

export const togglePinConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/cuoc-tro-chuyen/${otherUserId}/ghim`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật trạng thái ghim luồng hội thoại");
  return data;
};

export const translateMessageAPI = async (
  messageId: string,
  targetLang: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/dich-thuat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thực thi luồng phiên dịch thông điệp");
  return data;
};

export const createGroupAPI = async (
  groupName: string,
  memberIds: string[],
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/nhom`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ group_name: groupName, member_ids: memberIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo luồng hội thoại nhóm");
  return data;
};

export const addGroupMemberAPI = async (groupId: string, userId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/thanh-vien`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ user_id: userId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật danh sách thành viên nhóm");
  return data;
};

export const removeGroupMemberAPI = async (groupId: string, userId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/thanh-vien/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa thành viên khỏi nhóm");
  return data;
};

export const updateGroupInfoAPI = async (groupId: string, groupName: string, avatarUrl: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/thong-tin`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ group_name: groupName, avatar_url: avatarUrl }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật thông tin nhóm");
  return data;
};

export const forwardMessageAPI = async (messageId: string, receiverIds: string[]) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/chuyen-tiep`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message_id: messageId, receiver_ids: receiverIds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi chuyển tiếp tin nhắn");
  return data;
};

export const createPollAPI = async (receiverId: string, question: string, options: string[]) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/binh-chon`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ receiver_id: receiverId, question, options }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tạo bình chọn");
  return data;
};

export const votePollAPI = async (messageId: string, optionId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/binh-chon/${messageId}/bo-phieu`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ option_id: optionId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi bỏ phiếu");
  return data;
};

export const saveDraftAPI = async (otherUserId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/ban-nhap`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi lưu trữ dữ liệu thông điệp tạm thời");
  return data;
};

export const getDraftAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/ban-nhap`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy xuất bản ghi thông điệp tạm thời");
  return data;
};

export const toggleSelfDestructAPI = async (
  otherUserId: string,
  seconds: number,
) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tu-huy`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ seconds }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thiết lập bộ đếm vòng đời thông điệp");
  return data;
};

export const toggleMuteAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tat-thong-bao`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi thay đổi trạng thái cấu hình thông báo luồng");
  return data;
};

export const getConversationSettingsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi truy xuất bộ thông số cấu hình luồng");
  return data;
};

export const updateConversationSettingsAPI = async (otherUserId: string, updates: any) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/cai-dat`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật cấu hình cuộc trò chuyện");
  return data;
};

export const deleteConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Lỗi thiếu hụt phiên xác thực người dùng hợp lệ");
  const res = await fetch(
    `${API_URL}/tin-nhan/cuoc-tro-chuyen/${otherUserId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa bỏ toàn bộ dữ liệu luồng hội thoại");
  return data;
};
