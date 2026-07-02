"use client";
import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getConversationsAPI,
  getMessagesAPI,
  sendMessageAPI,
  togglePinAPI,
  editMessageAPI,
  recallMessageAPI,
  searchMessagesAPI,
  addReactionAPI,
  markAsReadAPI,
  shareDocumentAPI,
  getSharedAttachmentsAPI,
  blockUserAPI,
  unblockUserAPI,
  getBlockedStatusAPI,
  togglePinConversationAPI,
  translateMessageAPI,
  createGroupAPI,
  saveDraftAPI,
  getDraftAPI,
  toggleSelfDestructAPI,
  toggleMuteAPI,
  getConversationSettingsAPI,
  deleteConversationAPI,
} from "@/features/messaging/services/thread.service";
import { searchUsersAPI } from "@/features/management/services/profile.service";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  API_URL,
  WS_URL,
  getToken,
} from "@/features/authentication/services/session.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
} from "@/shared/components/ui/Modal";
import {
  ImageIcon,
  Book,
  Loader2,
  ArrowLeft,
  Search,
  Plus,
  Send,
  User,
  MoreVertical,
  ChevronRight,
  X,
  Eye,
  Share2,
  Paperclip,
  Languages,
  ShieldAlert,
  Pin,
  Users,
  Mic,
  Flame,
  Volume2,
  VolumeX,
  ThumbsUp,
  Heart,
  Play,
  Pause,
  Trash2,
  MoreHorizontal,
  Reply,
  PinOff,
  Download,
  Edit2,
  Undo2,
  CheckCheck,
  MessageSquare,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { parseUTC } from "@/shared/lib/app_utils";
import PageLoader from "@/shared/components/common/PageLoader";

const CustomAudioPlayer = ({
  src,
  isSender,
}: {
  src: string;
  isSender: boolean;
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);
  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) audioRef.current.pause();
      else audioRef.current.play();
      setIsPlaying(!isPlaying);
    }
  };
  const handleTimeUpdate = () => {
    if (audioRef.current)
      setProgress(
        (audioRef.current.currentTime / (audioRef.current.duration || 1)) * 100,
      );
  };
  const formatTime = (time: number) => {
    if (!time || isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };
  return (
    <div className="flex items-center gap-3 w-full py-1 min-w-[200px]">
      <button
        onClick={togglePlay}
        className={`flex shrink-0 items-center justify-center w-8 h-8 rounded-full ${isSender ? "bg-white text-[#0071E3]" : "bg-[#0071E3] text-white"}`}
      >
        {isPlaying ? (
          <Pause size={14} className="fill-current" />
        ) : (
          <Play size={14} className="ml-0.5 fill-current" />
        )}
      </button>
      <div className="flex-1 flex items-center gap-3">
        <div
          className="flex-1 h-1.5 rounded-full relative overflow-hidden"
          style={{
            background: isSender
              ? "rgba(255,255,255,0.3)"
              : "rgba(0,113,227,0.1)",
          }}
        >
          <div
            className="absolute top-0 left-0 h-full rounded-full transition-all duration-100"
            style={{
              width: `${progress}%`,
              background: isSender ? "white" : "#0071E3",
            }}
          ></div>
        </div>
        <span className="text-[12px] font-medium opacity-80 min-w-[32px] text-right">
          {formatTime(audioRef.current?.currentTime || 0)}
        </span>
      </div>
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => {
          setIsPlaying(false);
          setProgress(100);
        }}
        className="hidden"
      />
    </div>
  );
};

