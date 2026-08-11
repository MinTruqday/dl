"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  WS_URL,
  getToken,
} from "@/shared/services/api-client";
import {
  getChatAttachmentBlobUrlAPI,
  uploadChatAttachmentAPI,
} from "@/features/cloud/services/upload.service";
import { searchUsersAPI } from "@/features/humanity/services/user.service";
import {
  blockUserAPI,
  addReactionAPI,
  createPollAPI,
  createGroupAPI,
  deleteConversationAPI,
  editMessageAPI,
  getBlockedStatusAPI,
  getConversationsAPI,
  getDraftAPI,
  getConversationSettingsAPI,
  getMediaVaultAPI,
  getMessagesAPI,
  markAsReadAPI,
  recallMessageAPI,
  saveToCloudAPI,
  saveDraftAPI,
  searchMessagesAPI,
  sendMessageAPI,
  toggleMuteAPI,
  toggleSelfDestructAPI,
  translateMessageAPI,
  unblockUserAPI,
  votePollAPI,
} from "@/features/messaging/services/thread.service";
import {
  getPinnedMessagesAPI,
  togglePinAPI,
} from "@/features/messaging/services/pin.service";

export function conversationId(conversation: any) {
  return (
    conversation?.other_user_id ?? conversation?._id ?? conversation?.id ?? ""
  );
}
export function conversationName(conversation: any) {
  return (
    conversation?.group_name ??
    conversation?.name ??
    conversation?.other_user?.full_name ??
    conversation?.other_user?.username ??
    conversation?.other_user_email ??
    "Cuộc trò chuyện"
  );
}

export function isGroupConversation(conversation: any) {
  return (
    conversationId(conversation).startsWith("group_") ||
    conversation?.other_user?.is_group === true
  );
}

export function canBlockConversation(conversation: any) {
  return Boolean(
    conversation &&
      !isGroupConversation(conversation) &&
      conversation?.other_user_id &&
      conversation?.other_user?.username &&
      !conversation?.is_system &&
      !conversation?.other_user?.is_system,
  );
}

export function conversationPreview(conversation: any) {
  const last = conversation?.last_message;
  if (!last) return "Chưa có tin nhắn";
  if (last.is_recalled) return "Tin nhắn đã thu hồi";
  if (last.audio_url) return "Tin nhắn thoại";
  if (last.image_url) return "Hình ảnh";
  if (last.attachments?.length) {
    const attachment = last.attachments[0];
    const type = String(attachment?.type ?? attachment?.content_type ?? "");
    if (type.startsWith("video/")) return "Video";
    return attachment?.name ?? "Tệp đính kèm";
  }
  try {
    const parsed = JSON.parse(last.content ?? "");
    if (parsed?.type === "poll")
      return `Bình chọn: ${parsed.data?.question ?? parsed.question ?? ""}`;
  } catch {}
  return last.content || "Chưa có tin nhắn";
}

async function hydrateMessageAssets(messages: any[]) {
  return Promise.all(
    messages.map(async (message) => {
      const next = { ...message };
      if (message.image_url)
        next.display_image_url = await getChatAttachmentBlobUrlAPI(message.image_url).catch(() => message.image_url);
      if (message.audio_url)
        next.display_audio_url = await getChatAttachmentBlobUrlAPI(message.audio_url).catch(() => message.audio_url);
      next.attachments = await Promise.all(
        (message.attachments ?? []).map(async (attachment: any) => ({
          ...attachment,
          display_url: await getChatAttachmentBlobUrlAPI(attachment.url ?? attachment.file_url).catch(() => attachment.url ?? attachment.file_url),
        })),
      );
      return next;
    }),
  );
}

function sortMessages(messages: any[]) {
  return [...messages].sort((left, right) => {
    const leftTime = new Date(left.created_at ?? left.timestamp ?? 0).getTime();
    const rightTime = new Date(right.created_at ?? right.timestamp ?? 0).getTime();
    return leftTime - rightTime;
  });
}

