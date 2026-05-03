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
  X,
  MessageCircle,
  UserPlus,
  Sparkles,
  Zap,
  MoreVertical,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
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
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <Modal
        isOpen={showNewChatModal}
        onClose={() => setShowNewChatModal(false)}
        className="max-w-xl"
      >
        <ModalHeader>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-black flex items-center justify-center rounded-sm">
              <UserPlus className="w-6 h-6 text-white" />
            </div>
            <div>
              <ModalTitle>Bắt đầu hội thoại mới</ModalTitle>
              <ModalDescription>Tìm kiếm tri thức trong mạng lưới DocLib</ModalDescription>
            </div>
          </div>
        </ModalHeader>

        <ModalContent>
          <div className="space-y-10">
            <div className="relative group">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-200 group-focus-within:text-black transition-colors" />
              <input
                value={searchQuery}
                onChange={(e) => handleSearchUsers(e.target.value)}
                placeholder=""
                className="w-full h-16 pl-16 pr-6 font-bold text-sm bg-white border border-zinc-100 focus:border-black outline-none rounded-sm transition-colors"
              />
            </div>
            
            <div className="max-h-[400px] overflow-y-auto space-y-3 pr-2 custom-scrollbar">
              {searching ? (
                <div className="py-20 flex flex-col items-center gap-6">
                  <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
                  <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                    Đang tra cứu dữ liệu
                  </span>
                </div>
              ) : searchResults.length > 0 ? (
                searchResults.map((u) => (
                  <div
                    key={u._id || u.id}
                    onClick={() => startNewChat(u)}
                    className="flex items-center justify-between p-6 border border-zinc-50 hover:border-zinc-200 cursor-pointer rounded-sm transition-all group"
                  >
                    <div className="flex items-center gap-6">
                      <div className="w-16 h-16 border border-zinc-100 flex items-center justify-center overflow-hidden bg-white rounded-sm">
                        {u.avatar_url ? (
                          <img
                            src={u.avatar_url}
                            className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all"
                            alt=""
                          />
                        ) : (
                          <User className="w-6 h-6 text-zinc-200" />
                        )}
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-bold text-black tracking-tight">
                          {u.display_name || u.full_name || u.username}
                        </p>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                          ID: <span className="text-zinc-500">{u.slug || u.username}</span>
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-zinc-100 group-hover:text-black group-hover:translate-x-1 transition-all" />
                  </div>
                ))
              ) : searchQuery.length >= 2 ? (
                <div className="text-center py-20 bg-white border border-dashed border-zinc-100 rounded-sm">
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">
                    Hệ thống không tìm thấy kết quả phù hợp
                  </p>
                </div>
              ) : (
                <div className="text-center py-20 opacity-30">
                  <Zap className="w-12 h-12 mx-auto text-zinc-100 mb-6" />
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">
                    Khởi tạo tìm kiếm tri thức
                  </p>
                </div>
              )}
            </div>
          </div>
        </ModalContent>
      </Modal>

      <header
        className="mb-12 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 "
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
            Trò chuyện
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Secure Communication Node{" "}
            <ShieldCheck className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
        <button
          onClick={() => setShowNewChatModal(true)}
          className="h-14 px-10 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-4 active:scale-[0.98] rounded-sm"
        >
          <Plus className="w-4 h-4" /> Bắt đầu kết nối
        </button>
      </header>

      <div
        className="max-w-[1440px] h-[75vh] min-h-[600px] border border-zinc-100 bg-white flex overflow-hidden rounded-sm"
        style={{
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0)" : "translateY(10px)",
        }}
      >
        <div
          className={`w-full md:w-[400px] border-r border-zinc-100 flex flex-col ${selectedConv ? "hidden md:flex" : "flex"}`}
        >
          <div className="p-8 border-b border-zinc-50 bg-white">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-black uppercase tracking-widest">
                Hộp thư cá nhân
              </span>
              <Sparkles className="w-3.5 h-3.5 text-zinc-200" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-hide">
            {loadingConv ? (
              <div className="p-20 flex flex-col items-center gap-6">
                <Loader2 className="w-8 h-8 animate-spin text-zinc-100" />
                <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                  Đang đồng bộ
                </span>
              </div>
            ) : conversations.length > 0 ? (
              conversations.map((conv) => (
                <div
                  key={conv.other_user_id}
                  onClick={() => selectConversation(conv)}
                  className={`p-8 border-b border-zinc-50 cursor-pointer group ${
                    selectedConv?.other_user_id === conv.other_user_id
                      ? "bg-white border-l-4 border-l-black"
                      : ""
                  }`}
                >
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 border border-zinc-100 flex items-center justify-center overflow-hidden shrink-0 bg-white rounded-sm">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover grayscale "
                        />
                      ) : (
                        <User className="w-6 h-6 text-zinc-100" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-black text-sm tracking-tight truncate  ">
                          {conv.other_user?.display_name ||
                            conv.other_user?.username}
                        </h4>
                        <span className="text-[9px] text-zinc-300 font-bold uppercase tracking-widest">
                          {conv.last_message?.created_at
                            ? new Date(
                                conv.last_message.created_at,
                              ).toLocaleTimeString("vi-VN", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : ""}
                        </span>
                      </div>
                      <p
                        className={`text-[11px] truncate leading-relaxed ${
                          conv.unread_count > 0
                            ? "text-black font-bold"
                            : "text-zinc-400"
                        }`}
                      >
                        {conv.last_message?.content ||
                          "Khởi tạo hội thoại kết nối"}
                      </p>
                    </div>
                    {conv.unread_count > 0 && (
                      <div className="w-2.5 h-2.5 bg-black rounded-full shrink-0"></div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="py-40 flex flex-col items-center justify-center opacity-20 space-y-8">
                <MessageSquare className="w-16 h-16 text-black stroke-[1]" />
                <p className="text-[11px] font-bold uppercase tracking-[0.3em]">
                  Hệ thống ghi nhận rỗng
                </p>
              </div>
            )}
          </div>
        </div>

        <div
          className={`flex-1 flex flex-col ${!selectedConv ? "hidden md:flex" : "flex"}`}
        >
          {selectedConv ? (
            <>
              <div className="p-8 border-b border-zinc-100 flex items-center justify-between bg-white z-10">
                <div className="flex items-center gap-6">
                  <button
                    onClick={() => setSelectedConv(null)}
                    className="md:hidden w-10 h-10 border border-zinc-100 flex items-center justify-center "
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  <div className="w-14 h-14 border border-zinc-100 overflow-hidden bg-white rounded-sm">
                    {selectedConv.other_user?.avatar_url ? (
                      <img
                        src={selectedConv.other_user.avatar_url}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-100">
                        <User className="w-6 h-6" />
                      </div>
                    )}
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-bold text-xl tracking-tighter text-black">
                      {selectedConv.other_user?.display_name ||
                        selectedConv.other_user?.username}
                    </h3>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-black rounded-full animate-pulse"></div>
                      <p className="text-[9px] text-zinc-400 font-bold uppercase tracking-widest">
                        Bảo mật định danh mức cao
                      </p>
                    </div>
                  </div>
                </div>
                <button className="w-12 h-12 flex items-center justify-center border border-zinc-100 rounded-sm">
                  <MoreVertical className="w-5 h-5 text-zinc-300 " />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-12 space-y-10 bg-white/20 scroll-smooth scrollbar-hide">
                {loadingMsgs ? (
                  <div className="flex h-full flex-col items-center justify-center gap-6">
                    <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
                    <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
                      Đang tải lịch sử
                    </span>
                  </div>
                ) : (
                  messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${
                        msg.sender_id === user.id
                          ? "justify-end"
                          : "justify-start"
                      } animate-in fade-in slide-in-from-bottom-4 `}
                    >
                      <div
                        className={`max-w-[70%] p-8 text-sm leading-relaxed border selection:bg-black selection:text-white rounded-sm ${
                          msg.sender_id === user.id
                            ? "bg-black text-white border-black"
                            : "bg-white text-black font-medium border-zinc-100"
                        }`}
                      >
                        {msg.content}
                        <div
                          className={`text-[9px] font-bold mt-6 opacity-30 flex items-center gap-2 ${
                            msg.sender_id === user.id
                              ? "justify-end"
                              : "justify-start"
                          }`}
                        >
                          <Clock className="w-3 h-3" />
                          {new Date(msg.created_at).toLocaleTimeString(
                            "vi-VN",
                            {
                              hour: "2-digit",
                              minute: "2-digit",
                            },
                          )}
                          {msg.sender_id === user.id && (
                            <CheckCircle2 className="w-3 h-3 text-white/40" />
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-10 border-t border-zinc-100 bg-white">
                <div className="flex gap-6">
                  <input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder=""
                    className="flex-1 h-16 px-8 bg-white border border-zinc-100 text-sm font-bold focus:outline-none focus:border-black rounded-sm placeholder:text-zinc-200"
                  />
                  <button
                    onClick={handleSend}
                    disabled={sending || !newMessage.trim()}
                    className="bg-black text-white h-16 px-10 flex items-center justify-center gap-4 active:scale-[0.98] disabled:opacity-30 rounded-sm"
                  >
                    <span className="text-[11px] font-bold uppercase tracking-widest hidden sm:inline">
                      Gửi đi
                    </span>
                    {sending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-100 bg-white/5 opacity-50">
              <div className="w-32 h-32 bg-white border border-zinc-100 flex items-center justify-center mb-10 rounded-sm">
                <MessageCircle className="w-14 h-14 stroke-[0.5]" />
              </div>
              <div className="text-center space-y-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.3em]">
                  Hệ thống truyền tin DocLib
                </p>
                <p className="text-[10px] font-bold uppercase tracking-widest italic">
                  Chọn một thực thể để bắt đầu hội thoại bảo mật
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const Clock = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);
