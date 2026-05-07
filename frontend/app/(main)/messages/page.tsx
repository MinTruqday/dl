"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getConversationsAPI,
  getMessagesAPI,
  sendMessageAPI,
} from "@/services/chat.service";
import { searchUsersAPI } from "@/services/social.service";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
} from "@/components/ui/Modal";
import {
  MessageSquare,
  Send,
  User,
  Loader2,
  ArrowLeft,
  Search,
  Plus,
  UserPlus,
  MoreVertical,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { useRouter } from "next/navigation";

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
  const [visible, setVisible] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

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
      router.push("/login");
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

  const selectConversation = async (conv: any) => {
    setSelectedConv(conv);
    setLoadingMsgs(true);
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
    if (!newMessage.trim() || !selectedConv) return;
    setSending(true);
    try {
      const res = await sendMessageAPI(
        selectedConv.other_user_id,
        newMessage.trim(),
      );
      const msg = res.data || res;
      setMessages((prev) => [...prev, msg]);
      setNewMessage("");
      loadConversations();
    } catch (err: any) {
      showToast("Gửi tin nhắn thất bại. Vui lòng kiểm tra kết nối.", "error");
    } finally {
      setSending(false);
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
            <UserPlus className="w-4 h-4" /> Bắt đầu hội thoại mới
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

      <div
        className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Trò chuyện</h1>
          <p className="text-zinc-500 text-sm font-medium flex items-center gap-2">
            Hệ thống giao tiếp nội bộ <ShieldCheck className="w-4 h-4" />
          </p>
        </div>
        <button
          onClick={() => setShowNewChatModal(true)}
          className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 rounded-none"
        >
          <Plus className="w-4 h-4" /> Bắt đầu kết nối
        </button>
      </div>

      <div
        className="border border-zinc-200 bg-white flex h-[calc(100vh-200px)] min-h-[500px]"
      >
        <div
          className={`w-full md:w-[320px] lg:w-[380px] border-r border-zinc-200 flex flex-col shrink-0 ${
            selectedConv ? "hidden md:flex" : "flex"
          }`}
        >
          <div className="p-4 border-b border-zinc-200 bg-zinc-50 flex items-center justify-between shrink-0">
            <span className="text-xs font-semibold text-black">Hộp thư</span>
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
                      <span
                        className={`text-sm text-black truncate ${
                          conv.unread_count > 0 ? "font-semibold" : "font-medium"
                        }`}
                      >
                        {conv.other_user?.full_name || conv.other_user?.username}
                      </span>
                      <span
                        className={`text-[10px] shrink-0 ${
                          conv.unread_count > 0 ? "text-black font-semibold" : "text-zinc-500 font-medium"
                        }`}
                      >
                        {conv.last_message?.created_at
                          ? new Date(conv.last_message.created_at).toLocaleTimeString("vi-VN", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : ""}
                      </span>
                    </div>
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={`text-xs truncate ${
                          conv.unread_count > 0 ? "text-black font-semibold" : "text-zinc-500 font-medium"
                        }`}
                      >
                        {conv.last_message?.content || "Chưa có tin nhắn"}
                      </p>
                      {conv.unread_count > 0 && (
                        <div className="w-2 h-2 bg-black shrink-0 rounded-none"></div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-24 flex flex-col items-center justify-center opacity-50 space-y-4">
                <MessageSquare className="w-10 h-10 text-black stroke-[1]" />
                <p className="text-xs font-medium text-black">Hệ thống ghi nhận rỗng</p>
              </div>
            )}
          </div>
        </div>

        <div className={`flex-1 flex flex-col ${!selectedConv ? "hidden md:flex" : "flex"}`}>
          {selectedConv ? (
            <>
              <div className="p-4 border-b border-zinc-200 bg-white flex items-center justify-between shrink-0">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedConv(null)}
                    className="md:hidden p-2 text-zinc-500"
                  >
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
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className="w-1.5 h-1.5 bg-black rounded-none"></div>
                      <span className="text-[10px] text-zinc-500 font-medium">Bảo mật hai chiều</span>
                    </div>
                  </div>
                </div>
                <button className="p-2 text-zinc-400">
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-50/50">
                {loadingMsgs ? (
                  <div className="flex h-full flex-col items-center justify-center gap-4">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                    <span className="text-xs font-medium text-zinc-500">Đang tải lịch sử</span>
                  </div>
                ) : (
                  messages.map((msg, i) => {
                    const isSender = msg.sender_id === user.id;
                    return (
                      <div
                        key={i}
                        className={`flex flex-col ${isSender ? "items-end" : "items-start"}`}
                      >
                        <div
                          className={`max-w-[75%] px-4 py-3 text-sm leading-relaxed rounded-none ${
                            isSender
                              ? "bg-black text-white"
                              : "bg-white text-black border border-zinc-200"
                          }`}
                        >
                          {msg.content}
                        </div>
                        <div className="flex items-center gap-1.5 mt-1.5 px-1">
                          <span className="text-[10px] font-medium text-zinc-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(msg.created_at).toLocaleTimeString("vi-VN", {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                          {isSender && <CheckCircle2 className="w-3 h-3 text-zinc-400" />}
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-4 border-t border-zinc-200 bg-white shrink-0">
                <div className="flex gap-4">
                  <input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Nhập nội dung"
                    className="flex-1 h-12 px-4 bg-zinc-50 border border-zinc-200 text-sm font-medium focus:outline-none focus:border-black rounded-none placeholder:text-zinc-400"
                  />
                  <button
                    onClick={handleSend}
                    disabled={sending || !newMessage.trim()}
                    className="h-12 px-6 bg-black text-white flex items-center justify-center gap-2 disabled:opacity-50 rounded-none shrink-0"
                  >
                    <span className="text-xs font-medium hidden sm:inline">Gửi</span>
                    {sending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-400 bg-zinc-50/50">
              <div className="w-16 h-16 border border-zinc-200 flex items-center justify-center mb-4 bg-white">
                <MessageSquare className="w-6 h-6 stroke-[1.5]" />
              </div>
              <p className="text-sm font-semibold text-black">Hệ thống truyền tin</p>
              <p className="text-xs font-medium text-zinc-500 mt-1">Chọn một hội thoại để bắt đầu</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
