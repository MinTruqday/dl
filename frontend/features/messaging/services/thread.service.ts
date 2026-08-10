import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export const getConversationsAPI = async () => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/cuoc-tro-chuyen`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải bộ sưu tập luồng hội thoại");
  return data;
};

export const getMessagesAPI = async (
  otherUserId: string,
  limit: number = 50,
  cursor?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  let url = `${API_URL}/tin-nhan/${otherUserId}?limit=${limit}`;
  if (cursor) {
    url += `&cursor=${cursor}`;
  }
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải dữ liệu lịch sử hội thoại");
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
  parentMessageId?: string,
  scheduledAt?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
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
      attachments: documentUrl
        ? [{ url: documentUrl, name: documentName }]
        : [],
      parent_message_id: parentMessageId,
      scheduled_at: scheduledAt,
      client_msg_id: crypto.randomUUID(),
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message ||
        "Không thể thực hiện luồng chuyển tiếp dữ liệu thông điệp",
    );
  return data;
};

export const editMessageAPI = async (messageId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật cấu trúc dữ liệu thông điệp",
    );
  return data;
};

export const recallMessageAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể hoàn tác trạng thái dữ liệu thông điệp",
    );
  return data;
};

export const deleteMessageForMeAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/xoa-phia-toi`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể xóa bản ghi dữ liệu cục bộ");
  return data;
};

export const restoreMessageAPI = async (messageId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/khoi-phuc`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể khôi phục bản ghi dữ liệu thông điệp",
    );
  return data;
};

export const saveToCloudAPI = async (
  messageId: string,
  content: string,
  attachments: any[] = [],
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/cloud/luu-tin-nhan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message_id: messageId, content, attachments }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi lưu tin nhắn vào kho cá nhân");
  return data;
};

export const updateThemeAPI = async (otherUserId: string, themeId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/chu-de`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ theme_id: themeId }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật chủ đề cuộc trò chuyện",
    );
  return data;
};

export const createAnnouncementAPI = async (
  groupId: string,
  title: string,
  body: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/thong-bao`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title, body }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi đăng thông báo nhóm");
  return data;
};

export const generateGroupInviteAPI = async (groupId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/link-moi`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi tạo đường dẫn mời tham gia nhóm");
  return data;
};

export const joinByInviteAPI = async (inviteCode: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/tham-gia`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ invite_code: inviteCode }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi gia nhập nhóm trò chuyện");
  return data;
};

export const setNicknameAPI = async (otherUserId: string, nickname: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/biet-danh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ nickname }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể cập nhật biệt danh");
  return data;
};

export const shareContactCardAPI = async (
  otherUserId: string,
  contactUserId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/danh-thiep`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ contact_user_id: contactUserId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi chia sẻ thẻ danh thiếp");
  return data;
};

export const archiveThreadAPI = async (
  otherUserId: string,
  isArchived: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/luu-tru`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_archived: isArchived }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật trạng thái lưu trữ cuộc trò chuyện",
    );
  return data;
};

export const setPinLockAPI = async (otherUserId: string, pinCode: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/an-tin-nhan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pin_code: pinCode }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi đặt mã PIN ẩn cuộc trò chuyện");
  return data;
};

export const setMessageAlarmAPI = async (
  messageId: string,
  remindAt: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/nhac-hen`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ remind_at: remindAt }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi đặt lịch nhắc hẹn tin nhắn");
  return data;
};

export const transferGroupOwnershipAPI = async (
  groupId: string,
  newLeaderId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/chuyen-truong-nhom`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ new_leader_id: newLeaderId }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi chuyển giao quyền Trưởng nhóm");
  return data;
};

export const setGroupSlowModeAPI = async (
  groupId: string,
  delaySeconds: number,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/che-do-cham`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ delay_seconds: delaySeconds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật chế độ tin nhắn chậm");
  return data;
};

export const exportChatHistoryAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/xuat-lich-su`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải lịch sử trò chuyện");
  return data;
};

export const setAutoReplyAPI = async (
  autoReplyText: string,
  isEnabled: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/ca-nhan/tra-loi-tu-dong`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      auto_reply_text: autoReplyText,
      is_enabled: isEnabled,
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình tin nhắn tự động");
  return data;
};

export const manageGroupPermissionsAPI = async (
  groupId: string,
  adminOnly: boolean,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/quyen-gui-tin-nhan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ admin_only: adminOnly }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi phân quyền gửi tin nhắn nhóm");
  return data;
};

export const createGroupEventAPI = async (
  groupId: string,
  title: string,
  eventTime: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${groupId}/su-kien`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title, event_time: eventTime }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tạo sự kiện nhóm");
  return data;
};

export const setVipPriorityAPI = async (
  otherUserId: string,
  isVip: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/uu-tien-vip`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_vip: isVip }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật thẻ ưu tiên VIP");
  return data;
};

export const setAutoCleanScheduleAPI = async (
  otherUserId: string,
  days: number = 30,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/xoa-dinh-ky`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ days }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình lịch xóa định kỳ");
  return data;
};

export const snoozeNotificationsAPI = async (
  otherUserId: string,
  minutes: number = 60,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tam-tat-thong-bao`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ minutes }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tắt thông báo tạm thời");
  return data;
};

export const getMediaVaultAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/kho-phuong-tien`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải kho phương tiện & tệp");
  return data;
};

export const clearChatStorageAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/don-dung-luong`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi dọn dẹp dung lượng trò chuyện");
  return data;
};

export const setDeputyAdminAPI = async (
  groupId: string,
  deputyUserId: string,
  isDeputy: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/pho-nhom`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ deputy_user_id: deputyUserId, is_deputy: isDeputy }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi phân quyền Phó nhóm");
  return data;
};

export const setGroupRulesAPI = async (groupId: string, rules: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/noi-quy`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ rules }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể thiết lập Nội quy nhóm");
  return data;
};