export function useMessages() {
  const { user, isLoading: authLoading } = useAuth();
  const [conversations, setConversations] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const selectedRef = useRef<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [pinnedMessages, setPinnedMessages] = useState<any[]>([]);
  const [draft, setDraft] = useState("");
  const [blocked, setBlocked] = useState(false);
  const [muted, setMuted] = useState(false);
  const [settings, setSettings] = useState<any>({});
  const [media, setMedia] = useState<any[]>([]);
  const [loadingMedia, setLoadingMedia] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const reloadConversations = useCallback(async () => {
    if (!user) return setLoading(false);
    try {
      const response = await getConversationsAPI();
      const rows = response.data ?? response ?? [];
      setConversations(
        rows.filter(
          (row: any, index: number) =>
            rows.findIndex(
              (candidate: any) =>
                conversationId(candidate) === conversationId(row) &&
                conversationName(candidate) === conversationName(row),
            ) === index,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải cuộc trò chuyện",
      );
    } finally {
      setLoading(false);
    }
  }, [user]);
  useEffect(() => void reloadConversations(), [reloadConversations]);
  useEffect(() => {
    selectedRef.current = selected;
  }, [selected]);
  useEffect(() => {
    if (!user?._id || !WS_URL) return;
    const token = getToken();
    if (!token) return;
    const socket = new WebSocket(`${WS_URL}/ws/${user._id}`, ["doclib", token]);
    socket.onmessage = (event) => {
      try {
        const packet = JSON.parse(event.data);
        const message = packet.data;
        if (
          packet.type === "new_message" &&
          selectedRef.current &&
          message.sender_id === conversationId(selectedRef.current)
        )
          setMessages((rows) =>
            rows.some(
              (item) => (item._id ?? item.id) === (message._id ?? message.id),
            )
              ? rows
              : [...rows, message],
          );
        if (
          [
            "message_edited",
            "message_pinned",
            "message_recalled",
            "message_reaction",
          ].includes(
            packet.type,
          )
        )
          setMessages((rows) =>
            rows.map((item) =>
              (item._id ?? item.id) === (message._id ?? message.id)
                ? message
                : item,
            ),
          );
        void reloadConversations();
      } catch {
        return;
      }
    };
    const timer = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN)
        socket.send(JSON.stringify({ action: "ping" }));
    }, 30000);
    return () => {
      window.clearInterval(timer);
      socket.close();
    };
  }, [user?._id, reloadConversations]);
  useEffect(() => {
    if (!selected) return;
    const timer = window.setTimeout(
      () =>
        void saveDraftAPI(conversationId(selected), draft).catch(
          () => undefined,
        ),
      800,
    );
    return () => window.clearTimeout(timer);
  }, [selected, draft]);

  const open = async (conversation: any) => {
    setSelected(conversation);
    setLoadingMessages(true);
    setError("");
    try {
      const id = conversationId(conversation);
      const blockRequest = canBlockConversation(conversation)
        ? getBlockedStatusAPI(id).catch(() => ({ data: { is_blocked: false } }))
        : Promise.resolve({ data: { is_blocked: false } });
      const [messageResponse, pinnedResponse, draftResponse, blockResponse, settingsResponse] = await Promise.all(
        [
          getMessagesAPI(id),
          getPinnedMessagesAPI(id).catch(() => ({ data: [] })),
          getDraftAPI(id).catch(() => ({ data: { content: "" } })),
          blockRequest,
          getConversationSettingsAPI(id).catch(() => ({ data: {} })),
        ],
      );
      setMessages(
        sortMessages(
          await hydrateMessageAssets(messageResponse.data ?? messageResponse ?? []),
        ),
      );
      setPinnedMessages(pinnedResponse.data ?? pinnedResponse ?? []);
      setDraft(draftResponse.data?.content ?? "");
      setBlocked(Boolean(blockResponse.data?.is_blocked));
      setSettings(settingsResponse.data ?? settingsResponse ?? {});
      setMedia([]);
      await markAsReadAPI(id);
      setConversations((rows) =>
        rows.map((item) =>
          conversationId(item) === id ? { ...item, unread_count: 0 } : item,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải tin nhắn",
      );
    } finally {
      setLoadingMessages(false);
    }
  };
  const send = async (
    content: string,
    file?: File | null,
    replyId?: string,
  ) => {
    if (!selected || blocked || (!content.trim() && !file)) return false;
    setProcessing(true);
    setError("");
    try {
      let attachment: any = null;
      if (file) attachment = await uploadChatAttachmentAPI(file);
      const url = attachment?.data?.url;
      const response = await sendMessageAPI(
        conversationId(selected),
        content.trim(),
        file?.type.startsWith("image/") ? url : undefined,
        replyId,
        file?.type.startsWith("audio/") ? url : undefined,
        undefined,
        file &&
        !file.type.startsWith("image/") &&
        !file.type.startsWith("audio/")
          ? url
          : undefined,
        file?.name,
      );
      const row = (await hydrateMessageAssets([response.data ?? response]))[0];
      setMessages((items) => [...items, row]);
      setDraft("");
      await saveDraftAPI(conversationId(selected), "");
      await reloadConversations();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể gửi tin nhắn",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  };
  const edit = async (message: any, content: string) => {
    setProcessing(true);
    try {
      const response = await editMessageAPI(
        message._id ?? message.id,
        content.trim(),
      );
      const row = response.data ?? response;
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id) ? row : item,
        ),
      );
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể sửa tin nhắn",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  };
  const recall = async (message: any) => {
    setProcessing(true);
    try {
      await recallMessageAPI(message._id ?? message.id);
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id)
            ? { ...item, is_recalled: true }
            : item,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể thu hồi tin nhắn",
      );
    } finally {
      setProcessing(false);
    }
  };
  const pin = async (message: any) => {
    try {
      const response = await togglePinAPI(message._id ?? message.id);
      const row = response.data ?? response;
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id) ? row : item,
        ),
      );
      const pinnedResponse = await getPinnedMessagesAPI(
        conversationId(selected),
      );
      setPinnedMessages(pinnedResponse.data ?? pinnedResponse ?? []);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể ghim tin nhắn",
      );
    }
  };
  const translate = async (message: any) => {
    try {
      const response = await translateMessageAPI(
        message._id ?? message.id,
        "vi",
      );
      const translated =
        response.data?.translated_content ?? response.translated_content;
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id)
            ? { ...item, translated_content: translated }
            : item,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể dịch tin nhắn",
      );
    }
  };
  const react = async (message: any, reaction: string) => {
    try {
      const response = await addReactionAPI(
        message._id ?? message.id,
        reaction,
      );
      const row = response.data ?? response;
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id) ? row : item,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể bày tỏ cảm xúc",
      );
    }
  };
  const search = async (query: string) => {
    if (!selected || !query.trim()) return [];
    try {
      const response = await searchMessagesAPI(
        conversationId(selected),
        query.trim(),
      );
      return response.data ?? response ?? [];
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tìm tin nhắn",
      );
      return [];
    }
  };
  const toggleBlock = async () => {
    if (!selected || !canBlockConversation(selected)) return;
    setProcessing(true);
    try {
      if (blocked) await unblockUserAPI(conversationId(selected));
      else await blockUserAPI(conversationId(selected));
      setBlocked((value) => !value);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể cập nhật chặn người dùng",
      );
    } finally {
      setProcessing(false);
    }
  };
  const setDisappearingTimer = async (seconds: number) => {
    if (!selected) return false;
    try {
      await toggleSelfDestructAPI(conversationId(selected), seconds);
      setSettings((value: any) => ({
        ...value,
        self_destruct_seconds: seconds,
        timer_seconds: seconds,
      }));
      setNotice(seconds ? "Đã bật tự xóa tin nhắn" : "Đã tắt tự xóa tin nhắn");
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể cấu hình tự xóa");
      return false;
    }
  };
  const loadMedia = useCallback(async () => {
    if (!selected) return [];
    setLoadingMedia(true);
    try {
      const response = await getMediaVaultAPI(conversationId(selected));
      const rawRows = response.data?.attachments ?? response.attachments ?? [];
      const rows = await Promise.all(
        rawRows.map(async (row: any) => ({
          ...row,
          file: {
            ...(row.file ?? row),
            display_url: await getChatAttachmentBlobUrlAPI(
              row.file?.url ?? row.file?.file_url ?? row.url ?? row.file_url,
            ).catch(() => row.file?.url ?? row.file?.file_url ?? row.url ?? row.file_url),
          },
        })),
      );
      const derived = messages.flatMap((message) => {
        const items: any[] = [];
        if (message.image_url)
          items.push({ message_id: message._id ?? message.id, file: { url: message.image_url, display_url: message.display_image_url, name: "Hình ảnh", content_type: "image/*" } });
        if (message.audio_url)
          items.push({ message_id: message._id ?? message.id, file: { url: message.audio_url, display_url: message.display_audio_url, name: "Tin nhắn thoại", content_type: "audio/*" } });
        const links = String(message.content ?? "").match(/https?:\/\/[^\s]+/g) ?? [];
        links.forEach((url) => items.push({ message_id: message._id ?? message.id, file: { url, name: url, content_type: "text/uri-list" } }));
        return items;
      });
      const merged = [...rows, ...derived].filter(
        (row, index, items) => items.findIndex((candidate) => (candidate.file?.url ?? candidate.url) === (row.file?.url ?? row.url)) === index,
      );
      setMedia(merged);
      return merged;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tải tệp đã chia sẻ");
      return [];
    } finally {
      setLoadingMedia(false);
    }
  }, [selected, messages]);
  const saveToCloud = async (message: any) => {
    try {
      await saveToCloudAPI(
        message._id ?? message.id,
        message.content ?? "",
        message.attachments ?? [],
      );
      setNotice("Đã lưu vào kho cá nhân");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể lưu vào kho cá nhân");
    }
  };
  const createPoll = async (question: string, options: string[]) => {
    if (!selected) return false;
    try {
      const response = await createPollAPI(conversationId(selected), question, options);
      setMessages((rows) => [...rows, response.data ?? response]);
      await reloadConversations();
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tạo bình chọn");
      return false;
    }
  };
  const votePoll = async (message: any, optionId: string) => {
    try {
      const response = await votePollAPI(message._id ?? message.id, optionId);
      const row = response.data ?? response;
      setMessages((items) =>
        items.map((item) =>
          (item._id ?? item.id) === (message._id ?? message.id) ? row : item,
        ),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể ghi nhận bình chọn");
    }
  };
  const toggleMute = async () => {
    if (!selected) return;
    try {
      await toggleMuteAPI(conversationId(selected));
      setMuted((value) => !value);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể cập nhật thông báo",
      );
    }
  };
  const removeConversation = async () => {
    if (!selected) return;
    try {
      await deleteConversationAPI(conversationId(selected));
      setSelected(null);
      setMessages([]);
      await reloadConversations();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể xóa cuộc trò chuyện",
      );
    }
  };
  const findUsers = async (query: string) => {
    if (!query.trim()) return [];
    const response = await searchUsersAPI(query.trim());
    return response.data ?? response ?? [];
  };
  const startWithUser = (person: any) =>
    open({ other_user_id: person._id ?? person.id, other_user: person });
  const createGroup = async (name: string, memberIds: string[]) => {
    try {
      const response = await createGroupAPI(name.trim(), memberIds);
      await reloadConversations();
      await open(response.data ?? response);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể tạo nhóm");
      return false;
    }
  };
  return {
    user,
    authLoading,
    conversations,
    selected,
    setSelected,
    messages,
    pinnedMessages,
    draft,
    setDraft,
    blocked,
    muted,
    settings,
    media,
    loadingMedia,
    loading,
    loadingMessages,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reloadConversations,
    open,
    send,
    edit,
    recall,
    pin,
    translate,
    react,
    search,
    toggleBlock,
    setDisappearingTimer,
    loadMedia,
    saveToCloud,
    createPoll,
    votePoll,
    toggleMute,
    removeConversation,
    findUsers,
    startWithUser,
    createGroup,
  };
}
