"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import AppShell from "@/app/components/AppShell";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  getConversationsAPI,
  getMessagesAPI,
  sendMessageAPI,
  searchUsersAPI,
} from "@/app/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Notification } from "@/app/components/NotificationToast";
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
} from "lucide-react";
import { useRouter } from "next/navigation";

export default function MessagesPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConv, setSelectedConv] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loadingConv, setLoadingConv] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [sending, setSending] = useState(false);
  const [visible, setVisible] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversationsAPI();
      setConversations(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tải hội thoại:", err);
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
      const data = await getMessagesAPI(conv.other_user_id);
      setMessages(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tải tin nhắn:", err);
    } finally {
      setLoadingMsgs(false);
    }
  };

  const handleSend = async () => {
    if (!newMessage.trim() || !selectedConv) return;
    setSending(true);
    setNotification(null);
    try {
      const data = await sendMessageAPI(selectedConv.other_user_id, newMessage.trim());
      const msg = data.data || data;
      setMessages((prev) => [...prev, msg]);
      setNewMessage("");
      loadConversations();
    } catch (err: any) {
      console.error("Lỗi gửi tin nhắn:", err);
      setNotification({ type: "error", text: "Không thể gửi tin nhắn. Vui lòng thử lại sau" });
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
      const data = await searchUsersAPI(q);
      setSearchResults(data.data || data || []);
    } catch (err: any) {
      console.error("Lỗi tìm kiếm người dùng:", err);
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
      <AppShell>
        <div className="flex h-[80vh] items-center justify-center">
          <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
        </div>
      </AppShell>
    );
  }

  if (!user) return null;

  return (
    <AppShell>
      {showNewChatModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowNewChatModal(false)} />
          <div className="bg-white w-full max-w-md relative border border-zinc-200 animate-in zoom-in-95 duration-200">
            <div className="p-8 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/30">
              <h3 className="text-[11px] font-bold flex items-center gap-2">
                <Plus className="w-4 h-4" /> Bắt đầu trò chuyện mới
              </h3>
              <button onClick={() => setShowNewChatModal(false)} className="p-1 hover:bg-zinc-100 transition-colors">
                <X className="w-5 h-5 text-zinc-400" />
              </button>
            </div>
            <div className="p-8">
              <div className="relative mb-8">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <Input
                  value={searchQuery}
                  onChange={(e) => handleSearchUsers(e.target.value)}
                  placeholder=""
                  className="h-14 pl-12 font-bold text-xs border-zinc-200 focus:border-black transition-all"
                />
              </div>
              <div className="max-h-[300px] overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-zinc-200">
                {searching ? (
                  <div className="py-10 flex justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-200" />
                  </div>
                ) : searchResults.length > 0 ? (
                  searchResults.map((u) => (
                    <div
                      key={u._id || u.id}
                      onClick={() => startNewChat(u)}
                      className="flex items-center justify-between p-4 border border-zinc-100 hover:border-black cursor-pointer transition-all"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 border border-zinc-200 flex items-center justify-center overflow-hidden">
                          {u.avatar_url ? (
                            <img src={u.avatar_url} className="w-full h-full object-cover" alt="" />
                          ) : (
                            <User className="w-5 h-5 text-zinc-200" />
                          )}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-black tracking-tight">{u.full_name || u.username}</p>
                          <p className="text-[9px] font-bold text-zinc-400">@{u.slug || u.username}</p>
                        </div>
                      </div>
                      <UserPlus className="w-4 h-4 text-zinc-300" />
                    </div>
                  ))
                ) : searchQuery.length >= 2 ? (
                  <p className="text-center py-10 text-[10px] font-bold text-zinc-300">Không tìm thấy ai phù hợp</p>
                ) : (
                  <p className="text-center py-10 text-[10px] font-bold text-zinc-300">Nhập ít nhất 2 ký tự</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div
        className="max-w-6xl mx-auto h-[calc(100vh-14rem)] min-h-[600px] border border-zinc-200 bg-white flex transition-all duration-300 overflow-hidden font-sans"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className={`w-full md:w-96 border-r border-zinc-200 flex flex-col ${selectedConv ? "hidden md:flex" : "flex"}`}>
          <div className="p-8 border-b border-zinc-200 bg-zinc-50/50 flex items-center justify-between">
            <h2 className="text-[11px] font-bold text-black flex items-center gap-3">
              <MessageSquare className="w-4 h-4" /> Trò chuyện
            </h2>
            <button
              onClick={() => setShowNewChatModal(true)}
              className="w-10 h-10 border border-zinc-200 bg-white text-black hover:border-black transition-all flex items-center justify-center active:scale-95"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-100">
            {loadingConv ? (
              <div className="p-16 text-center text-zinc-400">
                <Loader2 className="w-8 h-8 animate-spin mx-auto text-zinc-200" />
              </div>
            ) : conversations.length > 0 ? (
              conversations.map((conv) => (
                <div
                  key={conv.other_user_id}
                  onClick={() => selectConversation(conv)}
                  className={`p-6 border-b border-zinc-50 cursor-pointer transition-all hover:bg-zinc-50/50 ${
                    selectedConv?.other_user_id === conv.other_user_id ? "bg-zinc-50 border-l-4 border-l-black" : ""
                  }`}
                >
                  <div className="flex items-center gap-5">
                    <div className="w-14 h-14 border border-zinc-200 flex items-center justify-center overflow-hidden shrink-0 bg-white">
                      {conv.other_user?.avatar_url ? (
                        <img src={conv.other_user.avatar_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <User className="w-6 h-6 text-zinc-200" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1.5">
                        <h4 className="font-bold text-black text-xs tracking-tight truncate">
                          {conv.other_user?.full_name || conv.other_user?.username}
                        </h4>
                        <span className="text-[9px] text-zinc-300 font-bold">
                          {conv.last_message?.created_at
                            ? new Date(conv.last_message.created_at).toLocaleDateString("vi-VN")
                            : ""}
                        </span>
                      </div>
                      <p
                        className={`text-[11px] truncate leading-relaxed ${
                          conv.unread_count > 0 ? "text-black font-bold" : "text-zinc-400"
                        }`}
                      >
                        {conv.last_message?.content || "Nhấn để bắt đầu hội thoại"}
                      </p>
                    </div>
                    {conv.unread_count > 0 && (
                      <div className="w-2 h-2 bg-black rounded-full shrink-0 animate-pulse"></div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-16 text-center flex flex-col items-center gap-6 opacity-20">
                <MessageCircle className="w-12 h-12 text-black" />
                <p className="text-[10px] font-bold">Chưa có hội thoại nào</p>
              </div>
            )}
          </div>
        </div>

        <div className={`flex-1 flex flex-col ${!selectedConv ? "hidden md:flex" : "flex"}`}>
          {selectedConv ? (
            <>
              <div className="p-6 border-b border-zinc-100 flex items-center justify-between bg-white z-10">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setSelectedConv(null)}
                    className="md:hidden p-2 text-black hover:bg-zinc-50 transition-all"
                  >
                    <ArrowLeft className="w-5 h-5" />
                  </button>
                  <div className="w-12 h-12 border border-zinc-200 overflow-hidden bg-zinc-50">
                    {selectedConv.other_user?.avatar_url ? (
                      <img src={selectedConv.other_user.avatar_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-200">
                        <User className="w-6 h-6" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="font-bold text-black text-sm tracking-tight">
                      {selectedConv.other_user?.full_name || selectedConv.other_user?.username}
                    </h3>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-black rounded-full"></div>
                      <p className="text-[10px] text-zinc-400 font-bold">Đang trực tuyến</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-10 space-y-8 bg-zinc-50/30 scroll-smooth scrollbar-thin scrollbar-thumb-zinc-200">
                {loadingMsgs ? (
                  <div className="flex h-full items-center justify-center">
                    <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
                  </div>
                ) : (
                  messages.map((msg, i) => (
                    <div
                      key={i}
                      className={`flex ${
                        msg.sender_id === user.id ? "justify-end" : "justify-start"
                      } animate-in fade-in slide-in-from-bottom-2 duration-300`}
                    >
                      <div
                        className={`max-w-[65%] p-6 text-xs leading-loose border ${
                          msg.sender_id === user.id
                            ? "bg-black text-white border-black"
                            : "bg-white text-black font-medium border-zinc-100"
                        }`}
                      >
                        {msg.content}
                        <div
                          className={`text-[8px] font-bold mt-4 opacity-40 ${
                            msg.sender_id === user.id ? "text-right" : "text-left"
                          }`}
                        >
                          {new Date(msg.created_at).toLocaleTimeString("vi-VN", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-8 border-t border-zinc-200 bg-white">
                {notification && <Notification type={notification.type} message={notification.text} className="mb-4" />}
                <div className="flex gap-4">
                  <input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder=""
                    className="flex-1 h-16 px-6 bg-zinc-50 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all duration-150"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={sending || !newMessage.trim()}
                    className="bg-black text-white hover:bg-zinc-800 h-16 w-16 flex items-center justify-center p-0 active:scale-95 transition-all"
                  >
                    {sending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-200 bg-zinc-50/10">
              <div className="w-24 h-24 bg-white border border-zinc-200 flex items-center justify-center mb-8">
                <MessageCircle className="w-10 h-10" />
              </div>
              <p className="text-[11px] font-bold text-zinc-300">Chọn hội thoại để bắt đầu kết nối tri thức</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