export const getGroupActivityLogAPI = async (groupId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/nhat-ky`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải nhật ký hoạt động nhóm");
  return data;
};

export const setQuietHoursAPI = async (
  startHour: number = 22,
  endHour: number = 7,
  isEnabled: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/ca-nhan/khung-gio-yen-tinh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      start_hour: startHour,
      end_hour: endHour,
      is_enabled: isEnabled,
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình khung giờ yên tĩnh");
  return data;
};

export const setAutoTranslateAPI = async (
  targetLang: string = "vi",
  isEnabled: boolean = true,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/ca-nhan/tu-dong-dich`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_lang: targetLang, is_enabled: isEnabled }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình tự động dịch tin nhắn");
  return data;
};

export const searchMessagesAPI = async (otherUserId: string, q: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tim-kiem?q=${encodeURIComponent(q)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi truy vấn cơ sở dữ liệu thông điệp");
  return data;
};

export const globalSearchAPI = async (q: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/tim-kiem-toan-cuc?q=${encodeURIComponent(q)}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi tìm kiếm toàn cục");
  return data;
};

export const addReactionAPI = async (messageId: string, reaction: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
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
    throw new Error(
      data.message || "Không thể cập nhật trường dữ liệu tương tác biểu tượng",
    );
  return data;
};

export const markAsReadAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/doc-hieu`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật trạng thái đọc của người dùng",
    );
  return data;
};

export const shareDocumentAPI = async (
  receiverId: string,
  documentId: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
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
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thiết lập quyền truy cập tài liệu liên kết",
    );
  return data;
};

export const getSharedAttachmentsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/tai-lieu/da-chia-se`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải danh sách tập tin đính kèm chia sẻ",
    );
  return data;
};

export const blockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/chan`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thiết lập quy tắc hạn chế người dùng",
    );
  return data;
};

export const unblockUserAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/bo-chan`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể xóa quy tắc hạn chế người dùng");
  return data;
};

export const getBlockedStatusAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/trang-thai-chan`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải trạng thái quy tắc hạn chế");
  return data;
};

export const translateMessageAPI = async (
  messageId: string,
  targetLang: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${messageId}/dich-thuat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thực hiện luồng phiên dịch thông điệp",
    );
  return data;
};

export const createGroupAPI = async (
  groupName: string,
  memberIds: string[],
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ group_name: groupName, member_ids: memberIds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo luồng hội thoại nhóm");
  return data;
};

export const addGroupMemberAPI = async (groupId: string, userId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/thanh-vien`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ user_id: userId }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật danh sách thành viên nhóm",
    );
  return data;
};

export const removeGroupMemberAPI = async (
  groupId: string,
  userId: string,
  silent: boolean = false,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/nhom/${groupId}/thanh-vien/${userId}?silent=${silent}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi xóa thành viên khỏi nhóm");
  return data;
};

export const updateGroupSettingsAPI = async (groupId: string, updates: any) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/cai-dat`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật thiết lập nhóm");
  return data;
};

export const updateGroupInfoAPI = async (
  groupId: string,
  groupName: string,
  avatarUrl: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/nhom/${groupId}/thong-tin`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ group_name: groupName, avatar_url: avatarUrl }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật thông tin nhóm");
  return data;
};

export const forwardMessageAPI = async (
  messageId: string,
  receiverIds: string[],
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
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

export const createPollAPI = async (
  receiverId: string,
  question: string,
  options: string[],
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
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
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/binh-chon/${messageId}/bo-phieu`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ option_id: optionId }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi bỏ phiếu");
  return data;
};

export const saveDraftAPI = async (otherUserId: string, content: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/ban-nhap`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể lưu dữ liệu thông điệp tạm thời",
    );
  return data;
};

export const getDraftAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/ban-nhap`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải bản ghi thông điệp tạm thời",
    );
  return data;
};

export const toggleSelfDestructAPI = async (
  otherUserId: string,
  seconds: number,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tu-huy`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ seconds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể thiết lập bộ đếm vòng đời thông điệp",
    );
  return data;
};

export const toggleMuteAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tat-thong-bao`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi thay đổi trạng thái cấu hình thông báo luồng",
    );
  return data;
};

export const getConversationSettingsAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải bộ thông số cấu hình luồng");
  return data;
};

export const updateConversationSettingsAPI = async (
  otherUserId: string,
  updates: any,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/cai-dat`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể cập nhật cấu hình cuộc trò chuyện",
    );
  return data;
};

export const deleteConversationAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/cuoc-tro-chuyen/${otherUserId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể xóa toàn bộ dữ liệu luồng hội thoại",
    );
  return data;
};

export const getThreadRepliesAPI = async (
  messageId: string,
  limit: number = 50,
  cursor?: string,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  let url = `${API_URL}/tin-nhan/${messageId}/thread?limit=${limit}`;
  if (cursor) {
    url += `&cursor=${cursor}`;
  }
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải luồng tin nhắn phụ");
  return data;
};

export const getQuickRepliesAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/goi-y-tra-loi`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi tạo gợi ý trả lời thông minh");
  return data;
};

export const markUnreadAPI = async (otherUserId: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(
    `${API_URL}/tin-nhan/${otherUserId}/danh-dau-chua-doc`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi đánh dấu chưa đọc cuộc trò chuyện");
  return data;
};

export const setDisappearingTimerAPI = async (
  otherUserId: string,
  timerSeconds: number,
) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/tu-xoa`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ timer_seconds: timerSeconds }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cấu hình tự xóa tin nhắn");
  return data;
};