export default function MessagesPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConv, setSelectedConv] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loadingConv, setLoadingConv] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [sending, setSending] = useState(false);
  const selectedConvRef = useRef<any>(null);

  useEffect(() => {
    selectedConvRef.current = selectedConv;
  }, [selectedConv]);

  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [replyingTo, setReplyingTo] = useState<any>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [editingMsg, setEditingMsg] = useState<any>(null);
  const [showMsgMenu, setShowMsgMenu] = useState<string | null>(null);
  const [activeConvMenuId, setActiveConvMenuId] = useState<string | null>(null);
  const [searchMsgQuery, setSearchMsgQuery] = useState("");
  const [showSearchMsgBar, setShowSearchMsgBar] = useState(false);
  const [searchedMsgResults, setSearchedMsgResults] = useState<any[]>([]);
  const [showShareDocModal, setShowShareDocModal] = useState(false);
  const [myDocsForShare, setMyDocsForShare] = useState<any[]>([]);
  const [loadingShareDocs, setLoadingShareDocs] = useState(false);
  const [showSharedSidebar, setShowSharedSidebar] = useState(false);
  const [sharedAttachments, setSharedAttachments] = useState<any[]>([]);
  const [isBlocked, setIsBlocked] = useState(false);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [allUsersForGroup, setAllUsersForGroup] = useState<any[]>([]);
  const [loadingGroupUsers, setLoadingGroupUsers] = useState(false);
  const [selfDestructSeconds, setSelfDestructSeconds] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  const [showSelfDestructMenu, setShowSelfDestructMenu] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null,
  );
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showConvMenu, setShowConvMenu] = useState(false);
  const recordTimerRef = useRef<any>(null);
  const cancelRecordingRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const socketRef = useRef<WebSocket | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversationsAPI();
      setConversations(res.data || res || []);
    } catch (err: any) {
      showToast("Lỗi đồng bộ danh sách hội thoại.", "error");
    } finally {
      setLoadingConv(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && !user) router.push("/dang-nhap");
    if (!authLoading && user) loadConversations();
  }, [authLoading, user, router, loadConversations]);

  useEffect(() => {
    if (messagesEndRef.current)
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, selectedConv?.other_user_id]);

  const updateConversationInPlace = useCallback(
    (senderId: string, messageData: any) => {
      setConversations((prev) => {
        const idx = prev.findIndex((c) => c.other_user_id === senderId);
        if (idx === -1) return prev;
        const updated = [...prev];
        const conv = { ...updated[idx], last_message: messageData };
        if (selectedConvRef.current?.other_user_id !== senderId)
          conv.unread_count = (conv.unread_count || 0) + 1;
        updated.splice(idx, 1);
        updated.unshift(conv);
        return updated;
      });
    },
    [],
  );

  useEffect(() => {
    if (!user?._id) return;
    const wsUrl = `${WS_URL}/ws/${user._id}?token=${getToken()}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;
    socket.onopen = () => {
      const lastMsgId = localStorage.getItem(`last_msg_id_${user._id}`);
      if (lastMsgId)
        socket.send(
          JSON.stringify({
            action: "sync",
            data: { last_message_id: lastMsgId },
          }),
        );
    };
    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN)
        socket.send(JSON.stringify({ action: "ping" }));
    }, 30000);

    socket.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);
        if (type === "new_message") {
          if (
            selectedConvRef.current &&
            data.sender_id === selectedConvRef.current.other_user_id
          ) {
            setMessages((prev) => {
              if (prev.some((m) => (m._id || m.id) === (data._id || data.id)))
                return prev;
              return [...prev, data];
            });
            if (socketRef.current?.readyState === WebSocket.OPEN) {
              socketRef.current.send(
                JSON.stringify({
                  action: "mark_read",
                  data: {
                    other_user_id: selectedConvRef.current.other_user_id,
                  },
                }),
              );
            }
          }
          updateConversationInPlace(data.sender_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_sent_ack") {
          setMessages((prev) => {
            if (prev.some((m) => (m._id || m.id) === (data._id || data.id)))
              return prev;
            return [...prev, data];
          });
          updateConversationInPlace(data.receiver_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_edited") {
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === (data._id || data.id) ? data : m,
            ),
          );
        } else if (type === "message_pinned") {
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === (data._id || data.id) ? data : m,
            ),
          );
        } else if (type === "message_recalled") {
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === (data._id || data.id) ? data : m,
            ),
          );
        } else if (type === "message_reaction") {
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === (data._id || data.id) ? data : m,
            ),
          );
        } else if (type === "messages_read") {
          setMessages((prev) =>
            prev.map((m) =>
              m.sender_id === data.reader_id ? { ...m, is_read: true } : m,
            ),
          );
        } else if (type === "message_translated") {
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === data.message_id
                ? { ...m, translated_content: data.translated_content }
                : m,
            ),
          );
        } else if (type === "conversation_settings_updated") {
          if (selectedConvRef.current)
            setSelfDestructSeconds(data.self_destruct_seconds || 0);
        }
      } catch (err) {}
    };
    return () => {
      clearInterval(pingInterval);
      socketRef.current = null;
      socket.close();
    };
  }, [user?._id, updateConversationInPlace]);

  const selectConversation = async (conv: any) => {
    if (selectedConvRef.current && newMessage.trim())
      await saveDraftAPI(
        selectedConvRef.current.other_user_id,
        newMessage.trim(),
      );
    setSelectedConv(conv);
    setShowConvMenu(false);
    setActiveConvMenuId(null);
    setLoadingMsgs(true);
    setReplyingTo(null);
    setImageFile(null);
    setShowSearchMsgBar(false);
    setSearchMsgQuery("");
    setSearchedMsgResults([]);
    setShowSharedSidebar(false);
    setShowSelfDestructMenu(false);
    try {
      const res = await getMessagesAPI(conv.other_user_id);
      setMessages(res.data || res || []);
      await markAsReadAPI(conv.other_user_id);
      const blockedRes = await getBlockedStatusAPI(conv.other_user_id);
      setIsBlocked(blockedRes.data?.is_blocked || false);
      const attachRes = await getSharedAttachmentsAPI(conv.other_user_id);
      setSharedAttachments(attachRes.data || attachRes || []);
      const settingsRes = await getConversationSettingsAPI(conv.other_user_id);
      const settings = settingsRes.data || settingsRes;
      setSelfDestructSeconds(settings.self_destruct_seconds || 0);
      setIsMuted(settings.is_muted || false);
      setIsOnline(settings.is_online || false);
      const draftRes = await getDraftAPI(conv.other_user_id);
      setNewMessage(draftRes.data?.content || "");
      setConversations((prev) =>
        prev.map((c) =>
          c.other_user_id === conv.other_user_id
            ? { ...c, unread_count: 0 }
            : c,
        ),
      );
    } catch (err: any) {
      showToast("Không thể truy xuất lịch sử", "error");
    } finally {
      setLoadingMsgs(false);
    }
  };

  const handleSend = async () => {
    if (isBlocked) {
      showToast("Không thể gửi khi bị chặn.", "error");
      return;
    }
    if ((!newMessage.trim() && !imageFile) || !selectedConv || sending) return;
    if (editingMsg) {
      setSending(true);
      try {
        await editMessageAPI(
          editingMsg._id || editingMsg.id,
          newMessage.trim(),
        );
        setMessages((prev) =>
          prev.map((m) =>
            (m._id || m.id) === (editingMsg._id || editingMsg.id)
              ? { ...m, content: newMessage.trim(), is_edited: true }
              : m,
          ),
        );
        setEditingMsg(null);
        setNewMessage("");
      } catch (err: any) {
        showToast("Chỉnh sửa thất bại.", "error");
      } finally {
        setSending(false);
      }
      return;
    }
    setSending(true);
    try {
      let imageUrl = "";
      if (imageFile) {
        setUploadingImage(true);
        const formData = new FormData();
        formData.append("file", imageFile);
        const resUpload = await fetch(`${API_URL}/tai-len/file`, {
          method: "POST",
          headers: { Authorization: `Bearer ${getToken()}` },
          body: formData,
        });
        const uploadData = await resUpload.json();
        imageUrl = uploadData.data.url;
        setUploadingImage(false);
      }
      const res = await sendMessageAPI(
        selectedConv.other_user_id,
        newMessage.trim(),
        imageUrl,
        replyingTo?._id || replyingTo?.id,
      );
      const msg = res.data || res;
      setMessages((prev) => [...prev, msg]);
      setNewMessage("");
      setReplyingTo(null);
      setImageFile(null);
      await saveDraftAPI(selectedConv.other_user_id, "");
      updateConversationInPlace(selectedConv.other_user_id, msg);
    } catch (err: any) {
      showToast("Gửi thất bại.", "error");
    } finally {
      setSending(false);
      setUploadingImage(false);
    }
  };

  const handleStartRecording = async () => {
    cancelRecordingRef.current = false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        if (cancelRecordingRef.current) return;
        setSending(true);
        try {
          const mimeType = recorder.mimeType || "audio/webm";
          const blob = new Blob(chunks, { type: mimeType });
          const file = new File([blob], `voice.webm`, { type: mimeType });
          const formData = new FormData();
          formData.append("file", file);
          const resUpload = await fetch(`${API_URL}/tai-len/file`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}` },
            body: formData,
          });
          const uploadData = await resUpload.json();
          const res = await sendMessageAPI(
            selectedConv.other_user_id,
            "Tin nhắn thoại",
            undefined,
            undefined,
            uploadData.data.url,
          );
          const msg = res.data || res;
          setMessages((prev) => [...prev, msg]);
          updateConversationInPlace(selectedConv.other_user_id, msg);
        } catch (err) {
          showToast("Lỗi gửi giọng nói.", "error");
        } finally {
          setSending(false);
        }
      };
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingDuration(0);
      recordTimerRef.current = setInterval(
        () => setRecordingDuration((prev) => prev + 1),
        1000,
      );
    } catch (err) {
      showToast("Không thể ghi âm.", "error");
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      clearInterval(recordTimerRef.current);
    }
  };

  const handleCancelRecording = () => {
    if (mediaRecorder && isRecording) {
      cancelRecordingRef.current = true;
      mediaRecorder.stop();
      setIsRecording(false);
      clearInterval(recordTimerRef.current);
    }
  };

  const scrollToMessage = (id: string) => {
    const el = messageRefs.current[id];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("bg-[#F5F5F7]");
      setTimeout(() => el.classList.remove("bg-[#F5F5F7]"), 2000);
    }
  };

  const handlePin = async (messageId: string) => {
    try {
      await togglePinAPI(messageId);
      setMessages((prev) => {
        const newMsgs = prev.map((m) =>
          (m._id || m.id) === messageId ? { ...m, is_pinned: !m.is_pinned } : m,
        );
        if (selectedConv)
          setSelectedConv({
            ...selectedConv,
            pinned_messages: newMsgs.filter((m) => m.is_pinned),
          });
        return newMsgs;
      });
    } catch (err: any) {
      showToast("Ghim thất bại.", "error");
    }
  };

  const handleRecall = async (messageId: string) => {
    try {
      await recallMessageAPI(messageId);
      setMessages((prev) =>
        prev.map((m) =>
          (m._id || m.id) === messageId
            ? { ...m, is_recalled: true, content: "Tin nhắn đã thu hồi" }
            : m,
        ),
      );
      showToast("Đã thu hồi.", "success");
    } catch (err: any) {
      showToast("Thu hồi thất bại.", "error");
    }
  };

  const handleSearchMessages = async (q: string) => {
    setSearchMsgQuery(q);
    if (!selectedConv || q.length < 1) return setSearchedMsgResults([]);
    setSearchedMsgResults(
      messages.filter(
        (m) =>
          m.content &&
          !m.is_recalled &&
          m.content.toLowerCase().includes(q.toLowerCase()),
      ),
    );
  };

  const handleAddReaction = async (messageId: string, reaction: string) => {
    try {
      const msg = messages.find((m) => (m._id || m.id) === messageId);
      const existing = msg?.reactions?.find(
        (r: any) => r.user_id === user?._id,
      );
      const finalReaction = existing?.reaction === reaction ? "" : reaction;
      const res = await addReactionAPI(messageId, finalReaction);
      setMessages((prev) =>
        prev.map((m) =>
          (m._id || m.id) === messageId
            ? { ...m, reactions: (res.data || res).reactions }
            : m,
        ),
      );
    } catch (err: any) {
      showToast("Thất bại.", "error");
    }
  };

  const openShareDoc = async () => {
    setShowShareDocModal(true);
    setLoadingShareDocs(true);
    try {
      const docsRes = await getMyDocumentsAPI();
      setMyDocsForShare(docsRes.data || docsRes || []);
    } catch (err: any) {}
    setLoadingShareDocs(false);
  };

  const handleShareDoc = async (docId: string) => {
    if (!selectedConv) return;
    try {
      const res = await shareDocumentAPI(selectedConv.other_user_id, docId);
      const newMsg = res.data || res;
      setMessages((prev) => [...prev, newMsg]);
      setShowShareDocModal(false);
      showToast("Đã chia sẻ.", "success");
      updateConversationInPlace(selectedConv.other_user_id, newMsg);
    } catch (err: any) {
      showToast("Lỗi chia sẻ.", "error");
    }
  };

  const handleBlockUser = async () => {
    if (!selectedConv) return;
    try {
      if (isBlocked) {
        await unblockUserAPI(selectedConv.other_user_id);
        setIsBlocked(false);
        showToast("Đã bỏ chặn.", "success");
      } else {
        await blockUserAPI(selectedConv.other_user_id);
        setIsBlocked(true);
        showToast("Đã chặn.", "success");
      }
    } catch (err: any) {
      showToast("Thao tác thất bại.", "error");
    }
  };

  const handleTogglePinConv = async (otherId: string) => {
    try {
      const res = await togglePinConversationAPI(otherId);
      const status = res.data || res;
      showToast(status.is_pinned ? "Đã ghim." : "Đã bỏ ghim.", "success");
      setActiveConvMenuId(null);
    } catch (err: any) {
      showToast("Không thể ghim.", "error");
    }
  };

  const handleMarkAsRead = async (otherUserId: string) => {
    try {
      await markAsReadAPI(otherUserId);
      setConversations((prev) =>
        prev.map((c) =>
          c.other_user_id === otherUserId ? { ...c, unread_count: 0 } : c,
        ),
      );
      setActiveConvMenuId(null);
    } catch (err) {
      showToast("Không thể đánh dấu", "error");
    }
  };

  const handleDeleteConv = async (otherUserId: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa?")) return;
    try {
      await deleteConversationAPI(otherUserId);
      if (selectedConv?.other_user_id === otherUserId) setSelectedConv(null);
      setConversations((prev) =>
        prev.filter((c) => c.other_user_id !== otherUserId),
      );
      setActiveConvMenuId(null);
      showToast("Đã xóa", "success");
    } catch (err) {
      showToast("Không thể xóa", "error");
    }
  };

  const handleTranslate = async (messageId: string, lang: string) => {
    try {
      const res = await translateMessageAPI(messageId, lang);
      setMessages((prev) =>
        prev.map((m) =>
          (m._id || m.id) === messageId
            ? { ...m, translated_content: (res.data || res).translated_content }
            : m,
        ),
      );
      showToast("Đã dịch.", "success");
    } catch (err: any) {
      showToast("Không thể dịch.", "error");
    }
  };

  const handleToggleMute = async () => {
    if (!selectedConv) return;
    try {
      const res = await toggleMuteAPI(selectedConv.other_user_id);
      setIsMuted((res.data || res).is_muted);
      showToast(
        (res.data || res).is_muted ? "Đã tắt âm." : "Đã bật âm.",
        "success",
      );
    } catch (err: any) {
      showToast("Không thể điều chỉnh.", "error");
    }
  };

  const handleUpdateSelfDestruct = async (seconds: number) => {
    if (!selectedConv) return;
    try {
      await toggleSelfDestructAPI(selectedConv.other_user_id, seconds);
      setSelfDestructSeconds(seconds);
      setShowSelfDestructMenu(false);
      showToast(
        seconds > 0 ? `Đã đặt tự hủy sau ${seconds}s.` : "Đã tắt tự hủy.",
        "success",
      );
    } catch (err: any) {
      showToast("Cài đặt thất bại.", "error");
    }
  };

  const openGroupModal = async () => {
    setShowGroupModal(true);
    setLoadingGroupUsers(true);
    try {
      const res = await searchUsersAPI("a");
      setAllUsersForGroup(res.data || res || []);
    } catch (err: any) {}
    setLoadingGroupUsers(false);
  };

  const handleCreateGroup = async () => {
    if (!groupName.trim()) return showToast("Nhập tên nhóm.", "error");
    try {
      const res = await createGroupAPI(groupName.trim(), selectedMembers);
      const created = res.data || res;
      showToast("Tạo nhóm thành công.", "success");
      setShowGroupModal(false);
      setGroupName("");
      setSelectedMembers([]);
      loadConversations();
      selectConversation({
        other_user_id: created._id || created.id,
        other_user: {
          username: created.group_name,
          full_name: created.group_name,
          avatar_url: "",
          is_group: true,
        },
        last_message: null,
        pinned_messages: [],
        unread_count: 0,
      });
    } catch (err: any) {
      showToast("Tạo thất bại.", "error");
    }
  };

  const handleSearchUsers = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) return setSearchResults([]);
    setSearching(true);
    try {
      const res = await searchUsersAPI(q);
      setSearchResults(res.data || res || []);
    } catch (err: any) {
      showToast("Tìm kiếm thất bại.", "error");
    } finally {
      setSearching(false);
    }
  };

  const startNewChat = (otherUser: any) => {
    const existing = conversations.find(
      (c) => c.other_user_id === (otherUser._id || otherUser.id),
    );
    if (existing) selectConversation(existing);
    else {
      setSelectedConv({
        other_user_id: otherUser._id || otherUser.id,
        other_user: otherUser,
        last_message: null,
        pinned_messages: [],
      });
      setMessages([]);
    }
    setShowNewChatModal(false);
    setSearchQuery("");
    setSearchResults([]);
  };

  const sortedConversations = [...conversations].sort((a, b) => {
    const aPinned = user?.pinned_conversations?.includes(a.other_user_id)
      ? 1
      : 0;
    const bPinned = user?.pinned_conversations?.includes(b.other_user_id)
      ? 1
      : 0;
    if (aPinned !== bPinned) return bPinned - aPinned;
    return (
      new Date(b.last_message?.created_at || 0).getTime() -
      new Date(a.last_message?.created_at || 0).getTime()
    );
  });

  if (authLoading) return <PageLoader />;
  if (!user) return null;

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 h-[calc(100dvh-56px)] flex flex-col font-sans text-[#1D1D1F]">
      <Modal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        className="max-w-xl rounded-[18px] bg-[#F5F5F7] p-0 border-none -2xl"
      >
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            Bắt đầu hội thoại mới
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6 pt-0 space-y-6">
          <input
            value={searchQuery}
            onChange={(e) => handleSearchUsers(e.target.value)}
            placeholder=""
            className="apple-input w-full"
          />
          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {searching ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]" />
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((u) => (
                <div
                  key={u._id || u.id}
                  onClick={() => startNewChat(u)}
                  className="flex items-center justify-between p-4 bg-white rounded-[10px] cursor-pointer hover:"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-[#F5F5F7] rounded-full overflow-hidden flex items-center justify-center">
                      {u.avatar_url ? (
                        <img
                          src={u.avatar_url}
                          className="w-full h-full object-cover"
                          alt=""
                        />
                      ) : (
                        <User className="w-6 h-6 text-[#6E6E73]" />
                      )}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[15px] font-medium text-[#1D1D1F]">
                        {u.full_name || u.username}
                      </span>
                      <span className="text-[13px] text-[#6E6E73]">
                        ID: {u.slug || u.username}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#6E6E73]" />
                </div>
              ))
            ) : (
              <p className="text-center text-[13px] text-[#6E6E73] py-12">
                Không tìm thấy kết quả
              </p>
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showGroupModal}
        onClose={() => setShowGroupModal(false)}
        className="max-w-md rounded-[18px] bg-[#F5F5F7] p-0 border-none -2xl"
      >
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            Tạo nhóm
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6 pt-0 space-y-4">
          <input
            type="text"
            placeholder=""
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            className="apple-input w-full"
          />
          <div className="max-h-48 overflow-y-auto space-y-2 bg-white rounded-[10px] p-2 border border-[#D2D2D7]">
            {loadingGroupUsers ? (
              <div className="py-6 flex justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-[#6E6E73]" />
              </div>
            ) : (
              allUsersForGroup.map((u) => (
                <div
                  key={u._id || u.id}
                  className="flex items-center gap-3 p-2 hover:bg-[#F5F5F7] rounded-[8px]"
                >
                  <input
                    type="checkbox"
                    checked={selectedMembers.includes(u._id || u.id)}
                    onChange={(e) => {
                      if (e.target.checked)
                        setSelectedMembers([...selectedMembers, u._id || u.id]);
                      else
                        setSelectedMembers(
                          selectedMembers.filter(
                            (id) => id !== (u._id || u.id),
                          ),
                        );
                    }}
                    className="w-4 h-4 rounded text-[#0071E3] focus:ring-[#0071E3]"
                  />
                  <span className="text-[15px] text-[#1D1D1F]">
                    {u.full_name || u.username}
                  </span>
                </div>
              ))
            )}
          </div>
          <button onClick={handleCreateGroup} className="pill-button w-full">
            Khởi tạo
          </button>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showShareDocModal}
        onClose={() => setShowShareDocModal(false)}
        className="max-w-xl rounded-[18px] bg-[#F5F5F7] p-0 border-none -2xl"
      >
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">
            Chia sẻ tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6 pt-0 max-h-[350px] overflow-y-auto space-y-2">
          {loadingShareDocs ? (
            <div className="py-12 flex justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]" />
            </div>
          ) : myDocsForShare.length > 0 ? (
            myDocsForShare.map((doc) => (
              <div
                key={doc._id || doc.id}
                onClick={() => handleShareDoc(doc._id || doc.id)}
                className="p-4 bg-white rounded-[10px] cursor-pointer hover:flex justify-between items-center"
              >
                <div className="flex flex-col">
                  <span className="text-[15px] font-medium text-[#1D1D1F]">
                    {doc.title}
                  </span>
                  <span className="text-[13px] text-[#6E6E73]">
                    Định dạng: {doc.format || "TXT"}
                  </span>
                </div>
                <Share2 className="w-5 h-5 text-[#0071E3]" />
              </div>
            ))
          ) : (
            <p className="text-center text-[13px] text-[#6E6E73] py-6">
              Không có tài liệu
            </p>
          )}
        </ModalContent>
      </Modal>

      <div className="flex flex-1 min-h-0 gap-6">
        <div
          className={`w-full md:w-[320px] bg-[#F5F5F7] rounded-[18px] flex flex-col overflow-hidden shrink-0 ${selectedConv ? "hidden md:flex" : "flex"}`}
        >
          <div className="p-6 pb-4 flex items-center justify-between">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
              Hộp thư
            </h2>
            <div className="flex gap-2">
              <button
                onClick={openGroupModal}
                className="p-2 bg-white rounded-full text-[#0071E3] hover:opacity-80 transition-opacity"
              >
                <Users className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowNewChatModal(true)}
                className="p-2 bg-[#0071E3] rounded-full text-white hover:bg-[#0055C6] transition-colors"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 hide-scrollbar">
            {loadingConv ? (
              <div className="p-12 flex justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-[#6E6E73]" />
              </div>
            ) : sortedConversations.length > 0 ? (
              sortedConversations.map((conv) => {
                const isPinned = user?.pinned_conversations?.includes(
                  conv.other_user_id,
                );
                const active =
                  selectedConv?.other_user_id === conv.other_user_id;
                return (
                  <div
                    key={conv.other_user_id}
                    onClick={() => selectConversation(conv)}
                    className={`p-4 rounded-[14px] cursor-pointer flex items-center gap-4 transition-colors ${active ? "bg-white" : "hover:bg-white/50"}`}
                  >
                    <div className="w-12 h-12 bg-[#D2D2D7] rounded-full overflow-hidden shrink-0">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex justify-center items-center">
                          <User className="w-6 h-6 text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[15px] font-medium text-[#1D1D1F] truncate pr-2">
                          {conv.other_user?.full_name ||
                            conv.other_user?.username}
                        </span>
                        <span className="text-[12px] text-[#6E6E73] shrink-0">
                          {conv.last_message?.created_at
                            ? parseUTC(
                                conv.last_message.created_at,
                              ).toLocaleTimeString("vi-VN", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ""}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <p
                          className={`text-[13px] truncate ${conv.unread_count > 0 ? "font-semibold text-[#1D1D1F]" : "text-[#6E6E73]"}`}
                        >
                          {conv.last_message?.content || "Chưa có tin nhắn"}
                        </p>
                        {conv.unread_count > 0 && (
                          <div className="w-2.5 h-2.5 bg-[#0071E3] rounded-full shrink-0 ml-2" />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-24 text-center">
                <p className="text-[15px] text-[#6E6E73]">Hộp thư trống</p>
              </div>
            )}
          </div>
        </div>

        <div
          className={`flex-1 flex flex-col min-w-0 bg-[#F5F5F7] rounded-[18px] overflow-hidden ${!selectedConv ? "hidden md:flex items-center justify-center" : "flex"}`}
        >
          {selectedConv ? (
            <>
              <div className="h-[64px] px-6 flex items-center justify-between border-b border-[#D2D2D7] bg-transparent">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedConv(null)}
                    className="md:hidden text-[#0071E3]"
                  >
                    <ArrowLeft className="w-6 h-6" />
                  </button>
                  <div className="w-10 h-10 rounded-full bg-[#D2D2D7] overflow-hidden">
                    {selectedConv.other_user?.avatar_url ? (
                      <img
                        src={selectedConv.other_user.avatar_url}
                        className="w-full h-full object-cover"
                        alt=""
                      />
                    ) : (
                      <User className="w-5 h-5 text-white m-auto mt-2.5" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-[17px] font-medium text-[#1D1D1F]">
                      {selectedConv.other_user?.full_name ||
                        selectedConv.other_user?.username}
                    </h3>
                    <p className="text-[12px] text-[#6E6E73]">
                      {isOnline ? "Trực tuyến" : "Ngoại tuyến"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConvMenu(!showConvMenu)}
                  className="text-[#0071E3] p-2 hover:bg-[#F5F5F7] rounded-full"
                >
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 bg-transparent hide-scrollbar relative">
                {loadingMsgs ? (
                  <div className="flex h-full items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin text-[#0071E3]" />
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((msg, i) => {
                      const isSender = msg.sender_id === user?._id;
                      return (
                        <div
                          key={msg._id || msg.id || i}
                          ref={(el) => {
                            messageRefs.current[msg._id || msg.id] = el;
                          }}
                          className={`flex ${isSender ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[70%] rounded-[18px] px-4 py-2.5 ${msg.is_recalled ? "bg-[#F5F5F7] text-[#6E6E73] italic" : isSender ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#1D1D1F]"}`}
                          >
                            {msg.image_url && !msg.is_recalled && (
                              <img
                                src={
                                  msg.image_url.startsWith("http")
                                    ? msg.image_url
                                    : `${API_URL}/storage/${msg.image_url}`
                                }
                                alt=""
                                className="rounded-[10px] mb-2 max-h-[300px]"
                              />
                            )}
                            {msg.audio_url && !msg.is_recalled && (
                              <CustomAudioPlayer
                                src={
                                  msg.audio_url.startsWith("http")
                                    ? msg.audio_url
                                    : `${API_URL}/storage/${msg.audio_url}`
                                }
                                isSender={isSender}
                              />
                            )}
                            {!msg.is_recalled &&
                              msg.content !== "Tin nhắn thoại" && (
                                <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">
                                  {msg.content}
                                </p>
                              )}
                            {msg.is_recalled && "Tin nhắn đã thu hồi"}
                            <div
                              className={`text-[11px] mt-1 ${isSender ? "text-blue-200 text-right" : "text-[#6E6E73]"}`}
                            >
                              {parseUTC(msg.created_at).toLocaleTimeString(
                                "vi-VN",
                                { hour: "2-digit", minute: "2-digit" },
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              <div className="p-4 bg-transparent">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-[#0071E3] hover:bg-[#F5F5F7] rounded-full transition-colors shrink-0"
                  >
                    <ImageIcon className="w-6 h-6" />
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={(e) =>
                      setImageFile(e.target.files ? e.target.files[0] : null)
                    }
                  />
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSend();
                      }}
                      placeholder=""
                      className="w-full bg-white border border-transparent rounded-[980px] pl-4 pr-12 py-3 text-[15px] focus:outline-none focus:border-[#D2D2D7]"
                    />
                    <button
                      onClick={handleStartRecording}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[#0071E3] hover:bg-white rounded-full"
                    >
                      <Mic className="w-5 h-5" />
                    </button>
                  </div>
                  <button
                    onClick={handleSend}
                    disabled={!newMessage.trim() && !imageFile}
                    className="p-3 bg-[#0071E3] text-white rounded-full hover:bg-[#0055C6] disabled:opacity-50 transition-colors shrink-0"
                  >
                    <Send className="w-5 h-5 ml-0.5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center">
              <MessageSquare className="w-12 h-12 text-[#D2D2D7] mx-auto mb-4" />
              <p className="text-[17px] text-[#6E6E73]">
                Chọn một hội thoại để bắt đầu
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
