import React from "react";
import { API_URL } from "@/core/config";
import { FileText, Reply, Pin, PinOff, Edit2, Trash2, Undo2, ChevronRight } from "lucide-react";
import { formatRelativeTime, parseUTC } from "@/shared/lib/app_utils";
import { PollMessage } from "@/features/messaging/components/PollMessage";

// Simple Audio Player mockup since CustomAudioPlayer is locally defined in page.tsx currently
// We should ideally move CustomAudioPlayer to a separate file, but for now we inline or assume it's passed
const CustomAudioPlayer = ({ src, isSender }: { src: string, isSender: boolean }) => (
  <audio controls src={src} className={`h-8 ${isSender ? "brightness-125" : ""}`} />
);

interface MessageBubbleProps {
  msg: any;
  isSender: boolean;
  showTime: boolean;
  conversationTheme: string;
  user: any;
  activeMsgMenuId: string | null;
  showDeleteSubMenu: string | null;
  onDoubleClick: (msg: any, rect: any, isSender: boolean) => void;
  onReaction: (msgId: string, emoji: string) => void;
  onReply: (msg: any) => void;
  onPin: (msgId: string) => void;
  onEdit: (msg: any) => void;
  onToggleDeleteMenu: (msgId: string | null) => void;
  onRecall: (msgId: string) => void;
  onDeleteForMe: (msgId: string) => void;
  onForward: (msgId: string) => void;
  onVote: (msgId: string, optionId: string) => void;
  onScrollToReply: (replyId: string) => void;
}

export function MessageBubble({
  msg,
  isSender,
  showTime,
  conversationTheme,
  user,
  activeMsgMenuId,
  showDeleteSubMenu,
  onDoubleClick,
  onReaction,
  onReply,
  onPin,
  onEdit,
  onToggleDeleteMenu,
  onRecall,
  onDeleteForMe,
  onForward,
  onVote,
  onScrollToReply
}: MessageBubbleProps) {
  const getThemeBgClass = (theme: string) => {
    switch (theme) {
      case "ocean": return "bg-gradient-to-br from-[#0071E3] to-[#409CFF]";
      case "sunset": return "bg-gradient-to-br from-[#FF453A] to-[#FF9F0A]";
      case "forest": return "bg-gradient-to-br from-[#32ADE6] to-[#34C759]";
      case "lavender": return "bg-gradient-to-br from-[#AF52DE] to-[#FF375F]";
      case "monochrome": return "bg-gradient-to-br from-[#1D1D1F] to-[#6E6E73]";
      case "default":
      default: return "bg-[#0071E3]";
    }
  };

  const msgId = msg._id || msg.id;

  return (
    <div className={`flex flex-col transition-colors duration-500 mb-2 ${isSender ? "items-end" : "items-start"}`}>
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
          onDoubleClick(msg, rect, isSender);
        }}
      >
        <div
          className={`rounded-[18px] flex flex-col gap-2 ${
            msg.is_recalled
              ? "bg-transparent border border-dashed border-[#D2D2D7] text-[#6E6E73] min-h-[38px] p-4 justify-center"
              : isSender
              ? `${getThemeBgClass(conversationTheme)} text-white p-4`
              : "bg-white border border-[#E8E8ED] text-[#1D1D1F] p-4"
          } relative cursor-pointer select-none`}
        >
          {msg.reply_to && !msg.is_recalled && (
            <div 
              onClick={() => {
                const replyId = typeof msg.reply_to === 'object' ? msg.reply_to._id || msg.reply_to.id : msg.reply_to;
                if (replyId) onScrollToReply(replyId);
              }}
              className={`text-[12px] px-2 py-1.5 rounded-[10px] truncate max-w-[250px] opacity-80 cursor-pointer hover:opacity-100 transition-opacity ${isSender ? "bg-black/20 text-white" : "bg-[#E8E8ED] text-[#6E6E73]"}`}
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
                <a key={idx} href={att.url.startsWith("http") ? att.url : `${API_URL}/storage/${att.url}`} target="_blank" rel="noreferrer" className={`flex items-center gap-2 p-2 rounded-[10px] ${isSender ? "bg-black/20 text-white" : "bg-[#E8E8ED] text-[#1D1D1F]"}`}>
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

          {!msg.is_recalled && msg.poll_data && (
            <PollMessage 
              messageId={msgId}
              pollData={msg.poll_data}
              currentUserId={user?._id}
              onVote={onVote}
            />
          )}
          
          {!msg.is_recalled && !msg.poll_data && msg.content && msg.content !== "Tin nhắn thoại" && (
            <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">{msg.content}</p>
          )}
          
          {msg.is_recalled && (
            <span className="text-[13px] italic flex items-center h-full">Tin nhắn đã thu hồi</span>
          )}
        </div>
        
        {/* Reaction badge & Time */}
        <div className={`flex items-center gap-2 mt-1 ${isSender ? "flex-row-reverse mr-1" : "flex-row ml-1"}`}>
          <span className="text-[10px] text-[#6E6E73] whitespace-nowrap">
            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            {msg.is_edited && " • Đã chỉnh sửa"}
          </span>
          {msg.reactions && msg.reactions.length > 0 && (
            <div className="flex items-center bg-white border border-[#E8E8ED] rounded-full px-1.5 py-0.5 shadow-sm -mt-3 z-10 relative">
              {Array.from(new Set(msg.reactions.map((r: any) => r.reaction))).slice(0, 3).map((r: any, i: number) => (
                <span key={i} className="text-[12px]">{r}</span>
              ))}
              {msg.reactions.length > 1 && (
                <span className="text-[10px] text-[#6E6E73] ml-1 font-medium">{msg.reactions.length}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
