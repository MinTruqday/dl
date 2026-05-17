"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getConversationsAPI,
  getMessagesAPI,
  sendMessageAPI,
  togglePinAPI,
  editMessageAPI,
} from "@/services/chat.service";
import { searchUsersAPI } from "@/services/social.service";
import { API_URL, getToken } from "@/services/authentication.service";
import { useToast } from "@/contexts/ToastContext";
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
  }, []);

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

    const wsUrl = API_URL.replace("http", "ws") + `/tro-chuyen/ws/${user._id}`;
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
          }
          loadConversations();
        } else if (type === "message_edited") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
        } else if (type === "message_pinned") {
          setMessages(prev => prev.map(m => (m._id || m.id) === (data._id || data.id) ? data : m));
          loadConversations();
        }
      } catch (err) {
        console.error("WS Error:", err);
      }
    };

    return () => socket.close();
  }, [user?._id, loadConversations]);

  const selectConversation = async (conv: any) => {
    setSelectedConv(conv);
    setLoadingMsgs(true);
    setReplyingTo(null);
    setImageFile(null);
    try {
      const res = await getMessagesAPI(conv.other_user_id);
      setMessages(res.data || res || []);
    } catch (err: any) {
      showToast("Không thể truy xuất lịch sử tin nhắn.", "error");
    } finally {
      setLoadingMsgs(false);
    }
  };

  const handleSend = async () => {
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
        const resUpload = await fetch(`${API_URL}/luu-trư/`, {
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
      loadConversations();
    } catch (err: any) {
      showToast("Gửi tin nhắn thất bại. Vui lòng kiểm tra kết nối.", "error");
    } finally {
      setSending(false);
      setUploadingImage(false);
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

      <div className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold text-black">Trò chuyện</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Hệ thống giao tiếp nội bộ chuyên sâu
          </p>
        </div>
        <button
          onClick={() => setShowNewChatModal(true)}
          className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 rounded-none"
        >
          Bắt đầu kết nối
        </button>
      </div>

      <div className="border border-zinc-200 bg-white flex h-[calc(100vh-200px)] min-h-[500px]">
        <div
          className={`w-full md:w-[320px] lg:w-[380px] border-r border-zinc-200 flex flex-col shrink-0 ${
            selectedConv ? "hidden md:flex" : "flex"
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
            ) : conversations.length > 0 ? (
              conversations.map((conv) => (
                <div
                  key={conv.other_user_id}
                  onClick={() => selectConversation(conv)}
                  className={`p-4 border-b border-zinc-200 cursor-pointer flex items-center gap-4 ${
                    selectedConv?.other_user_id === conv.other_user_id
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
                      <span className={`text-sm text-black truncate ${conv.unread_count > 0 ? "font-semibold" : "font-medium"}`}>
                        {conv.other_user?.full_name || conv.other_user?.username}
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
                      {conv.unread_count > 0 && <div className="w-2 h-2 bg-black shrink-0 rounded-none"></div>}
                    </div>
                  </div>
                </div>
              ))
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
                    <div className="w-10 h-10 border border-zinc-200 overflow-hidden bg-white flex items-center justify-center">
                      {selectedConv.other_user?.avatar_url ? (
                        <img
                          src={selectedConv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale mix-blend-multiply"
                        />
                      ) : (
                        <User className="w-5 h-5 text-zinc-400 stroke-[1]" />
                      )}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm text-black">
                        {selectedConv.other_user?.full_name || selectedConv.other_user?.username}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-medium mt-0.5">Bảo mật hai chiều</span>
                    </div>
                  </div>
                  <button className="p-2 text-zinc-400">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>

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

                          <div className={`px-4 py-3 text-sm leading-relaxed border transition-colors ${isSender ? "bg-black text-white border-black" : "bg-white text-black border-zinc-200"}`}>
                            {msg.image_url && (
                              <div className="mb-2 border border-zinc-800 overflow-hidden">
                                <img
                                  src={msg.image_url.startsWith("http") ? msg.image_url : `${API_URL}/storage/${msg.image_url}`}
                                  alt=""
                                  className="w-full h-auto max-h-[300px] object-contain"
                                />
                              </div>
                            )}
                            {msg.content}
                            {msg.is_edited && (
                              <span className="block text-[9px] mt-1 opacity-50 italic">(Đã chỉnh sửa)</span>
                            )}
                          </div>

                          <div className={`absolute top-0 ${isSender ? "-left-10" : "-right-10"} opacity-0 group-hover:opacity-100 transition-opacity`}>
                            <div className="relative">
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
                                    <button 
                                      onClick={() => { setEditingMsg(msg); setNewMessage(msg.content); setShowMsgMenu(null); }}
                                      className="w-full text-left px-3 py-2 text-[11px] font-medium hover:bg-zinc-50"
                                    >
                                      Chỉnh sửa
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 mt-1 px-1">
                          <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-tighter">
                            {parseUTC(msg.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
                </div>
                <div ref={messagesEndRef} />
              </div>

              <div className="p-4 border-t border-zinc-200 bg-white shrink-0">
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
                  <button onClick={() => fileInputRef.current?.click()} className="w-12 h-12 bg-white border border-zinc-200 flex items-center justify-center text-zinc-400 hover:text-black transition-colors shrink-0">
                    <Plus className="w-5 h-5" />
                  </button>
                  <input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Nhập nội dung thông điệp"
                    className="flex-1 h-12 px-4 bg-zinc-50 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-none placeholder:text-zinc-400"
                  />
                  <button onClick={handleSend} disabled={sending || (!newMessage.trim() && !imageFile)} className="w-12 h-12 bg-black text-white flex items-center justify-center disabled:opacity-50 rounded-none shrink-0">
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
