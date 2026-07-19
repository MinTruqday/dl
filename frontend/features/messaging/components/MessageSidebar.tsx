import React, { useState, useEffect } from "react";
import { Search, Edit, User, Users } from "lucide-react";
import { formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";
import { Modal, ModalHeader, ModalTitle, ModalContent } from "@/shared/components/common/Modal";
import { Loader2 } from "lucide-react";
import { searchUsersAPI } from "@/features/messaging/services/thread.service";
import { showToast } from "@/core/components/Toast";

interface MessageSidebarProps {
  user: any;
  conversations: any[];
  selectedConv: any;
  onlineUsers: {[key: string]: boolean};
  onSelectConversation: (conv: any) => void;
  onStartNewChat: (otherUser: any) => void;
}

export function MessageSidebar({
  user,
  conversations,
  selectedConv,
  onlineUsers,
  onSelectConversation,
  onStartNewChat,
}: MessageSidebarProps) {
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [localSearch, setLocalSearch] = useState("");

  const handleSearchUsers = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) return setSearchResults([]);
    setSearching(true);
    try {
      const res = await searchUsersAPI(q);
      setSearchResults(res.data || res || []);
    } catch (err: any) {
      showToast("Lỗi tìm kiếm người dùng", "error");
    } finally {
      setSearching(false);
    }
  };

  const startNewChat = (otherUser: any) => {
    onStartNewChat(otherUser);
    setShowNewChatModal(false);
    setSearchQuery("");
    setSearchResults([]);
  };

  const filteredConversations = conversations.filter(c => {
    const isGroup = c.type === "group";
    const name = isGroup ? c.group_name : c.other_user?.full_name;
    return name?.toLowerCase().includes(localSearch.toLowerCase());
  });

  const sortedConversations = [...filteredConversations].sort((a, b) => {
    const aPinned = user?.pinned_conversations?.includes(a.other_user_id || a._id) ? 1 : 0;
    const bPinned = user?.pinned_conversations?.includes(b.other_user_id || b._id) ? 1 : 0;
    if (aPinned !== bPinned) return bPinned - aPinned;
    return new Date(b.last_message?.created_at || 0).getTime() - new Date(a.last_message?.created_at || 0).getTime();
  });

  return (
    <div className="w-[320px] flex-shrink-0 flex flex-col border-r border-[#E8E8ED] bg-[#F5F5F7] h-full relative z-10">
      <div className="p-4 flex items-center justify-between">
        <h2 className="text-[24px] font-bold tracking-tight">Đoạn chat</h2>
        <button
          onClick={() => setShowNewChatModal(true)}
          className="w-9 h-9 rounded-full bg-white flex items-center justify-center shadow-sm border border-[#E8E8ED] hover:bg-[#F2F2F7] text-[#0071E3] transition-colors"
        >
          <Edit className="w-4 h-4" />
        </button>
      </div>

      <div className="px-4 pb-2">
        <div className="relative">
          <Search className="w-4 h-4 text-[#A1A1A6] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Tìm kiếm"
            className="w-full bg-[#E8E8ED] text-[#1D1D1F] placeholder:text-[#A1A1A6] pl-9 pr-4 py-1.5 rounded-[8px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/20 transition-all text-[15px]"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto hide-scrollbar pb-4 pt-2 px-2 space-y-1">
        {sortedConversations.map((c) => {
          const isSelected = selectedConv && (selectedConv.other_user_id === c.other_user_id && selectedConv._id === c._id);
          const isGroup = c.type === "group";
          const isOnline = isGroup ? false : onlineUsers[c.other_user_id];
          const hasUnread = c.unread_count > 0;
          const isPinned = user?.pinned_conversations?.includes(c.other_user_id || c._id);

          return (
            <div
              key={c._id || c.id}
              onClick={() => onSelectConversation(c)}
              className={`flex items-center gap-3 p-2.5 rounded-[12px] cursor-pointer transition-colors ${
                isSelected ? "bg-[#0071E3] text-white" : "hover:bg-white text-[#1D1D1F]"
              }`}
            >
              <div className="relative w-12 h-12 flex-shrink-0">
                <div className={`w-full h-full rounded-full flex items-center justify-center overflow-hidden border border-[#E8E8ED] ${isSelected ? 'border-white/20' : ''}`}>
                  {isGroup ? (
                    c.avatar_url ? (
                      <img src={c.avatar_url} className="w-full h-full object-cover" alt="" />
                    ) : (
                      <Users className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-[#86868B]'}`} />
                    )
                  ) : c.other_user?.avatar_url ? (
                    <img src={c.other_user.avatar_url} className="w-full h-full object-cover" alt="" />
                  ) : (
                    <User className={`w-6 h-6 ${isSelected ? 'text-white' : 'text-[#86868B]'}`} />
                  )}
                </div>
                {!isGroup && isOnline && (
                  <span className={`absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 border-2 rounded-full ${isSelected ? 'border-[#0071E3]' : 'border-[#F5F5F7] group-hover:border-white'}`} />
                )}
              </div>
              <div className="flex-1 min-w-0 flex flex-col justify-center">
                <div className="flex items-center justify-between mb-0.5">
                  <span className={`font-semibold text-[15px] truncate ${hasUnread && !isSelected ? "text-[#1D1D1F]" : ""}`}>
                    {isGroup ? c.group_name : c.other_user?.full_name || "Người dùng"}
                  </span>
                  {c.last_message && (
                    <span className={`text-[12px] shrink-0 ml-2 ${isSelected ? "text-white/80" : hasUnread ? "text-[#0071E3] font-medium" : "text-[#86868B]"}`}>
                      {formatRelativeTime(parseUTC(c.last_message.created_at))}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <p className={`text-[13px] truncate ${isSelected ? "text-white/90" : hasUnread ? "text-[#1D1D1F] font-semibold" : "text-[#6E6E73]"}`}>
                    {c.last_message?.is_recalled
                      ? "Tin nhắn đã thu hồi"
                      : c.last_message?.content ||
                        (c.last_message?.image_url ? "[Hình ảnh]" : c.last_message?.poll_data ? "[Bình chọn]" : "Chưa có tin nhắn")}
                  </p>
                  {hasUnread && !isSelected && (
                    <span className="w-2.5 h-2.5 bg-[#0071E3] rounded-full shrink-0 ml-2" />
                  )}
                  {isPinned && !hasUnread && (
                    <div className={`shrink-0 ml-2 ${isSelected ? "text-white/80" : "text-[#A1A1A6]"}`}>
                      📍
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <Modal isOpen={showNewChatModal} onClose={() => setShowNewChatModal(false)} className="max-w-xl">
        <ModalHeader>
          <ModalTitle>Bắt đầu hội thoại mới</ModalTitle>
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
                  className="flex items-center justify-between p-4 bg-white rounded-[10px] cursor-pointer hover:bg-[#F5F5F7] border border-[#E8E8ED]"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-[#F5F5F7] rounded-full overflow-hidden flex items-center justify-center">
                      {u.avatar_url ? (
                        <img src={u.avatar_url} className="w-full h-full object-cover" alt="" />
                      ) : (
                        <User className="w-5 h-5 text-[#A1A1A6]" />
                      )}
                    </div>
                    <div>
                      <h4 className="font-semibold text-[15px]">{u.full_name}</h4>
                      <p className="text-[13px] text-[#6E6E73]">{u.email}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center text-[#6E6E73] text-[15px]">
                {searchQuery.length >= 2 ? "Không tìm thấy người dùng" : "Gõ tên hoặc email để tìm kiếm"}
              </div>
            )}
          </div>
        </ModalContent>
      </Modal>
    </div>
  );
}
