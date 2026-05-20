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
  Smile,
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
} from "lucide-react";
import { useRouter } from "next/navigation";
import { parseUTC } from "@/lib/utils";

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
  const recordTimerRef = useRef<any>(null);

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
  }, [messages]);

  useEffect(() => {
    if (!user?._id) return;

    const wsUrl = `${WS_URL}/tro-chuyen/ws/${user._id}`;
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);

        if (type === "new_message") {
          if (selectedConvRef.current && (data.sender_id === selectedConvRef.current.other_user_id)) {
            setMessages(prev => {
              if (prev.some(m => (m._id || m.id) === (data._id || data.id))) return prev;
              return [...prev, data];
            });
            markAsReadAPI(selectedConvRef.current.other_user_id).catch(() => {});
          }
          loadConversations();
        } else if (type === "message_edited") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "message_pinned") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
          loadConversations();
        } else if (type === "message_recalled") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
          loadConversations();
        } else if (type === "message_reaction") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "messages_read") {
          setMessages(prev => prev.map(m => m.sender_id === data.reader_id ? { ...m, is_read: true } : m));
        } else if (type === "message_translated") {
          setMessages(prev => prev.map(m => (m._id || m.id) === data.message_id ? { ...m, translated_content: data.translated_content } : m));
        } else if (type === "conversation_settings_updated") {
          if (selectedConvRef.current) {
            setSelfDestructSeconds(data.self_destruct_seconds || 0);
          }
        }
      } catch (err) {
        console.error("WS Error:", err);
      }
    };

    return () => socket.close();
  }, [user?._id, loadConversations]);

  const selectConversation = async (conv: any) => {
    if (selectedConvRef.current && newMessage.trim()) {
      await saveDraftAPI(selectedConvRef.current.other_user_id, newMessage.trim());
    }

    setSelectedConv(conv);
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
      
      loadConversations();
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
    if ((!newMessage.trim() && !imageFile) || !selectedConv) return;

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
      loadConversations();
      
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
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        setSending(true);
        try {
          const blob = new Blob(chunks, { type: "audio/webm" });
          const file = new File([blob], "voice.webm", { type: "audio/webm" });
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
          loadConversations();
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
      loadConversations();
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
      loadConversations();
    } catch (err: any) {
      showToast(err.message || "Thu hồi thất bại.", "error");
    }
  };

  const handleSearchMessages = async (q: string) => {
    setSearchMsgQuery(q);
    if (!selectedConv || q.length < 2) {
      setSearchedMsgResults([]);
      return;
    }
    try {
      const res = await searchMessagesAPI(selectedConv.other_user_id, q);
      setSearchedMsgResults(res.data || res || []);
    } catch (err) {}
  };

  const handleAddReaction = async (messageId: string, reaction: string) => {
    try {
      const res = await addReactionAPI(messageId, reaction);
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
    } catch (err) {}
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
      loadConversations();
      
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
      loadConversations();
    } catch (err: any) {
      showToast("Không thể thay đổi trạng thái ghim.", "error");
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
    } catch (err) {}
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <Modal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        className="max-w-xl rounded-none border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="p-6 border-b border-zinc-200">
          <ModalTitle className="text-sm font-semibold text-black flex items-center gap-2">
            Bắt đầu hội thoại mới
          </ModalTitle>
          <ModalDescription className="text-xs text-zinc-500 font-medium mt-1">
            Tìm kiếm người dùng qua tên hoặc ID để kết nối
          </ModalDescription>
        </ModalHeader>

        <ModalContent className="p-6 space-y-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              value={searchQuery}
              onChange={(e) => handleSearchUsers(e.target.value)}
              placeholder="Nhập tên người dùng"
              className="w-full h-10 pl-10 pr-4 bg-zinc-50 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-none"
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
                    <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center overflow-hidden bg-white shrink-0">
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
        className="max-w-xl rounded-none border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="p-6 border-b border-zinc-200">
          <ModalTitle className="text-sm font-semibold text-black flex items-center gap-2">
            Tạo nhóm thảo luận
          </ModalTitle>
          <ModalDescription className="text-xs text-zinc-500 font-medium mt-1">
            Kết nối nhiều tác giả để cùng trao đổi chuyên sâu
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-black uppercase">Tên nhóm thảo luận</label>
            <input
              type="text"
              placeholder="Nhập tên nhóm..."
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              className="w-full h-10 px-3 border border-zinc-200 bg-zinc-50 text-xs font-medium focus:outline-none focus:border-black rounded-none"
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
                  <div key={u._id || u.id} className="flex items-center gap-2 p-1.5 hover:bg-zinc-50">
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
                      className="accent-black rounded-none"
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
            className="w-full h-10 bg-black text-white text-xs font-semibold rounded-none"
          >
            Khởi tạo nhóm
          </button>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showShareDocModal}
        onClose={() => setShowShareDocModal(false)}
        className="max-w-xl rounded-none border border-zinc-200 bg-white p-0"
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

      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold text-black">Trò chuyện</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Hệ thống giao tiếp nội bộ chuyên sâu
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={openGroupModal}
            className="h-10 px-6 border border-zinc-200 bg-white hover:bg-zinc-50 text-black text-xs font-medium flex items-center gap-2 rounded-none"
          >
            <Users className="w-4 h-4" /> Tạo nhóm thảo luận
          </button>
          <button
            onClick={() => setShowNewChatModal(true)}
            className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 rounded-none"
          >
            Bắt đầu kết nối
          </button>
        </div>
      </div>

      <div className="border border-zinc-200 bg-white flex h-[calc(100vh-200px)] min-h-[500px]">
        <div
          className={`w-full md:w-[320px] lg:w-[380px] border-r border-zinc-200 flex flex-col shrink-0 ${selectedConv ? "hidden md:flex" : "flex"
            }`}
        >
          <div className="p-4 border-b border-zinc-200 bg-white flex items-center justify-between shrink-0">
            <span className="text-xs font-semibold text-black uppercase tracking-wider">Hộp thư</span>
          </div>
          <div className="flex-1 overflow-y-auto">
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
                    className={`p-4 border-b border-zinc-200 cursor-pointer flex items-center gap-4 group relative ${selectedConv?.other_user_id === conv.other_user_id
                        ? "bg-zinc-50 border-l-[3px] border-l-black pl-[13px]"
                        : "pl-4"
                      }`}
                  >
                    <div className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center shrink-0 overflow-hidden">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <User className="w-5 h-5 text-zinc-400 stroke-[1]" />
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
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleTogglePinConv(conv.other_user_id);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 bg-white border border-zinc-200 text-zinc-400 hover:text-black shrink-0"
                          >
                            <Pin className="w-3 h-3" />
                          </button>
                          {conv.unread_count > 0 && <div className="w-2 h-2 bg-black shrink-0 rounded-none"></div>}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-24 flex flex-col items-center justify-center opacity-50">
                <p className="text-xs font-medium text-black">Hộp thư rỗng</p>
              </div>
            )}
          </div>
        </div>

        <div className={`flex-1 flex flex-col ${!selectedConv ? "hidden md:flex" : "flex"}`}>
          {selectedConv ? (
            <>
              <div className="p-4 border-b border-zinc-200 bg-white flex flex-col shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <button onClick={() => setSelectedConv(null)} className="md:hidden p-2 text-zinc-500">
                      <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div className="w-10 h-10 border border-zinc-200 overflow-hidden bg-white flex items-center justify-center relative">
                      {selectedConv.other_user?.avatar_url ? (
                        <img
                          src={selectedConv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <User className="w-5 h-5 text-zinc-400 stroke-[1]" />
                      )}
                      <div className={`absolute bottom-0 right-0 w-2.5 h-2.5 border-2 border-white rounded-none ${isOnline ? "bg-black" : "bg-zinc-300"}`} />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm text-black flex items-center gap-1.5">
                        {selectedConv.other_user?.full_name || selectedConv.other_user?.username}
                        <span className="text-[9px] font-normal text-zinc-400">({isOnline ? "Trực tuyến" : "Ngoại tuyến"})</span>
                      </span>
                      <span className="text-[10px] text-zinc-500 font-medium mt-0.5">Bảo mật hai chiều</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)}
                      className={`p-2 border rounded-none relative ${selfDestructSeconds > 0 ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                      title="Tin nhắn tự hủy"
                    >
                      <Flame className="w-4 h-4" />
                      {showSelfDestructMenu && (
                        <div className="absolute right-0 top-full mt-1.5 z-20 w-36 bg-white border border-zinc-200 shadow-xl flex flex-col text-left">
                          <button onClick={() => handleUpdateSelfDestruct(0)} className="px-3 py-2 text-[10px] font-semibold text-black hover:bg-zinc-50 border-b border-zinc-100">Tắt tự hủy</button>
                          <button onClick={() => handleUpdateSelfDestruct(5)} className="px-3 py-2 text-[10px] font-semibold text-black hover:bg-zinc-50 border-b border-zinc-100">5 giây</button>
                          <button onClick={() => handleUpdateSelfDestruct(60)} className="px-3 py-2 text-[10px] font-semibold text-black hover:bg-zinc-50 border-b border-zinc-100">1 phút</button>
                          <button onClick={() => handleUpdateSelfDestruct(3600)} className="px-3 py-2 text-[10px] font-semibold text-black hover:bg-zinc-50">1 giờ</button>
                        </div>
                      )}
                    </button>
                    <button
                      onClick={handleToggleMute}
                      className={`p-2 border rounded-none ${isMuted ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                      title={isMuted ? "Bật âm thông báo" : "Tắt âm thông báo"}
                    >
                      {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={() => setShowSearchMsgBar(!showSearchMsgBar)}
                      className={`p-2 border rounded-none ${showSearchMsgBar ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                    >
                      <Search className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setShowSharedSidebar(!showSharedSidebar)}
                      className={`p-2 border rounded-none ${showSharedSidebar ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                    >
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <button
                      onClick={handleBlockUser}
                      className={`p-2 border rounded-none ${isBlocked ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200"}`}
                      title={isBlocked ? "Mở chặn" : "Chặn liên lạc"}
                    >
                      <ShieldAlert className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-zinc-400">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {showSearchMsgBar && (
                  <div className="mt-3 flex flex-col gap-2 bg-zinc-50 border border-zinc-200 p-2.5">
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        placeholder="Tìm kiếm nội dung tin nhắn trong lịch sử..."
                        value={searchMsgQuery}
                        onChange={(e) => handleSearchMessages(e.target.value)}
                        className="w-full pl-8 pr-3 h-8 border border-zinc-200 bg-white text-xs font-medium focus:outline-none focus:border-black rounded-none"
                      />
                    </div>
                    {searchedMsgResults.length > 0 && (
                      <div className="max-h-36 overflow-y-auto space-y-1.5 pt-1.5 border-t border-zinc-100">
                        {searchedMsgResults.map((sm) => (
                          <div
                            key={sm._id || sm.id}
                            onClick={() => scrollToMessage(sm._id || sm.id)}
                            className="p-1.5 hover:bg-zinc-100 text-[10px] text-zinc-500 flex justify-between cursor-pointer border border-zinc-100 bg-white"
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
                )}
              </div>

              <div className="flex-1 flex overflow-hidden">
                <div className="flex-1 overflow-y-auto px-6 pb-6 pt-0 bg-white no-scrollbar">
                  {(messages.some((m) => m.is_pinned)) && (
                    <div className="sticky top-0 z-10 -mx-6 px-6 py-4 mb-6 bg-white border-b border-zinc-100 flex flex-col gap-1 shrink-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-black tracking-wider shrink-0">Đã ghim:</span>
                      </div>
                      <div className="space-y-1">
                        {messages.filter((m) => m.is_pinned).slice(0, 3).map((pm: any) => (
                          <div
                            key={pm._id || pm.id}
                            onClick={() => scrollToMessage(pm._id || pm.id)}
                            className="text-[10px] font-medium text-zinc-600 truncate bg-zinc-50 px-2 py-1.5 border-l-2 border-black cursor-pointer hover:bg-zinc-100"
                          >
                            {pm.content || "Hình ảnh"}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {!messages.some(m => m.is_pinned) && <div className="pt-6" />}
                  <div className="flex flex-col gap-8">
                    {loadingMsgs ? (
                      <div className="flex h-full flex-col items-center justify-center gap-4">
                        <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                        <span className="text-xs font-medium text-zinc-500">Đang tải lịch sử</span>
                      </div>
                    ) : (
                      messages.map((msg, i) => {
                        const isSender = msg.sender_id === user?._id;
                        const reactions = msg.reactions || [];
                        return (
                          <div
                            key={i}
                            ref={(el) => (messageRefs.current[msg._id || msg.id] = el)}
                            className={`flex flex-col transition-colors duration-500 ${isSender ? "items-end" : "items-start"}`}
                          >
                            <div className="group relative max-w-[85%] sm:max-w-[70%]">
                              {msg.replied_message && (
                                <div className={`mb-1 px-3 py-1.5 border-l-2 border-zinc-300 bg-zinc-50/50 text-[11px] text-zinc-500 truncate`}>
                                  <span className="font-bold mr-1">{msg.replied_message.sender_id === user?._id ? "Bạn" : selectedConv.other_user?.full_name}:</span>
                                  {msg.replied_message.content || "[Hình ảnh]"}
                                </div>
                              )}

                              <div className={`px-4 py-3 text-sm leading-relaxed border transition-colors ${
                                msg.is_recalled 
                                  ? "bg-zinc-50 border-zinc-200 text-zinc-400 italic" 
                                  : isSender 
                                    ? "bg-black text-white border-black" 
                                    : "bg-white text-black border-zinc-200"
                              }`}>
                                {msg.image_url && !msg.is_recalled && (
                                  <div className="mb-2 border border-zinc-800 overflow-hidden">
                                    <img
                                      src={msg.image_url.startsWith("http") ? msg.image_url : `${API_URL}/storage/${msg.image_url}`}
                                      alt=""
                                      className="w-full h-auto max-h-[300px] object-contain"
                                    />
                                  </div>
                                )}
                                {msg.audio_url && !msg.is_recalled && (
                                  <div className="mb-2 w-full max-w-[260px] shrink-0">
                                    <audio controls src={msg.audio_url.startsWith("http") ? msg.audio_url : `${API_URL}/storage/${msg.audio_url}`} className="w-full h-9" />
                                  </div>
                                )}
                                {msg.content}
                                {msg.translated_content && (
                                  <div className="mt-2 pt-2 border-t border-dashed border-zinc-300/30 text-[11px] opacity-90 text-zinc-400">
                                    {msg.translated_content}
                                  </div>
                                )}
                                {msg.is_edited && !msg.is_recalled && (
                                  <span className="block text-[9px] mt-1 opacity-50 italic">(Đã chỉnh sửa)</span>
                                )}
                              </div>

                              {reactions.length > 0 && (
                                <div className={`flex gap-1 mt-1.5 flex-wrap ${isSender ? "justify-end" : "justify-start"}`}>
                                  {reactions.map((r: any, idx: number) => (
                                    <span
                                      key={idx}
                                      title={r.user_name}
                                      className="px-2 py-0.5 border border-zinc-200 bg-zinc-50 text-[10px] font-medium"
                                    >
                                      {r.reaction}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {!msg.is_recalled && (
                                <div className={`absolute top-0 ${isSender ? "-left-[120px]" : "-right-[120px]"} opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1`}>
                                  <div className="relative flex items-center gap-1 bg-white border border-zinc-200 p-1">
                                    <button
                                      onClick={() => handleAddReaction(msg._id || msg.id, "👍")}
                                      className="hover:scale-125 transition-transform text-[11px]"
                                    >
                                      👍
                                    </button>
                                    <button
                                      onClick={() => handleAddReaction(msg._id || msg.id, "❤️")}
                                      className="hover:scale-125 transition-transform text-[11px]"
                                    >
                                      ❤️
                                    </button>
                                  </div>
                                  <div className="relative flex items-center gap-0.5">
                                    <button
                                      onClick={() => handleTranslate(msg._id || msg.id, "vi")}
                                      className="p-1 bg-white border border-zinc-200 text-zinc-400 hover:text-black"
                                      title="Dịch sang tiếng Việt"
                                    >
                                      <Languages className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      onClick={() => setShowMsgMenu(showMsgMenu === (msg._id || msg.id) ? null : (msg._id || msg.id))}
                                      className="p-1.5 bg-white border border-zinc-200 text-zinc-400 hover:text-black transition-colors"
                                    >
                                      <MoreVertical className="w-4 h-4" />
                                    </button>
                                    {showMsgMenu === (msg._id || msg.id) && (
                                      <div className={`absolute z-10 w-32 bg-white border border-zinc-200 shadow-xl ${isSender ? "right-0" : "left-0"} top-full mt-1`}>
                                        <button
                                          onClick={() => { setReplyingTo(msg); setShowMsgMenu(null); }}
                                          className="w-full text-left px-3 py-2 text-[11px] font-medium hover:bg-zinc-50"
                                        >
                                          Trả lời
                                        </button>
                                        <button
                                          onClick={() => { handlePin(msg._id || msg.id); setShowMsgMenu(null); }}
                                          className="w-full text-left px-3 py-2 text-[11px] font-medium hover:bg-zinc-50"
                                        >
                                          {msg.is_pinned ? "Bỏ ghim" : "Ghim"}
                                        </button>
                                        {isSender && (
                                          <>
                                            <button
                                              onClick={() => { setEditingMsg(msg); setNewMessage(msg.content); setShowMsgMenu(null); }}
                                              className="w-full text-left px-3 py-2 text-[11px] font-medium hover:bg-zinc-50"
                                            >
                                              Chỉnh sửa
                                            </button>
                                            <button
                                              onClick={() => { handleRecall(msg._id || msg.id); setShowMsgMenu(null); }}
                                              className="w-full text-left px-3 py-2 text-[11px] font-medium hover:bg-zinc-50 text-black font-semibold"
                                            >
                                              Thu hồi
                                            </button>
                                          </>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-2 mt-1 px-1">
                              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-tighter">
                                {parseUTC(msg.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                              </span>
                              {isSender && i === messages.length - 1 && (
                                <span className="text-[8px] font-semibold uppercase tracking-widest text-zinc-500 flex items-center gap-0.5">
                                  <Eye className="w-2.5 h-2.5 text-zinc-400" /> {msg.is_read ? "Đã xem" : "Đã gửi"}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                  <div ref={messagesEndRef} />
                </div>

                {showSharedSidebar && (
                  <div className="w-64 border-l border-zinc-200 p-4 bg-zinc-50/50 flex flex-col shrink-0 overflow-y-auto">
                    <span className="text-[10px] font-bold text-black uppercase tracking-wider mb-3">Tệp tin chia sẻ</span>
                    <div className="space-y-3">
                      {sharedAttachments.length > 0 ? (
                        sharedAttachments.map((att) => (
                          <div key={att.id} className="p-2 border border-zinc-200 bg-white">
                            {att.type === "image" ? (
                              <div className="flex flex-col gap-1.5">
                                <img src={att.url.startsWith("http") ? att.url : `${API_URL}/storage/${att.url}`} className="w-full h-24 object-cover" />
                                <span className="text-[8px] font-mono text-zinc-400">Ảnh gửi lúc: {new Date(att.created_at).toLocaleDateString()}</span>
                              </div>
                            ) : (
                              <div className="flex flex-col gap-1">
                                <span className="text-xs font-semibold text-black truncate">{att.content}</span>
                                <span className="text-[8px] font-mono text-zinc-400">Tài liệu đính kèm</span>
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-zinc-400 text-center py-6">Chưa có tệp tin nào được chia sẻ</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-zinc-200 bg-white shrink-0">
                {isBlocked && (
                  <div className="mb-3 p-2 border border-zinc-200 bg-zinc-50 text-xs text-zinc-500 text-center font-medium">
                    Liên lạc đã bị khóa. Không thể truyền tin.
                  </div>
                )}

                {isRecording && (
                  <div className="mb-3 p-2.5 border border-black bg-zinc-50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-black animate-ping shrink-0" />
                      <span className="text-xs font-bold text-black uppercase">Đang ghi âm cuộc trò chuyện: {recordingDuration} giây</span>
                    </div>
                    <button onClick={handleStopRecording} className="h-7 px-3 bg-black text-white text-[10px] font-bold uppercase rounded-none">Hoàn tất & Gửi</button>
                  </div>
                )}

                {(replyingTo || editingMsg) && (
                  <div className="mb-4 p-3 bg-zinc-50 border-l-2 border-black flex items-center justify-between">
                    <div className="min-w-0">
                      <span className="text-[10px] font-bold text-black uppercase block mb-1">
                        {editingMsg ? "Đang chỉnh sửa tin nhắn" : `Đang trả lời ${replyingTo.sender_id === user?._id ? "chính mình" : selectedConv.other_user?.full_name}`}
                      </span>
                      <p className="text-xs text-zinc-500 truncate">{(editingMsg || replyingTo).content || "[Hình ảnh]"}</p>
                    </div>
                    <button onClick={() => { setReplyingTo(null); setEditingMsg(null); setNewMessage(""); }} className="p-2">
                      <X className="w-4 h-4 text-zinc-400" />
                    </button>
                  </div>
                )}

                {imageFile && (
                  <div className="mb-4 relative w-24 h-24 border border-zinc-200">
                    <img src={URL.createObjectURL(imageFile)} alt="" className="w-full h-full object-cover" />
                    <button onClick={() => setImageFile(null)} className="absolute -top-2 -right-2 w-5 h-5 bg-black text-white flex items-center justify-center text-[10px]">X</button>
                  </div>
                )}

                <div className="flex gap-3">
                  <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={(e) => setImageFile(e.target.files ? e.target.files[0] : null)} />
                  <button onClick={() => fileInputRef.current?.click()} disabled={isBlocked || isRecording} className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center text-zinc-400 hover:text-black transition-colors shrink-0 disabled:opacity-50">
                    <Plus className="w-5 h-5" />
                  </button>
                  <button onClick={openShareDoc} disabled={isBlocked || isRecording} className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center text-zinc-400 hover:text-black transition-colors shrink-0 disabled:opacity-50">
                    <Book className="w-5 h-5" />
                  </button>
                  <button onClick={handleStartRecording} disabled={isBlocked || isRecording} className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center text-zinc-400 hover:text-black transition-colors shrink-0 disabled:opacity-50">
                    <Mic className="w-5 h-5" />
                  </button>
                  <input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    disabled={isBlocked || isRecording}
                    placeholder={isBlocked ? "Hội thoại bị vô hiệu hóa" : isRecording ? "Bộ thu âm đang mở..." : "Nhập nội dung thông điệp"}
                    className="flex-1 h-12 px-4 bg-zinc-50 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-none placeholder:text-zinc-400 disabled:opacity-50"
                  />
                  <button onClick={handleSend} disabled={sending || isBlocked || isRecording || (!newMessage.trim() && !imageFile)} className="w-12 h-12 bg-black text-white flex items-center justify-center disabled:opacity-50 rounded-none shrink-0">
                    {sending || uploadingImage ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center bg-white">
              <p className="text-sm font-semibold text-black">Hệ thống truyền tin</p>
              <p className="text-xs font-medium text-zinc-500 mt-1">Chọn một hội thoại để bắt đầu</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
