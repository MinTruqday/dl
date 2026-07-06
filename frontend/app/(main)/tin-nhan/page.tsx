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
  deleteMessageForMeAPI,
  restoreMessageAPI,
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
  Timer,
  Check,
  FileText,
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
        className={`flex shrink-0 items-center justify-center w-6 h-6 rounded-full ${isSender ? "bg-white text-[#0071E3]" : "bg-[#0071E3] text-white"}`}
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

  const formatRelativeTime = (date: Date) => {
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    const timeStr = date.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
    if (now.toDateString() === date.toDateString()) return `${timeStr} Hôm nay`;
    
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (yesterday.toDateString() === date.toDateString()) return `${timeStr} Hôm qua`;
    
    if (diffDays < 7) {
      const days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
      return `${timeStr} ${days[date.getDay()]}`;
    }
    
    return `${timeStr} ${date.toLocaleDateString("vi-VN")}`;
  };
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
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [editingMsg, setEditingMsg] = useState<any>(null);
  const [activeMsgMenuId, setActiveMsgMenuId] = useState<string | null>(null);
  const [showMsgMenu, setShowMsgMenu] = useState<string | null>(null);
  const [showDeleteSubMenu, setShowDeleteSubMenu] = useState<string | null>(null);
  const [activeMsgRect, setActiveMsgRect] = useState<{top: number; left: number; right: number; bottom: number; isSender: boolean} | null>(null);
  const [activeMsgObj, setActiveMsgObj] = useState<any>(null);
  const [isPinnedExpanded, setIsPinnedExpanded] = useState(false);
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
  const [isRecordingPaused, setIsRecordingPaused] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null,
  );
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showConvMenu, setShowConvMenu] = useState(false);
  const [aliases, setAliases] = useState<Record<string, string>>({});
  const [showAliasModal, setShowAliasModal] = useState(false);
  const [aliasInput, setAliasInput] = useState("");
  const recordTimerRef = useRef<any>(null);
  const cancelRecordingRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
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
  }, [user, authLoading, router]);

  useEffect(() => {
    const stored = localStorage.getItem("user_aliases");
    if (stored) {
      try {
        setAliases(JSON.parse(stored));
      } catch (e) {}
    }
  }, []);

  const handleSetAlias = () => {
    if (!selectedConv) return;
    const userId = selectedConv.other_user_id;
    const updated = { ...aliases, [userId]: aliasInput };
    if (!aliasInput.trim()) delete updated[userId];
    setAliases(updated);
    localStorage.setItem("user_aliases", JSON.stringify(updated));
    setShowAliasModal(false);
  };

  useEffect(() => {
    if (!authLoading && user) loadConversations();
  }, [authLoading, user, router, loadConversations]);

  useEffect(() => {
    if (messagesContainerRef.current && !loadingMsgs) {
      const el = messagesContainerRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [messages.length, selectedConv?.other_user_id, loadingMsgs]);

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
    setImageFiles([]);
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
    if ((!newMessage.trim() && imageFiles.length === 0) || !selectedConv || sending) return;
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
      if (imageFiles.length > 0) {
        setUploadingImage(true);
        for (let i = 0; i < imageFiles.length; i++) {
          const formData = new FormData();
          formData.append("file", imageFiles[i]);
          const resUpload = await fetch(`${API_URL}/tai-len/tap-tin`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}` },
            body: formData,
          });
          const uploadData = await resUpload.json();
          const filename = imageFiles[i].name || uploadData.data?.url || "";
          const ext = filename.split(".").pop()?.toLowerCase() || "";
          const isImage = ["png", "jpg", "jpeg", "gif", "webp"].includes(ext);
          const res = await sendMessageAPI(
            selectedConv.other_user_id,
            i === 0 ? newMessage.trim() : "",
            isImage ? uploadData.data.url : undefined,
            replyingTo?._id || replyingTo?.id,
            undefined,
            selfDestructSeconds > 0 ? selfDestructSeconds : undefined,
            !isImage ? uploadData.data.url : undefined,
            !isImage ? imageFiles[i].name : undefined,
          );
          const msg = res.data || res;
          setMessages((prev) => [...prev, msg]);
          updateConversationInPlace(selectedConv.other_user_id, msg);
        }
        setUploadingImage(false);
      } else {
        const res = await sendMessageAPI(
          selectedConv.other_user_id,
          newMessage.trim(),
          "",
          replyingTo?._id || replyingTo?.id,
          undefined,
          selfDestructSeconds > 0 ? selfDestructSeconds : undefined,
        );
        const msg = res.data || res;
        setMessages((prev) => [...prev, msg]);
        updateConversationInPlace(selectedConv.other_user_id, msg);
      }
      setNewMessage("");
      setReplyingTo(null);
      setImageFiles([]);
      await saveDraftAPI(selectedConv.other_user_id, "");
    } catch (err: any) {
      showToast("Gửi thất bại.", "error");
    } finally {
      setSending(false);
      setUploadingImage(false);
    }
  };

  const handleTogglePauseRecording = () => {
    if (mediaRecorder && isRecording) {
      if (isRecordingPaused) {
        mediaRecorder.resume();
        setIsRecordingPaused(false);
        recordTimerRef.current = setInterval(
          () => setRecordingDuration((prev) => prev + 1),
          1000,
        );
      } else {
        mediaRecorder.pause();
        setIsRecordingPaused(true);
        clearInterval(recordTimerRef.current);
      }
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
          const resUpload = await fetch(`${API_URL}/tai-len/tap-tin`, {
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
            selfDestructSeconds > 0 ? selfDestructSeconds : undefined,
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
      setIsRecordingPaused(false);
      setRecordingDuration(0);
      if (recordTimerRef.current) clearInterval(recordTimerRef.current);
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
      setIsRecordingPaused(false);
      clearInterval(recordTimerRef.current);
    }
  };

  const handleCancelRecording = () => {
    if (mediaRecorder && isRecording) {
      cancelRecordingRef.current = true;
      mediaRecorder.stop();
      setIsRecording(false);
      setIsRecordingPaused(false);
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

  const handleDeleteForMe = async (messageId: string) => {
    try {
      await deleteMessageForMeAPI(messageId);
    } catch {
      // ignore API error — hide locally regardless
    }
    setMessages((prev) => prev.filter((m) => (m._id || m.id) !== messageId));
    showToast("Đã xóa khỏi màn hình của bạn.", "success");
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
      setMessages((prev) =>
        prev.map((m) => {
          if ((m._id || m.id) !== messageId) return m;
          const reactions = m.reactions || [];
          const updatedReactions = [...reactions, { user_id: user?._id, user_name: user?.full_name, reaction }];
          return { ...m, reactions: updatedReactions };
        })
      );
      if (activeMsgObj && (activeMsgObj._id || activeMsgObj.id) === messageId) {
        setActiveMsgObj((prev: any) => {
          const reactions = prev.reactions || [];
          const updatedReactions = [...reactions, { user_id: user?._id, user_name: user?.full_name, reaction }];
          return { ...prev, reactions: updatedReactions };
        });
      }
      const res = await addReactionAPI(messageId, reaction);
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
        className="max-w-xl"
      >
        <ModalHeader>
          <ModalTitle>
            Bắt đầu hội thoại mới
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="relative mb-4">
            <Search className="w-4 h-4 text-[#A1A1A6] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={searchQuery}
              onChange={(e) => handleSearchUsers(e.target.value)}
              placeholder="Tìm kiếm người dùng..."
              className="w-full bg-[#E8E8ED] text-[#1D1D1F] placeholder:text-[#A1A1A6] pl-9 pr-4 py-2 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3] transition-all text-[15px]"
            />
          </div>
          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {searching ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-[#6E6E73]" />
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((u) => (
                <div
                  key={u._id || u.id}
                  onClick={() => startNewChat(u)}
                  className="flex items-center justify-between p-4 bg-white rounded-[10px] cursor-pointer hover:"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-6 h-6 bg-[#F5F5F7] rounded-full overflow-hidden flex items-center justify-center">
                      {u.avatar_url ? (
                        <img
                          src={u.avatar_url}
                          className="w-full h-full object-cover"
                          alt=""
                        />
                      ) : (
                        <User className="w-4 h-4 text-[#6E6E73]" />
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
                  <ChevronRight className="w-4 h-4 text-[#6E6E73]" />
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
      >
        <ModalHeader>
          <ModalTitle>
            Tạo nhóm
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
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
                <Loader2 className="w-4 h-4 animate-spin text-[#6E6E73]" />
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
                    className="w-6 h-6 rounded text-[#0071E3] focus:ring-[#0071E3]"
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
        className="max-w-xl"
      >
        <ModalHeader>
          <ModalTitle>
            Chia sẻ tài liệu
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[350px] overflow-y-auto">
          {loadingShareDocs ? (
            <div className="py-12 flex justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-[#6E6E73]" />
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
                <Share2 className="w-4 h-4 text-[#0071E3]" />
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
              Tất cả tin nhắn
            </h2>
            <div className="flex gap-2">
              <button
                onClick={openGroupModal}
                className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                title="Tạo nhóm"
              >
                <Users className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowNewChatModal(true)}
                className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                title="Tin nhắn mới"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2 hide-scrollbar">
            {loadingConv ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="p-4 rounded-[14px] flex items-center gap-4 animate-pulse bg-white/50">
                    <div className="w-6 h-6 bg-[#D2D2D7] rounded-full shrink-0" />
                    <div className="flex-1 space-y-2.5">
                      <div className="h-3 bg-[#D2D2D7] rounded-full w-24" />
                      <div className="h-2 bg-[#D2D2D7] rounded-full w-32" />
                    </div>
                  </div>
                ))}
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
                    className={`p-4 rounded-[14px] cursor-pointer flex items-center gap-4 transition-colors group/conv relative ${active ? "bg-white" : "hover:bg-white/50"}`}
                  >
                    <div className="w-6 h-6 bg-[#D2D2D7] rounded-full overflow-hidden shrink-0">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex justify-center items-center">
                          <User className="w-4 h-4 text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[15px] font-medium text-[#1D1D1F] truncate pr-2">
                          {aliases[conv.other_user_id] || conv.other_user?.full_name ||
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
                      <div className="flex justify-between items-center relative group-hover/conv:pr-6">
                        <p
                          className={`text-[13px] truncate transition-all duration-300 ${conv.unread_count > 0 ? "font-semibold text-[#1D1D1F]" : "text-[#6E6E73]"}`}
                        >
                          {conv.last_message?.content || "Chưa có tin nhắn"}
                        </p>
                        {conv.unread_count > 0 && (
                          <div className="w-2.5 h-2.5 bg-[#0071E3] rounded-full shrink-0 ml-2" />
                        )}
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 opacity-0 group-hover/conv:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => { e.stopPropagation(); setActiveConvMenuId(activeConvMenuId === conv.other_user_id ? null : conv.other_user_id); }}
                            className="p-1 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full bg-[#F5F5F7] md:bg-white shadow-sm"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                          {activeConvMenuId === conv.other_user_id && (
                            <div className="absolute z-50 w-48 bg-white/90 backdrop-blur-md rounded-[14px] shadow-[0_8px_32px_rgba(0,0,0,0.15)] border border-[#E8E8ED] py-1.5 flex flex-col right-0 top-full mt-1">
                              <button 
                                onClick={(e) => { e.stopPropagation(); handleTogglePinConv(conv.other_user_id); }}
                                className="flex items-center gap-3 px-4 py-2.5 text-[13px] hover:bg-[#F5F5F7] text-[#1D1D1F] text-left rounded-t-[10px] transition-colors"
                              >
                                <Pin className="w-3.5 h-3.5 text-[#6E6E73]" />
                                {isPinned ? "Bỏ ghim" : "Ghim"}
                              </button>
                              <button 
                                onClick={(e) => { e.stopPropagation(); handleMarkAsRead(conv.other_user_id); }}
                                className="flex items-center gap-3 px-4 py-2.5 text-[13px] hover:bg-[#F5F5F7] text-[#1D1D1F] text-left transition-colors"
                              >
                                <CheckCheck className="w-3.5 h-3.5 text-[#6E6E73]" />
                                Đánh dấu đã đọc
                              </button>
                              <div className="h-px bg-[#F2F2F7] mx-3 my-1" />
                              <button 
                                onClick={(e) => { e.stopPropagation(); handleDeleteConv(conv.other_user_id); setActiveConvMenuId(null); }}
                                className="flex items-center gap-3 px-4 py-2.5 text-[13px] hover:bg-[#FFF5F5] text-red-500 text-left rounded-b-[10px] transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" /> Xóa hội thoại
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-24 text-center">
                <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
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
                    <ArrowLeft className="w-4 h-4" />
                  </button>
                  <div className="w-6 h-6 rounded-full bg-[#D2D2D7] overflow-hidden">
                    {selectedConv.other_user?.avatar_url ? (
                      <img
                        src={selectedConv.other_user.avatar_url}
                        className="w-full h-full object-cover"
                        alt=""
                      />
                    ) : (
                      <User className="w-4 h-4 text-white m-auto mt-2.5" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-[17px] font-medium text-[#1D1D1F]">
                      {aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name ||
                        selectedConv.other_user?.username}
                    </h3>
                    <p className="text-[12px] text-[#6E6E73]">
                      {isOnline ? "Trực tuyến" : "Ngoại tuyến"}
                    </p>
                  </div>
                </div>
                <div className="relative flex items-center gap-2">
                  <button
                    onClick={() => setShowSearchMsgBar(!showSearchMsgBar)}
                    className={`p-2 rounded-full transition-colors ${showSearchMsgBar ? "bg-[#E8E8ED] text-[#1D1D1F]" : "text-[#0071E3] hover:bg-[#F5F5F7]"}`}
                    title="Tìm kiếm"
                  >
                    <Search className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setShowConvMenu(!showConvMenu)}
                    className="text-[#0071E3] p-2 hover:bg-[#F5F5F7] rounded-full"
                  >
                    <MoreVertical className="w-4 h-4" />
                  </button>
                  {showConvMenu && (
                    <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-[14px] shadow-lg border border-[#F5F5F7] py-2 z-50">
                      <div className="relative">
                        <button onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center justify-between text-[14px]">
                          <span className="flex items-center gap-2"><Timer className="w-4 h-4" /> Tự hủy</span>
                          <ChevronRight className="w-4 h-4" />
                        </button>
                        {showSelfDestructMenu && (
                          <div className="absolute top-0 right-[100%] mr-2 w-48 bg-white rounded-[14px] shadow-lg border border-[#F5F5F7] py-2">
                            <div className="px-4 py-2 text-[12px] font-semibold text-[#6E6E73] uppercase tracking-wider">Thời gian tự hủy</div>
                            {[
                              { label: "Tắt", value: 0 },
                              { label: "5 giây", value: 5 },
                              { label: "10 giây", value: 10 },
                              { label: "1 phút", value: 60 },
                              { label: "5 phút", value: 300 },
                            ].map((opt) => (
                              <button
                                key={opt.value}
                                onClick={() => { setSelfDestructSeconds(opt.value); setShowSelfDestructMenu(false); setShowConvMenu(false); }}
                                className={`w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center justify-between text-[14px] ${selfDestructSeconds === opt.value ? "text-[#0071E3] font-medium" : "text-[#1D1D1F]"}`}
                              >
                                {opt.label}
                                {selfDestructSeconds === opt.value && <Check className="w-4 h-4" />}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <button onClick={() => { openShareDoc(); setShowConvMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center gap-2 text-[14px]">
                        <Share2 className="w-4 h-4" /> Chia sẻ tài liệu
                      </button>
                      <button onClick={() => { setAliasInput(aliases[selectedConv.other_user_id] || ""); setShowAliasModal(true); setShowConvMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center gap-2 text-[14px]">
                        <Edit2 className="w-4 h-4" /> Đặt biệt danh
                      </button>
                      <button onClick={() => { handleToggleMute(); setShowConvMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center gap-2 text-[14px]">
                        {isMuted ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />} {isMuted ? "Bật thông báo" : "Tắt thông báo"}
                      </button>
                      <button onClick={() => { handleBlockUser(); setShowConvMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center gap-2 text-[14px] text-red-500">
                        <ShieldAlert className="w-4 h-4" /> {isBlocked ? "Bỏ chặn" : "Chặn người dùng"}
                      </button>
                      <button onClick={() => { handleDeleteConv(selectedConv.other_user_id); setShowConvMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-[#F5F5F7] flex items-center gap-2 text-[14px] text-red-500">
                        <Trash2 className="w-4 h-4" /> Xóa hội thoại
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Search bar — slides in below header */}
              {showSearchMsgBar && (
                <div className="px-4 py-2.5 border-b border-[#F2F2F7] bg-transparent">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-[#A1A1A6] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                      autoFocus
                      type="text"
                      value={searchMsgQuery}
                      onChange={(e) => handleSearchMessages(e.target.value)}
                      placeholder="Tìm trong đoạn chat..."
                      className="w-full bg-[#E8E8ED] text-[#1D1D1F] placeholder:text-[#A1A1A6] pl-8 pr-8 py-1.5 rounded-[10px] text-[14px] focus:outline-none transition-all"
                    />
                    {searchMsgQuery && (
                      <button
                        onClick={() => { setSearchMsgQuery(""); setSearchedMsgResults([]); }}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#A1A1A6] hover:text-[#6E6E73] transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  {searchedMsgResults.length > 0 && (
                    <div className="mt-2 max-h-[180px] overflow-y-auto space-y-1 hide-scrollbar">
                      {searchedMsgResults.map((m) => (
                        <div
                          key={m._id || m.id}
                          onClick={() => { scrollToMessage(m._id || m.id); setShowSearchMsgBar(false); setSearchMsgQuery(""); setSearchedMsgResults([]); }}
                          className="px-3 py-2 bg-white rounded-[10px] cursor-pointer hover:bg-[#F5F5F7] transition-colors"
                        >
                          <p className="text-[13px] text-[#1D1D1F] truncate">{m.content}</p>
                          <p className="text-[11px] text-[#6E6E73] mt-0.5">
                            {new Date(parseUTC(m.created_at)).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                  {searchMsgQuery.length > 0 && searchedMsgResults.length === 0 && (
                    <p className="text-[12px] text-[#A1A1A6] mt-2 text-center">Không tìm thấy kết quả</p>
                  )}
                </div>
              )}

              {(() => {
                const pinnedMsgs = messages.filter((m) => m.is_pinned);
                if (pinnedMsgs.length === 0) return null;
                return (
                  <div className="z-10 sticky top-0 bg-transparent flex flex-col w-full transition-all duration-300">
                    <div 
                      className="flex items-center justify-between px-6 py-2.5 cursor-pointer hover:bg-black/5 transition-colors relative z-20" 
                      onClick={() => {
                        if (pinnedMsgs.length > 1) {
                          setIsPinnedExpanded(!isPinnedExpanded);
                        } else {
                          const lastPinned = pinnedMsgs[0];
                          if (messageRefs.current[lastPinned._id || lastPinned.id]) {
                            messageRefs.current[lastPinned._id || lastPinned.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          }
                        }
                      }}
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        <Pin className="w-3.5 h-3.5 text-[#0071E3] shrink-0" />
                        <span className="text-[13px] text-[#1D1D1F] opacity-90 truncate">
                          {pinnedMsgs[pinnedMsgs.length - 1].content || "Đính kèm"}
                        </span>
                      </div>
                      {pinnedMsgs.length > 1 && (
                        <div className="text-[#6E6E73] flex items-center gap-1 shrink-0 ml-4">
                          <span className="text-[12px] font-medium">{pinnedMsgs.length}</span>
                          <svg className={`w-3.5 h-3.5 transition-transform duration-300 ${isPinnedExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      )}
                    </div>
                    {isPinnedExpanded && pinnedMsgs.length > 1 && (
                      <div className="absolute top-full left-0 w-full bg-[#F5F5F7] flex flex-col z-50">
                        {pinnedMsgs.slice(0, -1).reverse().map((pinned) => (
                          <div 
                            key={pinned._id || pinned.id} 
                            className="flex items-center gap-2 px-6 py-2.5 cursor-pointer hover:bg-black/5 transition-colors"
                            onClick={() => {
                              if (messageRefs.current[pinned._id || pinned.id]) {
                                messageRefs.current[pinned._id || pinned.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                setIsPinnedExpanded(false);
                              }
                            }}
                          >
                            <div className="w-3.5 h-3.5 shrink-0" />
                            <span className="text-[13px] text-[#1D1D1F] opacity-90 truncate">
                              {pinned.content || "Đính kèm"}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}

              <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-6 pt-6 pb-2 bg-transparent hide-scrollbar relative">
                {loadingMsgs ? (
                  <div className="space-y-4 flex flex-col h-full justify-end pb-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"} animate-pulse`}>
                        <div className={`w-48 h-10 rounded-[18px] ${i % 2 === 0 ? "bg-[#D2D2D7]" : "bg-[#E8E8ED]"}`} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((msg, i) => {
                      const isSender = msg.sender_id === user?._id;
                      const prevMsg = i > 0 ? messages[i-1] : null;
                      const showTime = !prevMsg || (new Date(msg.created_at).getTime() - new Date(prevMsg.created_at).getTime() > 30 * 60 * 1000);
                      return (
                        <div
                          key={msg._id || msg.id || i}
                          ref={(el) => {
                            messageRefs.current[msg._id || msg.id] = el;
                          }}
                          className={`flex flex-col transition-colors duration-500 mb-2 ${isSender ? "items-end" : "items-start"}`}
                        >
                          {showTime && (
                            <div className="flex justify-center w-full my-3">
                              <span className="text-[11px] font-medium text-[#6E6E73]">
                                {formatRelativeTime(parseUTC(msg.created_at))}
                              </span>
                            </div>
                          )}
                          <div 
                            className={`group relative max-w-[85%] flex flex-col ${isSender ? "items-end" : "items-start"}`}
                            onDoubleClick={(e) => {
                              e.stopPropagation();
                              const rect = e.currentTarget.getBoundingClientRect();
                              if (activeMsgMenuId === (msg._id || msg.id)) {
                                setActiveMsgMenuId(null);
                                setActiveMsgRect(null);
                                setActiveMsgObj(null);
                                setShowDeleteSubMenu(null);
                              } else {
                                setActiveMsgMenuId(msg._id || msg.id);
                                setActiveMsgRect({ top: rect.top, left: rect.left, right: rect.right, bottom: rect.bottom, isSender });
                                setActiveMsgObj(msg);
                                setShowDeleteSubMenu(null);
                              }
                            }}
                          >
                            <div
                              className={`rounded-[18px] flex flex-col gap-2 ${
                                msg.is_recalled
                                  ? "bg-transparent border border-dashed border-[#D2D2D7] text-[#6E6E73] min-h-[38px] p-4 justify-center"
                                  : isSender
                                  ? "bg-[#0071E3] text-white p-4"
                                  : "bg-white border border-[#E8E8ED] text-[#1D1D1F] p-4"
                              } relative cursor-pointer select-none`}
                            >
                              {msg.reply_to && !msg.is_recalled && (
                                <div 
                                  onClick={() => {
                                    const replyId = typeof msg.reply_to === 'object' ? msg.reply_to._id || msg.reply_to.id : msg.reply_to;
                                    if (replyId && messageRefs.current[replyId]) {
                                      messageRefs.current[replyId]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                      messageRefs.current[replyId]?.classList.add('opacity-50');
                                      setTimeout(() => {
                                        messageRefs.current[replyId]?.classList.remove('opacity-50');
                                      }, 1500);
                                    }
                                  }}
                                  className={`text-[12px] px-2 py-1.5 rounded-[10px] truncate max-w-[250px] opacity-80 cursor-pointer hover:opacity-100 transition-opacity ${isSender ? "bg-[#0055C6] text-white" : "bg-[#E8E8ED] text-[#6E6E73]"}`}
                                >
                                  <span className="font-semibold block mb-0.5">Trích dẫn:</span>
                                  {typeof msg.reply_to === 'object' ? msg.reply_to.content : "Tin nhắn"}
                                </div>
                              )}
                              {msg.image_url && !msg.is_recalled && (
                                <img
                                  src={msg.image_url.startsWith("http") ? msg.image_url : `${API_URL}/storage/${msg.image_url}`}
                                  alt=""
                                  className="rounded-[10px] max-h-[300px] object-cover"
                                />
                              )}
                              {msg.attachments && msg.attachments.length > 0 && !msg.is_recalled && (
                                <div className="space-y-2">
                                  {msg.attachments.map((att: any, idx: number) => (
                                    <a key={idx} href={att.url.startsWith("http") ? att.url : `${API_URL}/storage/${att.url}`} target="_blank" rel="noreferrer" className={`flex items-center gap-2 p-2 rounded-[10px] ${isSender ? "bg-[#0055C6] text-white" : "bg-[#E8E8ED] text-[#1D1D1F]"}`}>
                                      <FileText className="w-5 h-5 shrink-0" />
                                      <span className="text-[13px] truncate">{att.name || "Tài liệu đính kèm"}</span>
                                    </a>
                                  ))}
                                </div>
                              )}
                              {msg.audio_url && !msg.is_recalled && (
                                <CustomAudioPlayer
                                  src={msg.audio_url.startsWith("http") ? msg.audio_url : `${API_URL}/storage/${msg.audio_url}`}
                                  isSender={isSender}
                                />
                              )}
                              {!msg.is_recalled && msg.content && msg.content !== "Tin nhắn thoại" && (
                                <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">{msg.content}</p>
                              )}
                              {msg.is_recalled && (
                                <span className="text-[13px] italic flex items-center h-full">Tin nhắn đã thu hồi</span>
                              )}
                            </div>
                            {/* Reaction badge & Time — below the bubble */}
                            <div className={`flex items-center gap-2 mt-1 ${isSender ? "flex-row-reverse mr-1" : "flex-row ml-1"}`}>
                              <span className="text-[10px] text-[#6E6E73] whitespace-nowrap">
                                {new Date(parseUTC(msg.created_at)).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                              </span>
                              {!msg.is_recalled && msg.reactions && msg.reactions.length > 0 && (
                                <div className="bg-white border border-[#D2D2D7] rounded-full px-1.5 py-0.5 text-[11px] flex items-center gap-1 shadow-sm text-[#1D1D1F]">
                                  {(() => {
                                    const counts: Record<string, number> = {};
                                    msg.reactions.forEach((r: any) => { counts[r.reaction] = (counts[r.reaction] || 0) + 1; });
                                    return Object.entries(counts).map(([emoji, count]) => (
                                      <span key={emoji} className="flex items-center gap-0.5 font-medium leading-none">
                                        <span className="text-[12px] leading-none">{emoji}</span>
                                        <span className="text-[#6E6E73] text-[11px] tabular-nums leading-none">{count}</span>
                                      </span>
                                    ));
                                  })()}
                                </div>
                              )}
                            </div>
                            {/* popup now rendered globally as fixed overlay */}
                          </div>
                        </div>
                      );
                    })}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              <div className="px-4 pb-4 pt-2 bg-transparent relative">
                {imageFiles.length > 0 && (
                  <div className="flex gap-2 mb-3 overflow-x-auto hide-scrollbar">
                    {imageFiles.map((file, idx) => {
                      let objectUrl = "";
                      const isImg = !!(file.type && file.type.startsWith("image/"));
                      if (isImg) {
                        try {
                          objectUrl = URL.createObjectURL(file);
                        } catch (err) {
                          console.error("Error creating object URL", err);
                        }
                      }
                      return (
                        <div key={idx} className="relative w-16 h-16 shrink-0 rounded-[10px] overflow-hidden border border-[#D2D2D7] bg-white flex items-center justify-center">
                          {isImg && objectUrl ? (
                            <img src={objectUrl} alt="" className="w-full h-full object-cover" />
                          ) : (
                            <FileText className="w-6 h-6 text-[#6E6E73]" />
                          )}
                          <button onClick={() => setImageFiles(prev => prev.filter((_, i) => i !== idx))} className="absolute top-1 right-1 w-5 h-5 bg-black/50 rounded-full flex items-center justify-center text-white hover:bg-black/70">
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
                <div className="flex items-center gap-3 h-[44px]">
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    multiple
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        const newFiles = Array.from(e.target.files);
                        setImageFiles(prev => [...prev, ...newFiles]);
                      }
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  />
                  <div className="flex-1 relative">
                    {isRecording ? (
                      <div className="w-full bg-[#E8E8ED] border border-transparent rounded-[980px] pl-4 pr-1.5 h-[44px] text-[15px] flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <div className={`w-2 h-2 bg-red-500 rounded-full ${!isRecordingPaused ? "animate-pulse" : ""}`} />
                          <span className="text-red-500 font-medium">
                            {isRecordingPaused ? "Tạm dừng" : "Đang ghi âm"} ({Math.floor(recordingDuration / 60)}:
                            {(recordingDuration % 60)
                              .toString()
                              .padStart(2, "0")}
                            )
                          </span>
                        </div>
                        <div className="flex items-center gap-0.5">
                          <button
                            onClick={handleTogglePauseRecording}
                            className="w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-black/5 rounded-full transition-colors"
                          >
                            {isRecordingPaused ? <Mic className="w-[18px] h-[18px]" /> : <Pause className="w-[18px] h-[18px]" />}
                          </button>
                          <button
                            onClick={handleCancelRecording}
                            className="w-8 h-8 flex items-center justify-center text-[#6E6E73] hover:text-red-500 hover:bg-black/5 rounded-full transition-colors"
                          >
                            <Trash2 className="w-[18px] h-[18px]" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10"
                        >
                          <Paperclip className="w-[18px] h-[18px]" />
                        </button>
                        <input
                          type="text"
                          value={newMessage}
                          onChange={(e) => setNewMessage(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSend();
                          }}
                          placeholder=""
                          className="w-full h-[44px] bg-white border border-transparent rounded-[980px] pl-[40px] pr-[40px] text-[15px] focus:outline-none focus:border-[#D2D2D7]"
                        />
                        <button
                          onClick={handleStartRecording}
                          className="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
                        >
                          <Mic className="w-[18px] h-[18px]" />
                        </button>
                      </>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      if (isRecording) {
                        handleStopRecording();
                      } else {
                        handleSend();
                      }
                    }}
                    disabled={!isRecording && !newMessage.trim() && imageFiles.length === 0}
                    className="w-[44px] h-[44px] flex-shrink-0 flex items-center justify-center bg-[#0071E3] text-white rounded-full hover:bg-[#0055C6] disabled:opacity-50 transition-colors"
                  >
                    <Send className="w-[20px] h-[20px] relative -left-[1px] top-[1px]" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center">
              <MessageSquare className="w-4 h-4 text-[#D2D2D7] mx-auto mb-4" />
              <p className="text-[17px] text-[#6E6E73]">
                Chọn một hội thoại để bắt đầu
              </p>
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showAliasModal} onClose={() => setShowAliasModal(false)}>
        <ModalHeader>
          <ModalTitle>Đặt biệt danh</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="mb-4">
            <input
              type="text"
              value={aliasInput}
              onChange={(e) => setAliasInput(e.target.value)}
              placeholder="Nhập biệt danh..."
              className="w-full bg-[#E8E8ED] text-[#1D1D1F] px-4 py-2.5 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3] transition-all text-[15px]"
              autoFocus
            />
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={() => setShowAliasModal(false)}
              className="px-4 py-2 text-[14px] font-medium text-[#1D1D1F] bg-[#E8E8ED] hover:bg-[#D2D2D7] rounded-full transition-colors"
            >
              Hủy
            </button>
            <button
              onClick={handleSetAlias}
              className="px-4 py-2 text-[14px] font-medium text-white bg-[#0071E3] hover:bg-[#0055C6] rounded-full transition-colors"
            >
              Lưu
            </button>
          </div>
        </ModalContent>
      </Modal>

      {/* ====== Global tapback popup (fixed, smart above/below) ====== */}
      {activeMsgMenuId && activeMsgRect && activeMsgObj && (() => {
        const msgId = activeMsgObj._id || activeMsgObj.id;
        const isRecalled = activeMsgObj.is_recalled;
        const isSender = activeMsgRect.isSender;

        // Estimate popup height: emoji pill (46px) + gap (8px) + actions (~200px)
        const emojiH = isRecalled ? 0 : 54;
        const actionsH = isRecalled ? 60 : (isSender ? 240 : 185);
        const totalH = emojiH + (isRecalled ? 0 : 8) + actionsH + 12;

        const spaceBelow = window.innerHeight - activeMsgRect.bottom;
        const showAbove = spaceBelow < totalH && activeMsgRect.top > totalH;

        const hPos = isSender
          ? { right: window.innerWidth - activeMsgRect.right }
          : { left: activeMsgRect.left };

        const vPos = showAbove
          ? { bottom: window.innerHeight - activeMsgRect.top + 8 }
          : { top: activeMsgRect.bottom + 8 };

        const dismiss = () => {
          setActiveMsgMenuId(null);
          setActiveMsgRect(null);
          setActiveMsgObj(null);
          setShowDeleteSubMenu(null);
        };

        return (
          <>
            {/* Backdrop */}
            <div className="fixed inset-0 z-40 bg-black/25 backdrop-blur-[2px]" onClick={dismiss} />

            {/* Cloned Message Group (elevates exactly above original) */}
            <div 
              style={{
                position: 'fixed',
                top: activeMsgRect.top,
                left: activeMsgRect.left,
                width: activeMsgRect.right - activeMsgRect.left,
                zIndex: 55
              }}
              className={`flex flex-col ${isSender ? "items-end" : "items-start"}`}
              onClick={dismiss}
            >
               <div
                  className={`rounded-[18px] flex flex-col gap-2 p-4 ${
                    activeMsgObj.is_recalled
                      ? "bg-white/90 border border-dashed border-[#D2D2D7] text-[#6E6E73] justify-center min-h-[38px]"
                      : isSender
                      ? "bg-[#0071E3] text-white"
                      : "bg-white border border-[#E8E8ED] text-[#1D1D1F]"
                  } cursor-pointer select-none shadow-2xl`}
                >
                  {activeMsgObj.reply_to && !activeMsgObj.is_recalled && (
                    <div className={`text-[12px] px-2 py-1.5 rounded-[10px] truncate opacity-80 ${isSender ? "bg-[#0055C6] text-white" : "bg-[#E8E8ED] text-[#6E6E73]"}`}>
                      <span className="font-semibold block mb-0.5">Trích dẫn:</span>
                      {typeof activeMsgObj.reply_to === 'object' ? activeMsgObj.reply_to.content : "Tin nhắn"}
                    </div>
                  )}
                  {activeMsgObj.image_url && !activeMsgObj.is_recalled && (
                    <img src={activeMsgObj.image_url.startsWith("http") ? activeMsgObj.image_url : `${API_URL}/storage/${activeMsgObj.image_url}`} alt="" className="rounded-[10px] max-h-[300px] object-cover" />
                  )}
                  {activeMsgObj.attachments && activeMsgObj.attachments.length > 0 && !activeMsgObj.is_recalled && (
                    <div className="space-y-2">
                      {activeMsgObj.attachments.map((att: any, idx: number) => (
                        <div key={idx} className={`flex items-center gap-2 p-2 rounded-[10px] ${isSender ? "bg-[#0055C6] text-white" : "bg-[#E8E8ED] text-[#1D1D1F]"}`}>
                          <FileText className="w-5 h-5 shrink-0" />
                          <span className="text-[13px] truncate">{att.name || "Tài liệu đính kèm"}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {activeMsgObj.audio_url && !activeMsgObj.is_recalled && (
                    <div className={`text-[13px] ${isSender ? "text-white/80" : "text-[#6E6E73]"}`}>[Tin nhắn thoại]</div>
                  )}
                  {!activeMsgObj.is_recalled && activeMsgObj.content && activeMsgObj.content !== "Tin nhắn thoại" && (
                    <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">{activeMsgObj.content}</p>
                  )}
                  {activeMsgObj.is_recalled && (
                    <span className="text-[13px] italic flex items-center h-full">Tin nhắn đã thu hồi</span>
                  )}
               </div>
               
               <div className={`flex items-center gap-2 mt-1 ${isSender ? "flex-row-reverse mr-1" : "flex-row ml-1"}`}>
                  <span className="text-[10px] text-white font-medium whitespace-nowrap drop-shadow-md">
                    {new Date(parseUTC(activeMsgObj.created_at)).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  {!activeMsgObj.is_recalled && activeMsgObj.reactions && activeMsgObj.reactions.length > 0 && (
                    <div className="bg-white border border-[#D2D2D7] rounded-full px-1.5 py-0.5 text-[11px] flex items-center gap-1 shadow-md text-[#1D1D1F]">
                      {(() => {
                        const counts: Record<string, number> = {};
                        activeMsgObj.reactions.forEach((r: any) => { counts[r.reaction] = (counts[r.reaction] || 0) + 1; });
                        return Object.entries(counts).map(([emoji, count]) => (
                          <span key={emoji} className="flex items-center gap-0.5 font-medium leading-none">
                            <span className="text-[12px] leading-none">{emoji}</span>
                            <span className="text-[#6E6E73] text-[11px] tabular-nums leading-none">{count}</span>
                          </span>
                        ));
                      })()}
                    </div>
                  )}
               </div>
            </div>

            {/* Unified popup container — flex direction flips for above/below */}
            <div
              style={{ position: "fixed", zIndex: 60, ...hPos, ...vPos }}
              className={`flex w-max gap-2 ${showAbove ? "flex-col-reverse" : "flex-col"}`}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Emoji pill */}
              {!isRecalled && (
                <div className="flex items-center gap-1 bg-white/95 backdrop-blur-md border border-[#E8E8ED] rounded-full px-3 py-2 shadow-[0_8px_32px_rgba(0,0,0,0.18)] self-start">
                  {["❤️", "👍", "😂", "😮", "😢", "🙏"].map((emoji) => (
                    <button
                      key={emoji}
                      onClick={() => { handleAddReaction(msgId, emoji); dismiss(); }}
                      className="text-[22px] hover:scale-125 transition-transform duration-150 active:scale-110 px-1"
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              )}

              {/* Action panel */}
              <div className="flex flex-col bg-white/95 backdrop-blur-md border border-[#E8E8ED] rounded-[16px] shadow-[0_8px_32px_rgba(0,0,0,0.15)] overflow-hidden">
                {!isRecalled && (
                  <button
                    onClick={() => { setReplyingTo(activeMsgObj); dismiss(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    <Reply className="w-[18px] h-[18px] text-[#6E6E73]" />
                    Trả lời
                  </button>
                )}
                {!isRecalled && (
                  <button
                    onClick={() => { handlePin(msgId); dismiss(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    {activeMsgObj.is_pinned ? <PinOff className="w-[18px] h-[18px] text-[#6E6E73]" /> : <Pin className="w-[18px] h-[18px] text-[#6E6E73]" />}
                    {activeMsgObj.is_pinned ? "Bỏ ghim" : "Ghim"}
                  </button>
                )}
                {!isRecalled && isSender && (
                  <button
                    onClick={() => { setEditingMsg(activeMsgObj); setNewMessage(activeMsgObj.content); dismiss(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    <Edit2 className="w-[18px] h-[18px] text-[#6E6E73]" />
                    Chỉnh sửa
                  </button>
                )}
                <button
                  onClick={() => setShowDeleteSubMenu(showDeleteSubMenu === msgId ? null : msgId)}
                  className={`flex items-center justify-between gap-3 w-full px-4 py-3 text-[15px] text-red-500 hover:bg-[#FFF5F5] text-left transition-colors ${showDeleteSubMenu === msgId ? "border-b border-[#F2F2F7]" : ""}`}
                >
                  <div className="flex items-center gap-3">
                    <Trash2 className="w-[18px] h-[18px]" />
                    Xóa
                  </div>
                  <ChevronRight className={`w-4 h-4 transition-transform duration-150 ${showDeleteSubMenu === msgId ? "rotate-90" : ""}`} />
                </button>
                {showDeleteSubMenu === msgId && (
                  <div className="overflow-hidden">
                    {isSender && !isRecalled && (
                      <button
                        onClick={() => { handleRecall(msgId); dismiss(); }}
                        className="flex items-center gap-3 w-full px-5 py-2.5 text-[14px] text-orange-500 hover:bg-orange-50 border-b border-[#F2F2F7] text-left transition-colors"
                      >
                        <Undo2 className="w-[15px] h-[15px]" />
                        Xóa cả hai
                      </button>
                    )}
                    <button
                      onClick={() => { handleDeleteForMe(msgId); dismiss(); }}
                      className="flex items-center gap-3 w-full px-5 py-2.5 text-[14px] text-red-500 hover:bg-[#FFF5F5] text-left transition-colors"
                    >
                      <Trash2 className="w-[15px] h-[15px]" />
                      Xóa phía tôi
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        );
      })()}
    </div>
  );
}
