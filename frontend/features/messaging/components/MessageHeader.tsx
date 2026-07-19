import React, { useState } from "react";
import { User, Users, Info, ArrowLeft, Phone, Video } from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent } from "@/shared/components/common/Modal";

interface MessageHeaderProps {
  selectedConv: any;
  onlineUsers: {[key: string]: boolean};
  onBack: () => void;
  onOpenSettings: () => void;
}

export function MessageHeader({ selectedConv, onlineUsers, onBack, onOpenSettings }: MessageHeaderProps) {
  if (!selectedConv) return null;

  const isGroup = selectedConv.type === "group";
  const isOnline = isGroup ? false : onlineUsers[selectedConv.other_user_id];
  const avatarUrl = isGroup ? selectedConv.avatar_url : selectedConv.other_user?.avatar_url;
  const name = isGroup ? selectedConv.group_name : selectedConv.other_user?.full_name || "Người dùng";

  return (
    <div className="h-[60px] border-b border-[#E8E8ED] bg-white/80 backdrop-blur-md flex items-center justify-between px-4 sticky top-0 z-20 shadow-sm">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="md:hidden w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#F5F5F7] text-[#0071E3]"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="relative">
          <div className="w-10 h-10 rounded-full flex items-center justify-center overflow-hidden bg-[#F5F5F7] border border-[#E8E8ED]">
            {avatarUrl ? (
              <img src={avatarUrl} className="w-full h-full object-cover" alt="" />
            ) : isGroup ? (
              <Users className="w-5 h-5 text-[#86868B]" />
            ) : (
              <User className="w-5 h-5 text-[#86868B]" />
            )}
          </div>
          {!isGroup && isOnline && (
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
          )}
        </div>
        <div>
          <h3 className="font-semibold text-[15px] text-[#1D1D1F]">{name}</h3>
          {!isGroup && (
            <p className="text-[12px] text-[#6E6E73]">{isOnline ? "Đang hoạt động" : "Ngoại tuyến"}</p>
          )}
          {isGroup && (
            <p className="text-[12px] text-[#6E6E73]">{selectedConv.participants?.length || 0} thành viên</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1">
        <button className="w-9 h-9 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full transition-colors opacity-50 cursor-not-allowed" title="Gọi thoại (Sắp ra mắt)">
          <Phone className="w-[18px] h-[18px]" />
        </button>
        <button className="w-9 h-9 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full transition-colors opacity-50 cursor-not-allowed" title="Gọi video (Sắp ra mắt)">
          <Video className="w-[18px] h-[18px]" />
        </button>
        <button
          onClick={onOpenSettings}
          className="w-9 h-9 flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full transition-colors ml-1"
        >
          <Info className="w-[18px] h-[18px]" />
        </button>
      </div>
    </div>
  );
}
