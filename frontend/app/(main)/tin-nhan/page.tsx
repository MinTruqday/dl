"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/Auth";
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
} from "@/services/chat.service";
import { searchUsersAPI } from "@/services/user.service";
import { getMyDocumentsAPI } from "@/services/document.service";
import { API_URL, WS_URL, getToken } from "@/services/authentication.service";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
} from "@/components/ui/Modal";
import {
  ImageIcon,
  Quote,
  PenTool,
  Book,
  Loader2,
  ArrowLeft,
  Search,
  Plus,
  MessageSquare,
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
  MicOff,
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
} from "lucide-react";
import { useRouter } from "next/navigation";
import { parseUTC } from "@/lib/utils";

const CustomAudioPlayer = ({ src, isSender }: { src: string, isSender: boolean }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setProgress((audioRef.current.currentTime / (audioRef.current.duration || 1)) * 100);
    }
  };

  const formatTime = (time: number) => {
    if (!time || isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className={`flex items-center gap-3 w-full rounded-full py-1 min-w-[200px]`}>
      <button onClick={togglePlay} className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${isSender ? "bg-white text-black" : "bg-black text-white"}`}>
        {isPlaying ? <Pause size={14} className="fill-current" /> : <Play size={14} className="ml-0.5 fill-current" />}
      </button>
      <div className="flex-1 flex items-center gap-3">
        <div className="flex-1 h-1.5 rounded-full relative overflow-hidden" style={{ background: isSender ? 'rgba(255,255,255,0.3)' : 'rgba(0,0,0,0.1)' }}>
          <div className="absolute top-0 left-0 h-full rounded-full transition-all duration-100 ease-linear" style={{ width: `${progress}%`, background: isSender ? 'white' : 'black' }}></div>
        </div>
        <span className="text-[11px] font-medium opacity-80 min-w-[32px] text-right">
          {formatTime(audioRef.current?.currentTime || 0)}
        </span>
      </div>
      <audio 
        ref={audioRef} 
        src={src} 
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => { setIsPlaying(false); setProgress(100); }}
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
  const [visible, setVisible] = useState(false);

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
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showConvMenu, setShowConvMenu] = useState(false);
  const recordTimerRef = useRef<any>(null);
  const cancelRecordingRef = useRef(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

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
    if (!authLoading && !user) {
      router.push("/dang-nhap");
    }
    if (!authLoading && user) {
      loadConversations();
      requestAnimationFrame(() => setVisible(true));
    }
  }, [authLoading, user, router, loadConversations]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, selectedConv?.other_user_id]);

  const socketRef = useRef<WebSocket | null>(null);

  const updateConversationInPlace = useCallback((senderId: string, messageData: any) => {
    setConversations(prev => {
      const idx = prev.findIndex(c => c.other_user_id === senderId);
      if (idx === -1) return prev;
      const updated = [...prev];
      const conv = { ...updated[idx] };
      conv.last_message = messageData;
      if (selectedConvRef.current?.other_user_id !== senderId) {
        conv.unread_count = (conv.unread_count || 0) + 1;
      }
      updated.splice(idx, 1);
      updated.unshift(conv);
      return updated;
    });
  }, []);

  useEffect(() => {
    if (!user?._id) return;

    const wsUrl = `${WS_URL}/tro-chuyen/ws/${user._id}?token=${getToken()}`;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      const lastMsgId = localStorage.getItem(`last_msg_id_${user._id}`);
      if (lastMsgId) {
        socket.send(JSON.stringify({ action: "sync", data: { last_message_id: lastMsgId } }));
      }
    };

    const pingInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "ping" }));
      }
    }, 30000);

    socket.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);

        if (type === "new_message") {
          if (selectedConvRef.current && (data.sender_id === selectedConvRef.current.other_user_id)) {
            setMessages(prev => {
              if (prev.some(m => (m._id || m.id) === (data._id || data.id))) return prev;
              return [...prev, data];
            });
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
              socketRef.current.send(JSON.stringify({
                action: "mark_read",
                data: { other_user_id: selectedConvRef.current.other_user_id }
              }));
            }
          }
          updateConversationInPlace(data.sender_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_sent_ack") {
          setMessages(prev => {
            if (prev.some(m => (m._id || m.id) === (data._id || data.id))) return prev;
            return [...prev, data];
          });
          updateConversationInPlace(data.receiver_id, data);
          localStorage.setItem(`last_msg_id_${user._id}`, data._id || data.id);
        } else if (type === "message_edited") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
          setConversations(prev => prev.map(c => {
            if (c.last_message && (c.last_message._id || c.last_message.id) === (data._id || data.id)) {
              return { ...c, last_message: { ...c.last_message, content: data.content } };
            }
            return c;
          }));
        } else if (type === "message_pinned") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "message_recalled") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
          setConversations(prev => prev.map(c => {
            if (c.last_message && (c.last_message._id || c.last_message.id) === (data._id || data.id)) {
              return { ...c, last_message: { ...c.last_message, content: data.content, is_recalled: true } };
            }
            return c;
          }));
        } else if (type === "message_reaction") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "messages_read") {
          setMessages(prev => prev.map(m => m.sender_id === data.reader_id ? { ...m, is_read: true } : m));
        } else if (type === "message_translated") {
          setMessages(prev => prev.map(m => (m._id || m.id) === data.message_id ? { ...m, translated_content: data.translated_content } : m));
        } else if (type === "typing_indicator") {
        } else if (type === "conversation_settings_updated") {
          if (selectedConvRef.current) {
            setSelfDestructSeconds(data.self_destruct_seconds || 0);
          }
        }
      } catch (err) {
        console.error("WS Error:", err);
      }
    };

    return () => {
      clearInterval(pingInterval);
      socketRef.current = null;
      socket.close();
    };
  }, [user?._id, updateConversationInPlace]);

  const selectConversation = async (conv: any) => {
    if (selectedConvRef.current && newMessage.trim()) {
      await saveDraftAPI(selectedConvRef.current.other_user_id, newMessage.trim());
    }

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
    setShowConvMenu(false);

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

      setConversations(prev => prev.map(c =>
        c.other_user_id === conv.other_user_id ? { ...c, unread_count: 0 } : c
      ));
    } catch (err: any) {
      showToast("Không thể truy xuất lịch sử tin nhắn.", "error");
    } finally {
      setLoadingMsgs(false);
    }
  };

  const handleSend = async () => {
    if (isBlocked) {
      showToast("Không thể gửi tin nhắn khi bị chặn hoặc đang chặn người dùng này.", "error");
      return;
    }
    if ((!newMessage.trim() && !imageFile) || !selectedConv || sending) return;

    if (editingMsg) {
      setSending(true);
      try {
        await editMessageAPI(editingMsg._id || editingMsg.id, newMessage.trim());
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
        showToast(err.message || "Chỉnh sửa thất bại.", "error");
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
        const resUpload = await fetch(`${API_URL}/tai-len/tap-tin`, {
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
      
      const attachRes = await getSharedAttachmentsAPI(selectedConv.other_user_id);
      setSharedAttachments(attachRes.data || attachRes || []);
    } catch (err: any) {
      showToast("Gửi tin nhắn thất bại. Vui lòng kiểm tra kết nối.", "error");
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
          const ext = mimeType.includes("mp4") ? "m4a" : mimeType.includes("ogg") ? "ogg" : "webm";
          const blob = new Blob(chunks, { type: mimeType });
          const file = new File([blob], `voice.${ext}`, { type: mimeType });
          const formData = new FormData();
          formData.append("file", file);

          const resUpload = await fetch(`${API_URL}/tai-len/tap-tin`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}` },
            body: formData,
          });
          const uploadData = await resUpload.json();
          const audioUrl = uploadData.data.url;

          const res = await sendMessageAPI(selectedConv.other_user_id, "Tin nhắn thoại", undefined, undefined, audioUrl);
          const msg = res.data || res;
          setMessages((prev) => [...prev, msg]);
          updateConversationInPlace(selectedConv.other_user_id, msg);
        } catch (err) {
          showToast("Lỗi gửi tin nhắn thoại.", "error");
        } finally {
          setSending(false);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingDuration(0);
      recordTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err) {
      showToast("Không thể khởi động bộ thu âm micro.", "error");
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
      el.classList.add("bg-zinc-100");
      setTimeout(() => el.classList.remove("bg-zinc-100"), 2000);
    }
  };

  const handlePin = async (messageId: string) => {
    try {
      await togglePinAPI(messageId);
      setMessages((prev) => {
        const newMsgs = prev.map((m) =>
          (m._id || m.id) === messageId ? { ...m, is_pinned: !m.is_pinned } : m,
        );
        if (selectedConv) {
          const pinned = newMsgs.filter(m => m.is_pinned);
          setSelectedConv({ ...selectedConv, pinned_messages: pinned });
        }
        return newMsgs;
      });
    } catch (err: any) {
      showToast("Thao tác ghim thất bại.", "error");
    }
  };

  const handleRecall = async (messageId: string) => {
    try {
      await recallMessageAPI(messageId);
      setMessages((prev) =>
        prev.map((m) =>
          (m._id || m.id) === messageId
            ? { ...m, is_recalled: true, content: "Tin nhắn đã bị thu hồi" }
            : m,
        ),
      );
      showToast("Đã thu hồi tin nhắn.", "success");
      setConversations(prev => prev.map(c => {
        if (c.last_message && (c.last_message._id || c.last_message.id) === messageId) {
          return { ...c, last_message: { ...c.last_message, content: "Tin nhắn đã bị thu hồi", is_recalled: true } };
        }
        return c;
      }));
    } catch (err: any) {
      showToast(err.message || "Thu hồi thất bại.", "error");
    }
  };

  const handleSearchMessages = async (q: string) => {
    setSearchMsgQuery(q);
    if (!selectedConv || q.length < 1) {
      setSearchedMsgResults([]);
      return;
    }
    const results = messages.filter(m => 
      m.content && 
      !m.is_recalled && 
      m.content.toLowerCase().includes(q.toLowerCase())
    );
    setSearchedMsgResults(results);
  };

  const handleAddReaction = async (messageId: string, reaction: string) => {
    try {
      const msg = messages.find(m => (m._id || m.id) === messageId);
      const existingReaction = msg?.reactions?.find((r: any) => r.user_id === user?._id);
      const finalReaction = existingReaction?.reaction === reaction ? "" : reaction;

      const res = await addReactionAPI(messageId, finalReaction);
      const updated = res.data || res;
      setMessages((prev) =>
        prev.map((m) =>
          (m._id || m.id) === messageId ? { ...m, reactions: updated.reactions } : m
        )
      );
    } catch (err: any) {
      showToast(err.message || "Không thể gửi cảm xúc.", "error");
    }
  };

  const openShareDoc = async () => {
    setShowShareDocModal(true);
    setLoadingShareDocs(true);
    try {
      const docsRes = await getMyDocumentsAPI();
      setMyDocsForShare(docsRes.data || docsRes || []);
    } catch (err: any) {
      console.warn("Failed to load documents for sharing", err.message || err);
    }
    setLoadingShareDocs(false);
  };

  const handleShareDoc = async (docId: string) => {
    if (!selectedConv) return;
    try {
      const res = await shareDocumentAPI(selectedConv.other_user_id, docId);
      const newMsg = res.data || res;
      setMessages((prev) => [...prev, newMsg]);
      setShowShareDocModal(false);
      showToast("Đã chia sẻ liên kết tài liệu.", "success");
      updateConversationInPlace(selectedConv.other_user_id, newMsg);
      
      const attachRes = await getSharedAttachmentsAPI(selectedConv.other_user_id);
      setSharedAttachments(attachRes.data || attachRes || []);
    } catch (err: any) {
      showToast("Lỗi chia sẻ tài liệu.", "error");
    }
  };

  const handleBlockUser = async () => {
    if (!selectedConv) return;
    try {
      if (isBlocked) {
        await unblockUserAPI(selectedConv.other_user_id);
        setIsBlocked(false);
        showToast("Đã bỏ chặn liên lạc.", "success");
      } else {
        await blockUserAPI(selectedConv.other_user_id);
        setIsBlocked(true);
        showToast("Đã chặn liên lạc người dùng này.", "success");
      }
    } catch (err: any) {
      showToast("Thao tác thất bại.", "error");
    }
  };

  const handleTogglePinConv = async (otherId: string) => {
    try {
      const res = await togglePinConversationAPI(otherId);
      const status = res.data || res;
      showToast(status.is_pinned ? "Đã ghim cuộc trò chuyện." : "Đã bỏ ghim cuộc trò chuyện.", "success");
      setActiveConvMenuId(null);
    } catch (err: any) {
      showToast("Không thể thay đổi trạng thái ghim.", "error");
    }
  };

  const handleMarkAsRead = async (otherUserId: string) => {
    try {
      await markAsReadAPI(otherUserId);
      setConversations(prev => prev.map(c =>
        c.other_user_id === otherUserId ? { ...c, unread_count: 0 } : c
      ));
      setActiveConvMenuId(null);
    } catch (err) {
      showToast("Không thể đánh dấu đã đọc", "error");
    }
  };

  const handleDeleteConv = async (otherUserId: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa cuộc hội thoại này? (Nhóm sẽ bị rời)")) return;
    try {
      await deleteConversationAPI(otherUserId);
      if (selectedConv?.other_user_id === otherUserId) {
        setSelectedConv(null);
      }
      setConversations(prev => prev.filter(c => c.other_user_id !== otherUserId));
      setActiveConvMenuId(null);
      showToast("Đã xóa cuộc hội thoại", "success");
    } catch (err) {
      showToast("Không thể xóa cuộc hội thoại", "error");
    }
  };

  const handleTranslate = async (messageId: string, lang: string) => {
    try {
      const res = await translateMessageAPI(messageId, lang);
      const data = res.data || res;
      setMessages(prev => prev.map(m => (m._id || m.id) === messageId ? { ...m, translated_content: data.translated_content } : m));
      showToast("Đã phiên dịch tin nhắn.", "success");
    } catch (err: any) {
      showToast("Không thể dịch tin nhắn này.", "error");
    }
  };

  const handleToggleMute = async () => {
    if (!selectedConv) return;
    try {
      const res = await toggleMuteAPI(selectedConv.other_user_id);
      const status = res.data || res;
      setIsMuted(status.is_muted);
      showToast(status.is_muted ? "Đã tắt âm thông báo cuộc trò chuyện." : "Đã bật âm thông báo cuộc trò chuyện.", "success");
    } catch (err: any) {
      showToast("Không thể điều chỉnh tắt âm.", "error");
    }
  };

  const handleUpdateSelfDestruct = async (seconds: number) => {
    if (!selectedConv) return;
    try {
      await toggleSelfDestructAPI(selectedConv.other_user_id, seconds);
      setSelfDestructSeconds(seconds);
      setShowSelfDestructMenu(false);
      showToast(seconds > 0 ? `Đã thiết lập tin nhắn tự hủy sau ${seconds} giây.` : "Đã tắt chế độ tin nhắn tự hủy.", "success");
    } catch (err: any) {
      showToast("Cài đặt tự hủy thất bại.", "error");
    }
  };

  const openGroupModal = async () => {
    setShowGroupModal(true);
    setLoadingGroupUsers(true);
    try {
      const res = await searchUsersAPI("a");
      setAllUsersForGroup(res.data || res || []);
    } catch (err: any) {
      console.warn("Failed to load users for group", err.message || err);
    }
    setLoadingGroupUsers(false);
  };

  const handleCreateGroup = async () => {
    if (!groupName.trim()) {
      showToast("Vui lòng nhập tên nhóm.", "error");
      return;
    }
    try {
      const res = await createGroupAPI(groupName.trim(), selectedMembers);
      const created = res.data || res;
      showToast("Tạo nhóm thảo luận thành công.", "success");
      setShowGroupModal(false);
      setGroupName("");
      setSelectedMembers([]);
      loadConversations();
      
      const newGroupConv = {
        other_user_id: created._id || created.id,
        other_user: {
          username: created.group_name,
          full_name: created.group_name,
          avatar_url: "",
          is_group: true
        },
        last_message: null,
        pinned_messages: [],
        unread_count: 0
      };
      
      selectConversation(newGroupConv);
    } catch (err: any) {
      showToast("Tạo nhóm thất bại.", "error");
    }
  };

  const handleSearchUsers = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const res = await searchUsersAPI(q);
      setSearchResults(res.data || res || []);
    } catch (err: any) {
      showToast("Tìm kiếm người dùng thất bại.", "error");
    } finally {
      setSearching(false);
    }
  };

  const startNewChat = (otherUser: any) => {
    const otherUserId = otherUser._id || otherUser.id;
    const existing = conversations.find((c) => c.other_user_id === otherUserId);
    if (existing) {
      selectConversation(existing);
    } else {
      setSelectedConv({
        other_user_id: otherUserId,
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
    const aPinned = user?.pinned_conversations?.includes(a.other_user_id) ? 1 : 0;
    const bPinned = user?.pinned_conversations?.includes(b.other_user_id) ? 1 : 0;
    if (aPinned !== bPinned) return bPinned - aPinned;
    return new Date(b.last_message?.created_at || 0).getTime() - new Date(a.last_message?.created_at || 0).getTime();
  });

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col font-sans text-black selection:bg-black selection:text-white">
      <Modal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        className="max-w-xl rounded-2xl border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="p-6 border-b border-zinc-200">
          <ModalTitle className="text-sm font-semibold text-black flex items-center gap-2">
            Bắt đầu hội thoại mới
          </ModalTitle>
        </ModalHeader>

        <ModalContent className="p-6 space-y-6">
          <div className="relative">
            <input
              value={searchQuery}
              onChange={(e) => handleSearchUsers(e.target.value)}
              placeholder="Nhập tên người dùng"
              className="w-full h-10 px-4 bg-zinc-50 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-2xl"
            />
          </div>

          <div className="max-h-[300px] overflow-y-auto space-y-2">
            {searching ? (
              <div className="py-12 flex flex-col items-center gap-4">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                <span className="text-xs font-medium text-zinc-500">Đang tìm kiếm</span>
              </div>
            ) : searchResults.length > 0 ? (
              searchResults.map((u) => (
                <div
                  key={u._id || u.id}
                  onClick={() => startNewChat(u)}
                  className="flex items-center justify-between p-3 border border-zinc-200 cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center overflow-hidden bg-white shrink-0 rounded-full">
                      {u.avatar_url ? (
                        <img
                          src={u.avatar_url}
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                          alt=""
                        />
                      ) : (
                        <User className="w-5 h-5 text-zinc-400 stroke-[1]" />
                      )}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold text-black">
                        {u.full_name || u.username}
                      </span>
                      <span className="text-[10px] font-medium text-zinc-500">
                        ID: {u.slug || u.username}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-zinc-400" />
                </div>
              ))
            ) : searchQuery.length >= 2 ? (
              <div className="text-center py-12 border border-dashed border-zinc-200 bg-zinc-50">
                <p className="text-xs font-medium text-zinc-500">Không tìm thấy kết quả</p>
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="w-8 h-8 mx-auto text-zinc-200 mb-3" />
                <p className="text-xs font-medium text-zinc-400">Khởi tạo tìm kiếm để bắt đầu</p>
              </div>
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showGroupModal}
        onClose={() => setShowGroupModal(false)}
        className="max-w-md rounded-2xl border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="border-b border-zinc-200">
          <ModalTitle className="text-sm font-semibold text-black flex items-center gap-2">
            Tạo nhóm thảo luận
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-black uppercase">Tên nhóm thảo luận</label>
            <input
              type="text"
              placeholder="Nhập tên nhóm..."
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              className="w-full h-10 px-3 border border-zinc-200 bg-zinc-50 text-xs font-medium focus:outline-none focus:border-black rounded-2xl"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-black uppercase block">Chọn thành viên</label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-zinc-200 p-2">
              {loadingGroupUsers ? (
                <div className="py-6 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                </div>
              ) : allUsersForGroup.length > 0 ? (
                allUsersForGroup.map((u) => (
                  <div key={u._id || u.id} className="flex items-center gap-2 p-1.5 ">
                    <input
                      type="checkbox"
                      checked={selectedMembers.includes(u._id || u.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedMembers([...selectedMembers, u._id || u.id]);
                        } else {
                          setSelectedMembers(selectedMembers.filter(id => id !== (u._id || u.id)));
                        }
                      }}
                      className="accent-black rounded-2xl"
                    />
                    <span className="text-xs font-medium text-black">{u.full_name || u.username}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-zinc-400 py-3 text-center">Không tìm thấy tác giả nào</p>
              )}
            </div>
          </div>
          <button
            onClick={handleCreateGroup}
            className="w-full h-10 bg-black text-white text-xs font-semibold rounded-2xl"
          >
            Khởi tạo nhóm
          </button>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showShareDocModal}
        onClose={() => setShowShareDocModal(false)}
        className="max-w-xl rounded-2xl border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="p-6 border-b border-zinc-200">
          <ModalTitle className="text-sm font-semibold text-black flex items-center gap-2">
            Chia sẻ tài liệu sáng tác
          </ModalTitle>
          <ModalDescription className="text-xs text-zinc-500 font-medium mt-1">
            Chọn tài liệu cá nhân để đính kèm gửi trực tiếp qua cuộc trò chuyện
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6 max-h-[350px] overflow-y-auto space-y-2">
          {loadingShareDocs ? (
            <div className="py-12 flex flex-col items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
            </div>
          ) : myDocsForShare.length > 0 ? (
            myDocsForShare.map((doc) => (
              <div
                key={doc._id || doc.id}
                onClick={() => handleShareDoc(doc._id || doc.id)}
                className="p-3 border border-zinc-200 bg-zinc-50 cursor-pointer flex justify-between items-center"
              >
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-black">{doc.title}</span>
                  <span className="text-[9px] font-mono text-zinc-400">Định dạng: {doc.format || "TXT"}</span>
                </div>
                <Share2 className="w-4 h-4 text-zinc-400" />
              </div>
            ))
          ) : (
            <p className="text-xs text-zinc-400 py-6 text-center">Bạn chưa có tài liệu sáng tác nào để chia sẻ</p>
          )}
        </ModalContent>
      </Modal>

      <div className="flex flex-1 min-h-0 gap-4">
        <div
          className={`w-full md:w-[320px] lg:w-[380px] bg-white border border-zinc-200 rounded-2xl shadow-sm flex flex-col overflow-hidden shrink-0 self-start max-h-full animate-in fade-in slide-in-from-bottom-8 duration-300 ${selectedConv ? "hidden md:flex" : "flex"
            }`}
        >
          <div className="p-5 flex items-center justify-between shrink-0">
            <h2 className="text-lg font-semibold text-black">Hộp thư</h2>
            <div className="flex items-center gap-3">
              <button onClick={openGroupModal} className="p-1.5 border border-transparent rounded-xl text-zinc-500 hover:text-black hover:bg-zinc-100 transition-all" title="Tạo nhóm thảo luận">
                <Users className="w-4 h-4" />
              </button>
              <button onClick={() => setShowNewChatModal(true)} className="p-1.5 border border-transparent rounded-xl text-zinc-500 hover:text-black hover:bg-zinc-100 transition-all" title="Bắt đầu kết nối">
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="overflow-y-auto px-5 pb-5 pt-1 flex flex-col gap-2 overflow-x-hidden min-h-0 animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>
            {loadingConv ? (
              <div className="p-12 flex flex-col items-center gap-4">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                <span className="text-xs font-medium text-zinc-500">Đang đồng bộ</span>
              </div>
            ) : sortedConversations.length > 0 ? (
              sortedConversations.map((conv) => {
                const isConvPinned = user?.pinned_conversations?.includes(conv.other_user_id);
                return (
                  <div
                    key={conv.other_user_id}
                    onClick={() => selectConversation(conv)}
                    className={`p-3 rounded-2xl cursor-pointer flex items-center gap-3 group relative transition-colors ${selectedConv?.other_user_id === conv.other_user_id
                        ? "bg-zinc-100"
                        : "hover:bg-zinc-50"
                      }`}
                  >
                    <div className="w-10 h-10 bg-white border border-zinc-200 flex items-center justify-center shrink-0 overflow-hidden rounded-full">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <User className="w-4 h-4 text-zinc-400 stroke-[1]" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                      <div className="flex justify-between items-center mb-1">
                        <span className={`text-sm text-black truncate flex items-center gap-1.5 ${conv.unread_count > 0 ? "font-semibold" : "font-medium"}`}>
                          {conv.other_user?.full_name || conv.other_user?.username}
                          {isConvPinned && <Pin className="w-3.5 h-3.5 text-black shrink-0 fill-current" />}
                        </span>
                        <span className={`text-[10px] shrink-0 ${conv.unread_count > 0 ? "text-black font-semibold" : "text-zinc-500 font-medium"}`}>
                          {conv.last_message?.created_at
                            ? parseUTC(conv.last_message.created_at).toLocaleTimeString("vi-VN", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                            : ""}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-xs truncate ${conv.unread_count > 0 ? "text-black font-semibold" : "text-zinc-500 font-medium"}`}>
                          {conv.last_message?.content || "Chưa có tin nhắn"}
                        </p>
                        <div className="flex items-center gap-1.5 relative">
                          {conv.unread_count > 0 && activeConvMenuId !== conv.other_user_id && (
                            <div className="w-2 h-2 bg-black shrink-0 rounded-2xl"></div>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveConvMenuId(activeConvMenuId === conv.other_user_id ? null : conv.other_user_id);
                            }}
                            className="p-1 text-zinc-400 hover:text-black transition-colors block"
                          >
                            <MoreVertical className="w-4 h-4" />
                          </button>
                          {activeConvMenuId === conv.other_user_id && (
                            <div className="absolute right-0 top-full mt-1 w-40 bg-white border border-zinc-200 rounded-2xl shadow-lg z-50 overflow-hidden flex flex-col py-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTogglePinConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                {isConvPinned ? <PinOff className="w-3.5 h-3.5" /> : <Pin className="w-3.5 h-3.5" />}
                                {isConvPinned ? "Bỏ ghim" : "Ghim"}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMarkAsRead(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-50 text-zinc-700 flex items-center gap-2 transition-colors"
                              >
                                <CheckCheck className="w-3.5 h-3.5" /> Đã đọc
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteConv(conv.other_user_id);
                                }}
                                className="w-full text-left px-3 py-2 text-xs hover:bg-red-50 text-red-600 flex items-center gap-2 transition-colors"
                              >
                                <Trash2 className="w-3.5 h-3.5" /> Xóa
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
              <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl">
                <p className="text-sm font-medium text-zinc-500">Hộp thư rỗng</p>
              </div>
            )}
          </div>
        </div>

        <div className={`flex-1 flex flex-col min-w-0 ${!selectedConv ? "hidden md:flex" : "flex"}`}>
          {selectedConv ? (
            <div className="flex-1 flex flex-col bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 overflow-hidden gap-4 animate-in fade-in slide-in-from-bottom-8 duration-300">
              <div className="flex items-center justify-between shrink-0 relative z-30">
                  <div className="flex items-center gap-4">
                    <button onClick={() => setSelectedConv(null)} className="md:hidden p-2 text-zinc-500">
                      <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="w-10 h-10 border border-zinc-200 overflow-hidden bg-white flex items-center justify-center relative rounded-full">
                      {selectedConv.other_user?.avatar_url ? (
                        <img
                          src={selectedConv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <User className="w-5 h-5 text-zinc-400 stroke-[1]" />
                      )}
                      <div className={`absolute bottom-0 right-0 w-2.5 h-2.5 border-2 border-white rounded-2xl ${isOnline ? "bg-black" : "bg-zinc-300"}`} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm text-black flex items-center gap-1.5">
                        {selectedConv.other_user?.full_name || selectedConv.other_user?.username}
                        <span className="text-[10px] font-normal text-zinc-400">({isOnline ? "Trực tuyến" : "Ngoại tuyến"})</span>
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 relative">
                    {showConvMenu && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setShowConvMenu(false); setShowSelfDestructMenu(false); }} />
                        <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-zinc-200 rounded-2xl shadow-lg py-1 z-50">
                        <button
                          onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center justify-between"
                        >
                          <div className="flex items-center gap-2.5">
                            <Flame className={`w-4 h-4 ${selfDestructSeconds > 0 ? "text-red-500" : ""}`} />
                            Tin nhắn tự hủy
                          </div>
                          {selfDestructSeconds > 0 && <span className="text-[10px] font-medium text-red-500">{selfDestructSeconds}s</span>}
                        </button>
                        {showSelfDestructMenu && (
                          <div className="bg-zinc-50 border-y border-zinc-100 flex flex-col text-left text-xs">
                            <button onClick={() => { handleUpdateSelfDestruct(0); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">Tắt tự hủy</button>
                            <button onClick={() => { handleUpdateSelfDestruct(5); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">5 giây</button>
                            <button onClick={() => { handleUpdateSelfDestruct(60); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">1 phút</button>
                            <button onClick={() => { handleUpdateSelfDestruct(3600); setShowConvMenu(false); }} className="px-9 py-2 hover:bg-zinc-100">1 giờ</button>
                          </div>
                        )}

                        <button
                          onClick={() => { handleToggleMute(); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          {isMuted ? <VolumeX className="w-4 h-4 text-zinc-400" /> : <Volume2 className="w-4 h-4" />}
                          {isMuted ? "Bật âm thông báo" : "Tắt âm thông báo"}
                        </button>

                        <button
                          onClick={() => { setShowSearchMsgBar(!showSearchMsgBar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <Search className={`w-4 h-4 ${showSearchMsgBar ? "text-black" : "text-zinc-500"}`} />
                          Tìm kiếm tin nhắn
                        </button>

                        <button
                          onClick={() => { setShowSharedSidebar(!showSharedSidebar); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <Paperclip className={`w-4 h-4 ${showSharedSidebar ? "text-black" : "text-zinc-500"}`} />
                          Tệp đính kèm
                        </button>

                        <button
                          onClick={() => { handleTogglePinConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                          {user?.pinned_conversations?.includes(selectedConv.other_user_id) ? "Bỏ ghim" : "Ghim hội thoại"}
                        </button>

                        <button
                          onClick={() => { handleMarkAsRead(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                        >
                          <CheckCheck className="w-4 h-4" />
                          Đánh dấu đã đọc
                        </button>

                        <button
                          onClick={() => { handleBlockUser(); setShowConvMenu(false); }}
                          className={`w-full text-left px-3 py-2 text-sm transition-colors flex items-center gap-2.5 ${isBlocked ? "text-green-600 hover:bg-green-50" : "text-yellow-600 hover:bg-yellow-50"}`}
                        >
                          <ShieldAlert className="w-4 h-4" />
                          {isBlocked ? "Mở chặn liên lạc" : "Chặn liên lạc"}
                        </button>

                        <button
                          onClick={() => { handleDeleteConv(selectedConv.other_user_id); setShowConvMenu(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2.5"
                        >
                          <Trash2 className="w-4 h-4" />
                          Xóa cuộc trò chuyện
                        </button>
                      </div>
                      </>
                    )}
                    <button 
                      onClick={() => setShowConvMenu(!showConvMenu)}
                      className="p-1.5 text-zinc-400 hover:text-black hover:bg-zinc-100 rounded-full transition-colors"
                    >
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>

              <div className="flex-1 flex overflow-hidden border border-zinc-200 bg-white rounded-2xl relative animate-in fade-in slide-in-from-bottom-8 duration-300" style={{ animationDelay: '150ms', animationFillMode: 'both' }}>

                <div className="flex-1 overflow-y-auto px-4 pb-4 pt-2 no-scrollbar relative">
                  {!(showSearchMsgBar || messages.some((m) => m.is_pinned)) && <div className="pt-2" />}
                  {(showSearchMsgBar || messages.some((m) => m.is_pinned)) && (
                    <div className="sticky top-2 z-10 mb-4 bg-white/95 backdrop-blur-md border border-zinc-200 rounded-2xl shadow-sm p-4 flex flex-col gap-1.5 shrink-0">
                      {showSearchMsgBar ? (
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center justify-end">
                            <button onClick={() => { setShowSearchMsgBar(false); setSearchMsgQuery(""); setSearchedMsgResults([]); }} className="text-zinc-400 hover:text-black">
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          <div className="relative">
                            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                            <input
                              type="text"
                              placeholder="Nhập nội dung cần tìm..."
                              value={searchMsgQuery}
                              onChange={(e) => handleSearchMessages(e.target.value)}
                              className="w-full pl-8 pr-3 h-8 border border-zinc-200 bg-white text-xs font-medium focus:outline-none focus:border-black rounded-2xl"
                            />
                          </div>
                          {searchedMsgResults.length > 0 && (
                            <div className="max-h-36 overflow-y-auto space-y-1.5 pt-1.5 border-t border-zinc-100 mt-1">
                              {searchedMsgResults.map((sm) => (
                                <div
                                  key={sm._id || sm.id}
                                  onClick={() => scrollToMessage(sm._id || sm.id)}
                                  className="p-1.5 text-[10px] text-zinc-500 flex justify-between cursor-pointer border border-zinc-100 bg-white rounded-md hover:border-black transition-colors"
                                >
                                  <span className="font-semibold text-black truncate max-w-[70%]">{sm.content}</span>
                                  <span className="font-mono text-[8px] text-zinc-400">
                                    {new Date(sm.created_at).toLocaleTimeString("vi-VN")}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center">
                            <span className="text-[10px] font-bold text-black tracking-wider shrink-0">Đã ghim:</span>
                          </div>
                          <div className="space-y-1">
                            {messages.filter((m) => m.is_pinned).slice(0, 3).map((pm: any) => (
                              <div
                                key={pm._id || pm.id}
                                onClick={() => scrollToMessage(pm._id || pm.id)}
                                className="text-[10px] font-medium text-zinc-600 truncate bg-zinc-50 px-2.5 py-1.5 border-l-2 border-black cursor-pointer rounded-r-md hover:bg-zinc-100 transition-colors"
                              >
                                {pm.is_recalled ? <span className="italic text-zinc-400">Tin nhắn đã bị thu hồi</span> : pm.content || "[Hình ảnh / Tệp đính kèm]"}
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  <div className="flex flex-col pb-4">
                    {loadingMsgs ? (
                      <div className="flex h-full flex-col items-center justify-center gap-4">
                        <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                        <span className="text-xs font-medium text-zinc-500">Đang tải lịch sử</span>
                      </div>
                    ) : (
                      messages.map((msg, i) => {
                        const isSender = msg.sender_id === user?._id;
                        const reactions = msg.reactions || [];
                        
                        let showTimeDivider = false;
                        let timeLabel = "";
                        let isDifferentSender = false;
                        
                        if (i === 0) {
                          showTimeDivider = true;
                          isDifferentSender = true;
                        } else {
                          const prevMsg = messages[i - 1];
                          const currDate = new Date(msg.created_at);
                          const prevDate = new Date(prevMsg.created_at);
                          const diffMs = currDate.getTime() - prevDate.getTime();
                          
                          if (diffMs > 1800000) { // 30 mins
                            showTimeDivider = true;
                          }
                          
                          if (prevMsg.sender_id !== msg.sender_id) {
                            isDifferentSender = true;
                          }
                        }

                        if (showTimeDivider) {
                          const currDate = new Date(msg.created_at);
                          const today = new Date();
                          const yesterday = new Date();
                          yesterday.setDate(yesterday.getDate() - 1);
                          
                          const isToday = currDate.getDate() === today.getDate() && currDate.getMonth() === today.getMonth() && currDate.getFullYear() === today.getFullYear();
                          const isYesterday = currDate.getDate() === yesterday.getDate() && currDate.getMonth() === yesterday.getMonth() && currDate.getFullYear() === yesterday.getFullYear();
                          
                          const timeString = currDate.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
                          
                          if (isToday) {
                            timeLabel = `${timeString} Hôm nay`;
                          } else if (isYesterday) {
                            timeLabel = `${timeString} Hôm qua`;
                          } else {
                            const dateString = currDate.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
                            timeLabel = `${timeString} ${dateString}`;
                          }
                        }

                        const marginTopClass = showTimeDivider ? "mt-1" : "mt-1.5";

                        return (
                          <React.Fragment key={msg._id || msg.id || i}>
                            {showTimeDivider && (
                              <div className={`flex justify-center mb-4 mt-8`}>
                                <span className="px-3 py-1 bg-zinc-50 border border-zinc-200 rounded-full text-[10px] font-bold text-zinc-500 shadow-sm">
                                  {timeLabel}
                                </span>
                              </div>
                            )}
                            <div
                              ref={(el) => (messageRefs.current[msg._id || msg.id] = el)}
                              className={`group flex flex-col ${isSender ? "items-end" : "items-start"} ${marginTopClass}`}
                            >
                              <div className="relative max-w-[85%] sm:max-w-[400px]">
                              {msg.replied_message && (
                                <div className={`mb-1 px-3 py-1.5 border-l-2 border-zinc-300 bg-zinc-50/50 text-[11px] text-zinc-500 truncate`}>
                                  <span className="font-bold mr-1">{msg.replied_message.sender_id === user?._id ? user?.full_name : selectedConv.other_user?.full_name}:</span>
                                  {msg.replied_message.content || "[Hình ảnh]"}
                                </div>
                              )}

                              <div className={`px-4 py-3 text-sm leading-relaxed border rounded-2xl break-words whitespace-pre-wrap ${isSender ? "rounded-tr-sm" : "rounded-tl-sm"} ${
                                msg.is_recalled 
                                  ? "bg-zinc-50 border-zinc-200 text-zinc-400 italic" 
                                  : isSender 
                                    ? "bg-black text-white border-black" 
                                    : "bg-white text-black border-zinc-200"
                              }`}>
                                {msg.image_url && !msg.is_recalled && (
                                  <div 
                                    className="mb-2 border border-zinc-200/20 overflow-hidden rounded-2xl cursor-pointer hover:opacity-90 transition-opacity"
                                    onClick={() => window.open(msg.image_url.startsWith("http") ? msg.image_url : `${API_URL}/storage/${msg.image_url}`, '_blank')}
                                  >
                                    <img
                                      src={msg.image_url.startsWith("http") ? msg.image_url : `${API_URL}/storage/${msg.image_url}`}
                                      alt=""
                                      className="w-full h-auto max-h-[300px] object-cover"
                                    />
                                  </div>
                                )}
                                {msg.audio_url && !msg.is_recalled && (
                                  <div className="w-[240px] shrink-0">
                                    <CustomAudioPlayer src={msg.audio_url.startsWith("http") ? msg.audio_url : `${API_URL}/storage/${msg.audio_url}`} isSender={isSender} />
                                  </div>
                                )}
                                {(() => {
                                  if (msg.is_recalled) return "Tin nhắn đã bị thu hồi";
                                  const docMatch = msg.content.match(/^Đã chia sẻ tài liệu: \*\*\[([^\]]+)\](?:\(([^)]+)\))?\*\*(?:\n\n([\s\S]*))?/);
                                  if (docMatch) {
                                    return (
                                      <div 
                                        className="mb-1 mt-1 p-3 border border-zinc-200/50 bg-black text-white rounded-2xl cursor-pointer hover:bg-zinc-900 transition-colors"
                                        onClick={() => {
                                          if (docMatch[2]) router.push(`/truyen/${docMatch[2]}`);
                                        }}
                                      >
                                        <span className="font-bold text-[14px] text-blue-400">{docMatch[1]}</span>
                                      </div>
                                    );
                                  }
                                  if (msg.audio_url && msg.content === "Tin nhắn thoại") return null;
                                  return msg.content;
                                })()}
                                {msg.translated_content && !msg.is_recalled && (
                                  <div className="mt-2 pt-2 border-t border-dashed border-zinc-300/30 text-[11px] opacity-90 text-zinc-400">
                                    {msg.translated_content}
                                  </div>
                                )}
                                {msg.is_edited && !msg.is_recalled && (
                                  <span className="block text-[9px] mt-1 opacity-50 italic">(Đã chỉnh sửa)</span>
                                )}
                              </div>

                              {reactions.length > 0 && !msg.is_recalled && (
                                <div className={`flex gap-1 mt-1.5 flex-wrap ${isSender ? "justify-end" : "justify-start"}`}>
                                  {reactions.map((r: any, idx: number) => (
                                    <div
                                      key={idx}
                                      title={r.user_name}
                                      onClick={() => { if (r.user_id === user?._id) handleAddReaction(msg._id || msg.id, r.reaction); }}
                                      className={`flex items-center justify-center px-1.5 py-1 border border-zinc-200 bg-white rounded-full shadow-sm hover:bg-zinc-50 transition-colors ${r.user_id === user?._id ? "cursor-pointer hover:border-black" : "cursor-default"}`}
                                    >
                                      {r.reaction === "like" ? (
                                        <ThumbsUp className="w-3 h-3 text-black" />
                                      ) : r.reaction === "love" ? (
                                        <Heart className="w-3 h-3 text-red-500" fill="currentColor" />
                                      ) : (
                                        <span className="text-[10px] font-medium">{r.reaction}</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}


                            </div>

                            <div className={`flex items-center gap-2 mt-1 px-1 ${isSender ? "flex-row-reverse" : "flex-row"}`}>
                              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-tighter">
                                {parseUTC(msg.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                              </span>
                              {isSender && i === messages.length - 1 && (
                                <span className="text-[8px] font-semibold uppercase tracking-widest text-zinc-500 flex items-center gap-0.5">
                                  <Eye className="w-2.5 h-2.5 text-zinc-400" /> {msg.is_read ? "Đã xem" : "Đã gửi"}
                                </span>
                              )}
                              
                              {!msg.is_recalled && (
                                <div className={`flex items-center gap-1 transition-opacity ${isSender ? "flex-row-reverse" : "flex-row"} ${showMsgMenu === (msg._id || msg.id) ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}>
                                  <button
                                    onClick={() => handleAddReaction(msg._id || msg.id, "like")}
                                    className="p-1 hover:bg-zinc-100 rounded-full transition-colors text-zinc-400 hover:text-black"
                                    title="Thích"
                                  >
                                    <ThumbsUp className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    onClick={() => handleAddReaction(msg._id || msg.id, "love")}
                                    className="p-1 hover:bg-zinc-100 rounded-full transition-colors text-zinc-400 hover:text-red-500"
                                    title="Yêu thích"
                                  >
                                    <Heart className="w-3.5 h-3.5" />
                                  </button>
                                  <div className="relative">
                                    <button
                                      onClick={(e) => { e.stopPropagation(); setShowMsgMenu(showMsgMenu === (msg._id || msg.id) ? null : (msg._id || msg.id)); }}
                                      className={`p-1 rounded-full transition-colors ${showMsgMenu === (msg._id || msg.id) ? "bg-zinc-100 text-black" : "text-zinc-400 hover:text-black hover:bg-zinc-100"}`}
                                    >
                                      <MoreHorizontal className="w-4 h-4" />
                                    </button>
                                    {showMsgMenu === (msg._id || msg.id) && (
                                      <>
                                        <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setShowMsgMenu(null); }} />
                                        <div className={`absolute z-50 w-48 bg-white border border-zinc-200 shadow-xl rounded-2xl py-1.5 ${isSender ? "right-0" : "left-0"} top-full mt-1`}>
                                          <button
                                            onClick={() => { setReplyingTo(msg); setShowMsgMenu(null); }}
                                          className="w-full text-left px-3 py-2 text-[12px] font-medium text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2"
                                        >
                                          <Reply className="w-4 h-4" />
                                          Trả lời
                                        </button>
                                        <button
                                          onClick={() => { handlePin(msg._id || msg.id); setShowMsgMenu(null); }}
                                          className="w-full text-left px-3 py-2 text-[12px] font-medium text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2"
                                        >
                                          {msg.is_pinned ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                                          {msg.is_pinned ? "Bỏ ghim" : "Ghim"}
                                        </button>
                                        <button
                                          onClick={() => { handleTranslate(msg._id || msg.id, "vi"); setShowMsgMenu(null); }}
                                          className="w-full text-left px-3 py-2 text-[12px] font-medium text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2"
                                        >
                                          <Languages className="w-4 h-4" />
                                          Dịch sang Tiếng Việt
                                        </button>
                                        {(msg.image_url || msg.audio_url || (msg.attachments && msg.attachments.length > 0)) && (
                                          <button
                                            onClick={() => {
                                              const url = msg.image_url || msg.audio_url || (msg.attachments && msg.attachments[0].url);
                                              if (url) window.open(url.startsWith("http") ? url : `${API_URL}/storage/${url}`, '_blank');
                                              setShowMsgMenu(null);
                                            }}
                                            className="w-full text-left px-3 py-2 text-[12px] font-medium text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2"
                                          >
                                            <Download className="w-4 h-4" />
                                            Tải xuống
                                          </button>
                                        )}
                                        {isSender && (
                                          <>
                                            <div className="h-px bg-zinc-100 my-1.5 mx-2" />
                                            <button
                                              onClick={() => { setEditingMsg(msg); setNewMessage(msg.content); setShowMsgMenu(null); }}
                                              className="w-full text-left px-3 py-2 text-[12px] font-medium text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2"
                                            >
                                              <Edit2 className="w-4 h-4" />
                                              Chỉnh sửa
                                            </button>
                                            <button
                                              onClick={() => { handleRecall(msg._id || msg.id); setShowMsgMenu(null); }}
                                              className="w-full text-left px-3 py-2 text-[12px] font-medium text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2"
                                            >
                                              <Undo2 className="w-4 h-4" />
                                              Thu hồi
                                            </button>
                                          </>
                                        )}
                                      </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                          </React.Fragment>
                        );
                      })
                    )}
                  </div>
                  <div ref={messagesEndRef} />
                </div>

                {showSharedSidebar && (
                  <>
                    <div className="absolute inset-0 z-20" onClick={() => setShowSharedSidebar(false)} />
                    <div className="absolute right-4 top-4 bottom-4 w-[280px] border border-zinc-200 p-4 bg-white/95 backdrop-blur-md flex flex-col shrink-0 overflow-y-auto z-30 shadow-sm transition-all rounded-2xl">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] font-bold text-black uppercase tracking-wider">Tệp tin chia sẻ</span>
                        <button onClick={() => setShowSharedSidebar(false)} className="text-zinc-400 hover:text-black p-1.5 rounded-full hover:bg-zinc-100 transition-colors">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="space-y-3">
                        {sharedAttachments.length > 0 ? (
                          sharedAttachments.map((att) => {
                            const isDoc = att.content && att.content.includes("](/truyen/");
                            let parsedTitle = att.content;
                            let docUrl = null;
                            if (isDoc) {
                              const match = att.content.match(/\[(.*?)\]\((.*?)\)/);
                              if (match) {
                                parsedTitle = match[1];
                                docUrl = match[2];
                              }
                            }
                            return (
                              <div
                                key={att.id || att._id}
                                onClick={() => {
                                  if (att.image_url) {
                                    window.open(att.image_url.startsWith("http") ? att.image_url : `${API_URL}/storage/${att.image_url}`, '_blank');
                                  } else if (docUrl) {
                                    if (docUrl.startsWith("http") || docUrl.startsWith("/")) window.open(docUrl, '_blank');
                                    else window.open(`${API_URL}/storage/${docUrl}`, '_blank');
                                  } else if (att.audio_url) {
                                    window.open(`${API_URL}/storage/${att.audio_url}`, '_blank');
                                  }
                                }}
                                className="p-2 border border-zinc-200 bg-white hover:border-black cursor-pointer transition-colors"
                              >
                                {att.image_url ? (
                                  <div className="flex flex-col gap-1.5">
                                    <img src={att.image_url.startsWith("http") ? att.image_url : `${API_URL}/storage/${att.image_url}`} className="w-full h-24 object-cover" />
                                    <span className="text-[8px] font-mono text-zinc-400">Ảnh gửi lúc: {new Date(att.created_at).toLocaleDateString()}</span>
                                  </div>
                                ) : (
                                  <div className="flex flex-col gap-1">
                                    <span className="text-xs font-semibold text-black truncate">{parsedTitle || "Tài liệu đính kèm"}</span>
                                    <span className="text-[8px] font-mono text-zinc-400">
                                      {isDoc ? "Tài liệu sáng tác" : (att.audio_url ? "Tin nhắn thoại" : "Tài liệu đính kèm")}
                                    </span>
                                  </div>
                                )}
                              </div>
                            );
                          })
                        ) : (
                          <p className="text-xs text-zinc-400 text-center py-6">Chưa có tệp tin nào được chia sẻ</p>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="shrink-0 z-10 relative">
                {isBlocked && (
                  <div className="mb-3 p-2 border border-zinc-200 bg-zinc-50 text-xs text-zinc-500 text-center font-medium">
                    Liên lạc đã bị khóa. Không thể truyền tin.
                  </div>
                )}


                {(replyingTo || editingMsg) && (
                  <div className="mb-4 p-3 bg-zinc-50 border-l-2 border-black flex items-center justify-between">
                    <div className="min-w-0">
                      <span className="text-[11px] font-bold text-black block mb-1">
                        {editingMsg ? "Chỉnh sửa tin nhắn" : (replyingTo.sender_id === user?._id ? user?.full_name : selectedConv.other_user?.full_name)}
                      </span>
                      <p className="text-xs text-zinc-500 truncate">{(editingMsg || replyingTo).content || "[Hình ảnh]"}</p>
                    </div>
                    <button onClick={() => { setReplyingTo(null); setEditingMsg(null); setNewMessage(""); }} className="p-2">
                      <X className="w-4 h-4 text-zinc-400" />
                    </button>
                  </div>
                )}

                {imageFile && (
                  <div className="mb-4 relative w-16 h-16">
                    <img src={URL.createObjectURL(imageFile)} alt="" className="w-full h-full object-cover rounded-2xl border border-zinc-200" />
                    <button 
                      onClick={() => setImageFile(null)} 
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-black text-white flex items-center justify-center rounded-full shadow-sm"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                )}

                <div className="flex gap-3 relative items-end">
                  <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={(e) => { setImageFile(e.target.files ? e.target.files[0] : null); setShowAttachMenu(false); }} />
                  
                  {showAttachMenu && (
                    <>
                      <div className="fixed inset-0 z-40" onClick={(e) => { e.stopPropagation(); setShowAttachMenu(false); }} />
                      <div className="absolute bottom-full left-0 mb-2 w-48 bg-white border border-zinc-200 rounded-2xl shadow-lg py-1 z-50">
                      <button
                        onClick={() => { fileInputRef.current?.click(); }}
                        className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                      >
                        <ImageIcon className="w-4 h-4" />
                        Hình ảnh
                      </button>
                      <button
                        onClick={() => { openShareDoc(); setShowAttachMenu(false); }}
                        className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                      >
                        <Book className="w-4 h-4" />
                        Tài liệu sáng tác
                      </button>
                      <button
                        onClick={() => { handleStartRecording(); setShowAttachMenu(false); }}
                        className="w-full text-left px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors flex items-center gap-2.5"
                      >
                        <Mic className="w-4 h-4" />
                        Ghi âm
                      </button>
                    </div>
                    </>
                  )}

                  <div className={`flex-1 min-h-[48px] bg-white border border-zinc-200 flex ${isRecording ? "items-center" : "items-end"} px-4 gap-3 focus-within:border-zinc-300 rounded-2xl transition-colors py-1`}>
                    {!isRecording ? (
                      <>
                        <button
                          type="button"
                          onClick={() => setShowAttachMenu(!showAttachMenu)}
                          disabled={isBlocked}
                          className="text-zinc-400 shrink-0 rounded-full p-1.5 hover:bg-zinc-100 transition-colors disabled:opacity-50 mb-1"
                        >
                          <Plus className="w-5 h-5" />
                        </button>
                        <textarea
                          rows={1}
                          value={newMessage}
                          onChange={(e) => {
                            setNewMessage(e.target.value);
                            e.target.style.height = 'auto';
                            e.target.style.height = e.target.scrollHeight + 'px';
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                              e.preventDefault();
                              if (!sending) handleSend();
                            }
                          }}
                          disabled={isBlocked}
                          placeholder={isBlocked ? "Hội thoại bị vô hiệu hóa" : ""}
                          className="flex-1 min-w-0 py-2.5 max-h-32 resize-none text-sm bg-transparent outline-none font-medium text-black placeholder:text-zinc-400 disabled:opacity-50 scrollbar-hide"
                        />
                      </>
                    ) : (
                      <div className="flex-1 flex items-center justify-between py-1 h-full">
                        <button 
                          onClick={handleCancelRecording}
                          className="text-zinc-400 hover:text-black hover:bg-zinc-100 p-1.5 rounded-full transition-colors shrink-0"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                        <div className="flex-1 flex items-center justify-center gap-3">
                          <span className="w-2.5 h-2.5 bg-black rounded-full animate-ping shrink-0" />
                          <span className="text-sm font-bold text-black font-mono">
                            {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')}
                          </span>
                        </div>
                        <div className="w-8 shrink-0"></div> {/* Placeholder to perfectly center the text */}
                      </div>
                    )}
                  </div>

                  <button 
                    onClick={isRecording ? handleStopRecording : handleSend} 
                    disabled={sending || isBlocked || (!isRecording && (!newMessage.trim() && !imageFile))} 
                    className="w-12 h-[48px] bg-black text-white flex items-center justify-center disabled:opacity-50 rounded-2xl shrink-0 transition-colors hover:bg-zinc-800"
                  >
                    {sending || uploadingImage ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center bg-white border border-zinc-200 rounded-2xl shadow-sm animate-in fade-in slide-in-from-bottom-8 duration-300">
              <p className="text-sm font-semibold text-black">DocLib Tin nhắn</p>
              <p className="text-xs font-medium text-zinc-500 mt-1">Chọn một cuộc hội thoại từ hộp thư để bắt đầu kết nối</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
