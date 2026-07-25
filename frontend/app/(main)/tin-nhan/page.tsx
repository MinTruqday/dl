"use client";
import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getConversationsAPI,
  forwardMessageAPI,
  createPollAPI,
  votePollAPI,
  getMessagesAPI,
  sendMessageAPI,
  togglePinAPI,
  editMessageAPI,
  recallMessageAPI,
  deleteMessageForMeAPI,
  restoreMessageAPI,
  searchMessagesAPI,
  globalSearchAPI,
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
  updateConversationSettingsAPI,
  deleteConversationAPI,
  getThreadRepliesAPI,
  getQuickRepliesAPI,
  markUnreadAPI,
  saveToCloudAPI,
  updateThemeAPI,
  createAnnouncementAPI,
  generateGroupInviteAPI,
  joinByInviteAPI,
  setNicknameAPI,
  shareContactCardAPI,
  archiveThreadAPI,
  setPinLockAPI,
  setMessageAlarmAPI,
  transferGroupOwnershipAPI,
  setGroupSlowModeAPI,
  exportChatHistoryAPI,
  setAutoReplyAPI,
  manageGroupPermissionsAPI,
  createGroupEventAPI,
  setVipPriorityAPI,
  setAutoCleanScheduleAPI,
  snoozeNotificationsAPI,
  getMediaVaultAPI,
  clearChatStorageAPI,
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
  Phone,
  Video,
  Info,
  SmilePlus,
  Forward,
  BarChart2,
  CheckCircle2,
  Circle,
  Sparkles,
  MessageSquareReply,
  Palette,
  Camera,
  LogOut,
  Settings2,
  Clock,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { parseUTC } from "@/shared/lib/app_utils";
import PageLoader from "@/shared/components/common/PageLoader";




interface ForwardModalProps {
  messageId: string;
  conversations: any[];
  user: any;
  onClose: () => void;
  onForward: (messageId: string, receiverIds: string[]) => Promise<void>;
}

function ForwardModal({ messageId, conversations, user, onClose, onForward }: ForwardModalProps) {
  const { showToast } = useToast();

  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filtered = conversations.filter(c => {
    const isGroup = c.type === "group";
    const name = isGroup ? c.group_name : c.participants.find((p: any) => p._id !== user?._id)?.full_name;
    return name?.toLowerCase().includes(search.toLowerCase());
  });

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleForward = async () => {
    if (selectedIds.length === 0) return;
    setIsSubmitting(true);
    try {
      await onForward(messageId, selectedIds);
      showToast("Chuyển tiếp tin nhắn thành công");
      onClose();
    } catch (error: any) {
      showToast(error.message || "Lỗi chuyển tiếp tin nhắn", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Chuyển tiếp tin nhắn</ModalTitle>
      </ModalHeader>
      
      <div className="px-6 py-4 border-b border-[#E8E8ED]">
        <div className="relative">
          <Search className="w-4 h-4 text-[#6E6E73] absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            type="text"
            placeholder=""
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="apple-input w-full pl-9"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[300px] px-4 py-2">
        {filtered.map(c => {
          const isGroup = c.type === "group";
          const targetId = isGroup ? c._id : c.participants.find((p: any) => p._id !== user?._id)?._id;
          const name = isGroup ? c.group_name : c.participants.find((p: any) => p._id !== user?._id)?.full_name;
          const avatar = isGroup ? c.avatar_url : c.participants.find((p: any) => p._id !== user?._id)?.avatar_url;
          
          return (
            <div 
              key={c._id}
              onClick={() => toggleSelect(targetId)}
              className="flex items-center gap-3 p-2 rounded-[10px] hover:bg-[#F5F5F7] cursor-pointer transition-colors"
            >
              <input 
                type="checkbox" 
                checked={selectedIds.includes(targetId)}
                readOnly
                className="w-4 h-4 rounded-full border-[#D2D2D7] text-[#0071E3] focus:ring-[#0071E3]"
              />
              {avatar ? (
                <img 
                  src={avatar} 
                  alt="" 
                  className="w-10 h-10 rounded-full object-cover border border-[#E8E8ED]" 
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-[#E8E8ED] flex items-center justify-center border border-[#E8E8ED]">
                  <User className="w-5 h-5 text-[#6E6E73]" />
                </div>
              )}
              <span className="text-[15px] text-[#1D1D1F] font-medium truncate">{name || "Người dùng"}</span>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="p-4 text-center text-[#6E6E73] text-[15px]">Không tìm thấy cuộc trò chuyện nào</div>
        )}
      </div>

      <div className="flex justify-end gap-3 px-6 py-4 border-t border-[#E8E8ED]">
        <button
          onClick={onClose}
          className="px-4 py-2 text-[14px] font-medium text-[#1D1D1F] bg-[#E8E8ED] hover:bg-[#D2D2D7] rounded-full transition-colors"
        >
          Hủy
        </button>
        <button
          onClick={handleForward}
          disabled={selectedIds.length === 0 || isSubmitting}
          className="px-4 py-2 text-[14px] font-medium text-white bg-[#0071E3] hover:opacity-80 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          Gửi ({selectedIds.length})
        </button>
      </div>
    </Modal>
  );
}



interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSchedule: (date: Date) => void;
}

function ScheduleModal({ isOpen, onClose, onSchedule }: ScheduleModalProps) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!date || !time) return;
    const scheduledAt = new Date(`${date}T${time}`);
    if (scheduledAt <= new Date()) {
      alert("Thời gian phải ở tương lai");
      return;
    }
    onSchedule(scheduledAt);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-sm">
      <ModalHeader>
        <ModalTitle>Hẹn giờ gửi tin nhắn</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-1">Ngày gửi</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required className="w-full bg-[#E8E8ED] text-[#1D1D1F] px-4 py-2 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#1D1D1F] mb-1">Giờ gửi</label>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required className="w-full bg-[#E8E8ED] text-[#1D1D1F] px-4 py-2 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3]" />
          </div>
          <button type="submit" className="w-full bg-[#0071E3] text-white rounded-[10px] py-2 font-medium hover:bg-[#0077ED] transition-colors">
            Hẹn giờ
          </button>
        </form>
      </ModalContent>
    </Modal>
  );
}

interface CreatePollModalProps {
  onClose: () => void;
  onSubmit: (question: string, options: string[]) => Promise<void>;
}

function CreatePollModal({ onClose, onSubmit }: CreatePollModalProps) {
  const { showToast } = useToast();

  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState<string[]>(["", ""]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddOption = () => {
    if (options.length >= 10) {
      showToast("Tối đa 10 lựa chọn", "error");
      return;
    }
    setOptions([...options, ""]);
  };

  const handleRemoveOption = (index: number) => {
    if (options.length <= 2) return;
    setOptions(options.filter((_, i) => i !== index));
  };

  const handleChangeOption = (index: number, val: string) => {
    const newOptions = [...options];
    newOptions[index] = val;
    setOptions(newOptions);
  };

  const handleSubmit = async () => {
    const validOptions = options.filter(o => o.trim() !== "");
    if (!question.trim()) {
      showToast("Vui lòng nhập câu hỏi", "error");
      return;
    }
    if (validOptions.length < 2) {
      showToast("Cần ít nhất 2 lựa chọn", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(question, validOptions);
      showToast("Tạo bình chọn thành công");
      onClose();
    } catch (error: any) {
      showToast(error.message || "Tạo bình chọn thất bại", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Tạo bình chọn</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-4 max-h-[50vh] overflow-y-auto hide-scrollbar">
          <div>
            <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Câu hỏi</label>
            <input 
              type="text" 
              value={question}
              onChange={e => setQuestion(e.target.value)}
              placeholder=""
              className="apple-input w-full"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[13px] font-medium text-[#6E6E73] mb-1">Các lựa chọn</label>
            {options.map((opt, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input 
                  type="text" 
                  value={opt}
                  onChange={e => handleChangeOption(idx, e.target.value)}
                  placeholder=""
                  className="apple-input flex-1"
                />
                {options.length > 2 && (
                  <button onClick={() => handleRemoveOption(idx)} className="p-2 text-[#6E6E73] hover:text-red-500 rounded-full hover:bg-[#FFF5F5] transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
            <button 
              onClick={handleAddOption}
              className="flex items-center gap-2 text-[#0071E3] text-[14px] font-medium mt-2 hover:opacity-80 transition-opacity p-1"
            >
              <Plus className="w-4 h-4" /> Thêm lựa chọn
            </button>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-[#E8E8ED]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[14px] font-medium text-[#1D1D1F] bg-[#E8E8ED] hover:bg-[#D2D2D7] rounded-full transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 text-[14px] font-medium text-white bg-[#0071E3] hover:opacity-80 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Tạo bình chọn
          </button>
        </div>
      </ModalContent>
    </Modal>
  );
}



interface PollOption {
  id: string;
  text: string;
  votes: string[];
}

interface PollData {
  question: string;
  options: PollOption[];
  multiple_choice?: boolean;
}

interface PollMessageProps {
  messageId: string;
  pollData: PollData;
  currentUserId: string;
  onVote: (messageId: string, optionId: string) => Promise<void>;
}

function PollMessage({ messageId, pollData, currentUserId, onVote }: PollMessageProps) {
  const { showToast } = useToast();

  const [isVoting, setIsVoting] = useState(false);

  const totalVotes = pollData.options.reduce((sum, opt) => sum + (opt.votes?.length || 0), 0);

  const handleVote = async (optionId: string) => {
    if (isVoting) return;
    setIsVoting(true);
    try {
      await onVote(messageId, optionId);
    } catch (err: any) {
      showToast(err.message || "Bỏ phiếu thất bại", "error");
    } finally {
      setIsVoting(false);
    }
  };

  return (
    <div className="w-full min-w-[260px] max-w-[320px] bg-white rounded-[18px] border border-[#E8E8ED] overflow-hidden shadow-sm flex flex-col">
      <div className="p-4 border-b border-[#E8E8ED] bg-[#F5F5F7]">
        <h4 className="font-semibold text-[#1D1D1F] text-[15px] leading-snug">
          {pollData.question}
        </h4>
        <span className="text-[12px] text-[#6E6E73] mt-1 block">Bình chọn • {totalVotes} lượt vote</span>
      </div>
      <div className="p-2 space-y-1">
        {pollData.options.map((opt) => {
          const voteCount = opt.votes?.length || 0;
          const percentage = totalVotes > 0 ? Math.round((voteCount / totalVotes) * 100) : 0;
          const hasVoted = opt.votes?.includes(currentUserId);

          return (
            <div 
              key={opt.id}
              onClick={() => handleVote(opt.id)}
              className="relative rounded-[10px] overflow-hidden cursor-pointer group/pollopt transition-colors border border-transparent hover:border-[#E8E8ED]"
            >

              <div 
                className={`absolute inset-y-0 left-0 transition-all duration-500 ease-out ${hasVoted ? "bg-[#0071E3]/15" : "bg-[#F5F5F7]"}`}
                style={{ width: `${percentage}%` }}
              />

              <div className="absolute inset-0 bg-black/[0.03] opacity-0 group-hover/pollopt:opacity-100 transition-opacity" />
              
              <div className="relative flex items-center justify-between p-3 z-10">
                <div className="flex items-center gap-3">
                  {hasVoted ? (
                    <CheckCircle2 className="w-[18px] h-[18px] text-[#0071E3] shrink-0" />
                  ) : (
                    <Circle className="w-[18px] h-[18px] text-[#6E6E73] shrink-0" />
                  )}
                  <span className={`text-[15px] font-medium ${hasVoted ? "text-[#0071E3]" : "text-[#1D1D1F]"}`}>
                    {opt.text}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {voteCount > 0 && (
                     <div className="flex -space-x-1.5 mr-1">

                        <div className="w-5 h-5 rounded-full bg-white border border-[#D2D2D7] flex items-center justify-center text-[9px] font-bold text-[#6E6E73]">
                          {voteCount}
                        </div>
                     </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface ReplyBlockProps {
  replyingTo: any;
  onCancel: () => void;
}

function ReplyBlock({ replyingTo, onCancel }: ReplyBlockProps) {
  if (!replyingTo) return null;

  return (
    <div className="absolute bottom-full left-0 w-full bg-white/95 backdrop-blur-md border-t border-[#E8E8ED] px-4 py-2.5 flex items-center justify-between z-10 animate-in slide-in-from-bottom-2 fade-in duration-200">
      <div className="flex flex-col flex-1 overflow-hidden pr-4 border-l-2 border-[#0071E3] pl-3">
        <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#0071E3] mb-0.5">
          <Reply className="w-3.5 h-3.5" />
          <span>Đang trả lời tin nhắn</span>
        </div>
        <p className="text-[14px] text-[#6E6E73] truncate">
          {replyingTo.content || (replyingTo.image_url ? "[Hình ảnh]" : replyingTo.poll_data ? "[Bình chọn]" : "[Đính kèm]")}
        </p>
      </div>
      <button 
        onClick={onCancel}
        className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-[#F5F5F7] text-[#6E6E73] transition-colors shrink-0"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}


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


function SmartQuickReplies({ replies, onSelect }: { replies: string[], onSelect: (r: string) => void }) {
  if (!replies || replies.length === 0) return null;
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-white border-t border-[#E8E8ED] overflow-x-auto no-scrollbar">
      <Sparkles className="w-4 h-4 text-[#0071E3] shrink-0" />
      {replies.map((reply, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(reply)}
          className="whitespace-nowrap px-4 py-1.5 bg-[#F5F5F7] hover:bg-[#E8E8ED] text-[#1D1D1F] text-[14px] font-medium rounded-[980px] transition-colors"
        >
          {reply}
        </button>
      ))}
    </div>
  );
}



const parsePollData = (msg: any) => {
  if (msg.poll_data) return msg;
  if (msg.content && typeof msg.content === "string" && msg.content.includes('"type": "poll"')) {
    try {
      const parsed = JSON.parse(msg.content);
      if (parsed.type === "poll" && parsed.data) {
        return { ...msg, poll_data: parsed.data, content: "" };
      }
    } catch (e) {}
  }
  return msg;
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
  const [showGlobalSearch, setShowGlobalSearch] = useState(false);
  const [globalSearchQuery, setGlobalSearchQuery] = useState("");
  const [globalSearchResults, setGlobalSearchResults] = useState<any[]>([]);
  const [isGlobalSearching, setIsGlobalSearching] = useState(false);
  const [replyingTo, setReplyingTo] = useState<any>(null);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [editingMsg, setEditingMsg] = useState<any>(null);
  const [activeMsgMenuId, setActiveMsgMenuId] = useState<string | null>(null);


  const [activeThreadParentId, setActiveThreadParentId] = useState<string | null>(null);
  const [threadMessages, setThreadMessages] = useState<any[]>([]);
  const [loadingThread, setLoadingThread] = useState(false);
  const [threadInput, setThreadInput] = useState("");


  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const [loadingQuickReplies, setLoadingQuickReplies] = useState(false);
  const [showMsgMenu, setShowMsgMenu] = useState<string | null>(null);
  const [showForwardModal, setShowForwardModal] = useState<string | null>(null);
  const [showPollModal, setShowPollModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
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

  const [showSelfDestructMenu, setShowSelfDestructMenu] = useState(false);
  const [showGroupSettingsModal, setShowGroupSettingsModal] = useState(false);
  const [showLeaveGroupModal, setShowLeaveGroupModal] = useState(false);
  const [tempGroupSettings, setTempGroupSettings] = useState({ messaging_restricted: false, requires_approval: false });
  const [isRecording, setIsRecording] = useState(false);
  const [isRecordingPaused, setIsRecordingPaused] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null,
  );
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showConvMenu, setShowConvMenu] = useState(false);
  const [aliases, setAliases] = useState<Record<string, string>>({});
  const [conversationTheme, setConversationTheme] = useState<string>("default");

  const getThemeBgClass = (theme: string) => {
    switch(theme) {
      case "red": return "bg-red-500";
      case "green": return "bg-green-500";
      case "purple": return "bg-purple-500";
      default: return "bg-[#0071E3]";
    }
  };

  const getThemeTextClass = (theme: string) => {
    switch(theme) {
      case "red": return "text-red-500";
      case "green": return "text-green-500";
      case "purple": return "text-purple-500";
      default: return "text-[#0071E3]";
    }
  };

  const updateTheme = async (newTheme: string) => {
    if (!selectedConvRef.current) return;
    setConversationTheme(newTheme);
    setShowConvMenu(false);
    try {
      await updateConversationSettingsAPI(selectedConvRef.current.other_user_id, { theme: newTheme });
    } catch (e) {
      console.error(e);
    }
  };
  const [showAliasModal, setShowAliasModal] = useState(false);
  const [aliasInput, setAliasInput] = useState("");
  const recordTimerRef = useRef<any>(null);
  const cancelRecordingRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const socketRef = useRef<WebSocket | null>(null);
  const conversationsRef = useRef<any[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<{[key: string]: boolean | number}>({});
  const [typingUsers, setTypingUsers] = useState<{[key: string]: boolean}>({});
  const typingTimeoutRef = useRef<any>(null);
  const groupAvatarInputRef = useRef<HTMLInputElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      const res = await getConversationsAPI();
      const loaded = (res.data || res || []).map((c: any) => {
        if (c.last_message) c.last_message = parsePollData(c.last_message);
        return c;
      });
      setConversations(loaded);
      conversationsRef.current = loaded;
      if (socketRef.current?.readyState === WebSocket.OPEN) {
          const userIds = loaded.map((c: any) => c.other_user_id);
          if (userIds.length > 0) {
              socketRef.current.send(JSON.stringify({ action: "check_online", data: { user_ids: userIds } }));
          }
      }
    } catch (err: any) {
      showToast("Lỗi đồng bộ danh sách phiên hội thoại", "error");
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

  const handleSetAlias = async () => {
    if (!selectedConv) return;
    const userId = selectedConv.other_user_id;
    const updated: Record<string, string> = { ...aliases, [userId]: aliasInput };
    if (!aliasInput.trim()) delete updated[userId];
    setAliases(updated);
    localStorage.setItem("user_aliases", JSON.stringify(updated));
    setShowAliasModal(false);
    try {
        await updateConversationSettingsAPI(userId, { nicknames: updated });
    } catch (e) {
        console.error(e);
    }
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
        conversationsRef.current = updated;
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
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "ping" }));
        const userIds = conversationsRef.current.map((c) => c.other_user_id);
        if (userIds.length > 0) {
          socket.send(JSON.stringify({ action: "check_online", data: { user_ids: userIds } }));
        }
      }
    }, 30000);

    socket.onmessage = (event) => {
      try {
        const { type, data } = JSON.parse(event.data);
        if (type === "new_message") {
          const parsedData = parsePollData(data);
          if (
            selectedConvRef.current &&
            parsedData.sender_id === selectedConvRef.current.other_user_id
          ) {
            setMessages((prev) => {
              if (prev.some((m) => (m._id || m.id) === (parsedData._id || parsedData.id)))
                return prev;
              return [...prev, parsedData];
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
          updateConversationInPlace(parsedData.sender_id, parsedData);
          localStorage.setItem(`last_msg_id_${user._id}`, parsedData._id || parsedData.id);
        } else if (type === "message_sent_ack") {
          const parsedData = parsePollData(data);
          setMessages((prev) => {
            if (prev.some((m) => (m._id || m.id) === (parsedData._id || parsedData.id)))
              return prev;
            return [...prev, parsedData];
          });
          updateConversationInPlace(parsedData.receiver_id, parsedData);
          localStorage.setItem(`last_msg_id_${user._id}`, parsedData._id || parsedData.id);
        } else if (["message_edited", "message_pinned", "message_recalled", "message_reaction"].includes(type)) {
          const parsedData = parsePollData(data);
          setMessages((prev) =>
            prev.map((m) =>
              (m._id || m.id) === (parsedData._id || parsedData.id) ? parsedData : m,
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
        } else if (type === "online_status") {
          setOnlineUsers(prev => ({ ...prev, ...data }));
        } else if (type === "typing_start") {
          setTypingUsers(prev => ({ ...prev, [data.sender_id]: true }));
        } else if (type === "typing_end") {
          setTypingUsers(prev => ({ ...prev, [data.sender_id]: false }));
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
      const rawMsgs = res.data || res || [];
      setMessages(rawMsgs.map(parsePollData));
      await markAsReadAPI(conv.other_user_id);
      const blockedRes = await getBlockedStatusAPI(conv.other_user_id);
      setIsBlocked(blockedRes.data?.is_blocked || false);
      const attachRes = await getSharedAttachmentsAPI(conv.other_user_id);
      setSharedAttachments(attachRes.data || attachRes || []);
      const settingsRes = await getConversationSettingsAPI(conv.other_user_id);
      const settings = settingsRes.data || settingsRes;
      setSelfDestructSeconds(settings.self_destruct_seconds || 0);
      setIsMuted(settings.is_muted || false);
      setConversationTheme(settings.theme || "default");
      if (settings.nicknames) {
        setAliases(prev => ({ ...prev, ...settings.nicknames }));
      }
      setSelfDestructSeconds(settings.self_destruct_seconds || 0);
      setIsMuted(settings.is_muted || false);
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
      showToast("Lỗi trích xuất lịch sử phiên hội thoại", "error");
    } finally {
      setLoadingMsgs(false);
    }
  };
  const handleTyping = (e: any) => {
    setNewMessage(e.target.value);
    if (!selectedConvRef.current || !socketRef.current) return;
    if (socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        action: "typing_start",
        data: { receiver_id: selectedConvRef.current.other_user_id }
      }));
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        socketRef.current?.send(JSON.stringify({
          action: "typing_end",
          data: { receiver_id: selectedConvRef.current.other_user_id }
        }));
      }, 3000);
    }
  };


  const handleSend = async (textOverride?: string, parentIdOverride?: string) => {
    if (isBlocked) {
      showToast("Không thể gửi tin nhắn do giới hạn bảo mật", "error");
      return;
    }
    const effectiveParentId = parentIdOverride || activeThreadParentId;
    const textToSend = textOverride !== undefined ? textOverride : newMessage.trim();
    if ((!textToSend && imageFiles.length === 0) || !selectedConv || sending) return;
    if (editingMsg) {
      setSending(true);
      try {
        await editMessageAPI(
          editingMsg._id || editingMsg.id,
          textToSend,
        );
        setMessages((prev) =>
          prev.map((m) =>
            (m._id || m.id) === (editingMsg._id || editingMsg.id)
              ? { ...m, content: textToSend, is_edited: true }
              : m,
          ),
        );
        setEditingMsg(null);
        setNewMessage("");
      } catch (err: any) {
        showToast("Lỗi cập nhật nội dung tin nhắn", "error");
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
            i === 0 ? textToSend : "",
            isImage ? uploadData.data.url : undefined,
            replyingTo?._id || replyingTo?.id,
            undefined,
            selfDestructSeconds > 0 ? selfDestructSeconds : undefined,
            !isImage ? uploadData.data.url : undefined,
            !isImage ? imageFiles[i].name : undefined,
            effectiveParentId || undefined,
          );
          const msg = res.data || res;
          if (effectiveParentId) {
            setThreadMessages((prev) => [...prev, msg]);
          } else {
            setMessages((prev) => [...prev, msg]);
          }
          updateConversationInPlace(selectedConv.other_user_id, msg);
        }
        setUploadingImage(false);
      } else {
        const res = await sendMessageAPI(
          selectedConv.other_user_id,
          textToSend,
          "",
          replyingTo?._id || replyingTo?.id,
          undefined,
          selfDestructSeconds > 0 ? selfDestructSeconds : undefined,
          undefined,
          undefined,
          effectiveParentId || undefined,
        );
        const msg = res.data || res;
        if (effectiveParentId) {
          setThreadMessages((prev) => [...prev, msg]);
        } else {
          setMessages((prev) => [...prev, msg]);
        }
        updateConversationInPlace(selectedConv.other_user_id, msg);
      }
      setNewMessage("");
      setReplyingTo(null);
      setImageFiles([]);
      await saveDraftAPI(selectedConv.other_user_id, "");
    } catch (err: any) {
      showToast("Lỗi truyền tải dữ liệu tin nhắn", "error");
    } finally {
      setSending(false);
      setUploadingImage(false);
    }
  };

  const handleScheduleSend = async (scheduledAt: Date) => {
    if (!newMessage.trim() && imageFiles.length === 0) return;
    try {
      showToast("Đang lên lịch gửi tin nhắn...", "info");
      
      if (imageFiles.length > 0) {
        for (let i = 0; i < imageFiles.length; i++) {
          const file = imageFiles[i];
          const formData = new FormData();
          formData.append("file", file);
          const resUpload = await fetch(`${API_URL}/tai-len/tap-tin`, {
            method: "POST",
            headers: { Authorization: `Bearer ${getToken()}` },
            body: formData,
          });
          const uploadData = await resUpload.json();
          await sendMessageAPI(
            selectedConvRef.current!.other_user_id,
            i === 0 ? newMessage.trim() : "",
            uploadData.data.url,
            activeMsgObj?._id || undefined,
            undefined,
            undefined,
            undefined,
            undefined,
            activeThreadParentId || undefined,
            scheduledAt.toISOString()
          );
        }
      } else {
        await sendMessageAPI(
          selectedConvRef.current!.other_user_id,
          newMessage.trim(),
          undefined,
          activeMsgObj?._id || undefined,
          undefined,
          undefined,
          undefined,
          undefined,
          activeThreadParentId || undefined,
          scheduledAt.toISOString()
        );
      }
      
      showToast("Đã lên lịch gửi tin nhắn", "success");
      setNewMessage("");
      setImageFiles([]);
    } catch (e) {
      showToast(e instanceof Error ? e.message : "Lỗi lên lịch gửi tin nhắn", "error");
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
          showToast("Lỗi thực thi luồng dữ liệu âm thanh", "error");
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
      showToast("Lỗi kết nối đến thiết bị thu âm", "error");
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
      showToast("Lỗi cập nhật trạng thái ghim tin nhắn", "error");
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
      showToast("Thu hồi tin nhắn hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi thực thi yêu cầu thu hồi tin nhắn", "error");
    }
  };

  const handleDeleteForMe = async (messageId: string) => {
    try {
      await deleteMessageForMeAPI(messageId);
    } catch {

    }
    setMessages((prev) => prev.filter((m) => (m._id || m.id) !== messageId));
    showToast("Xóa dữ liệu cục bộ hoàn tất", "success");
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

  
  const handleForward = async (messageId: string, receiverIds: string[]) => {
    await forwardMessageAPI(messageId, receiverIds);
  };

  const handleCreatePoll = async (question: string, options: string[]) => {
    if (!selectedConv) return;
    const receiverId = selectedConv.type === "group" ? selectedConv._id : selectedConv.participants.find((p: any) => p._id !== user?._id)?._id;
    await createPollAPI(receiverId, question, options);
  };

  const handleVote = async (messageId: string, optionId: string) => {
    await votePollAPI(messageId, optionId);

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
      showToast("Lỗi thực thi thao tác phản hồi", "error");
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
      showToast("Chia sẻ tài liệu hoàn tất", "success");
      updateConversationInPlace(selectedConv.other_user_id, newMsg);
    } catch (err: any) {
      showToast("Lỗi khởi tạo liên kết chia sẻ tài liệu", "error");
    }
  };

  const handleGroupAvatarUpload = async (e: any) => {
    const file = e.target.files?.[0];
    if (!file || !selectedConv) return;
    try {
      showToast("Đang tải ảnh lên...", "info");
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_URL}/tai-len/tap-tin`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd
      });
      const data = await res.json();
      if (data.data?.url) {
        await fetch(`${API_URL}/chat/nhom/${selectedConv.other_user_id}/thong-tin`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`
          },
          body: JSON.stringify({ avatar_url: data.data.url })
        });
        showToast("Đã cập nhật ảnh đại diện nhóm", "success");
        setSelectedConv({
          ...selectedConv,
          group_avatar: data.data.url,
          other_user: { ...selectedConv.other_user, avatar_url: data.data.url }
        });
        updateConversationInPlace(selectedConv.other_user_id, { avatar_url: data.data.url, group_avatar: data.data.url });
      }
    } catch (err: any) {
      showToast("Lỗi tải ảnh đại diện nhóm", "error");
    }
  };

  const handleBlockUser = async () => {
    if (!selectedConv) return;
    try {
      if (isBlocked) {
        await unblockUserAPI(selectedConv.other_user_id);
        setIsBlocked(false);
        showToast("Gỡ chặn người dùng hoàn tất", "success");
      } else {
        await blockUserAPI(selectedConv.other_user_id);
        setIsBlocked(true);
        showToast("Chặn người dùng hoàn tất", "success");
      }
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái kết nối người dùng", "error");
    }
  };

  const handleTogglePinConv = async (otherId: string) => {
    try {
      const res = await togglePinConversationAPI(otherId);
      const status = res.data || res;
      showToast(status.is_pinned ? "Ghim phiên hội thoại hoàn tất" : "Bỏ ghim phiên hội thoại hoàn tất", "success");
      setActiveConvMenuId(null);
    } catch (err: any) {
      showToast("Lỗi cấu hình ghim phiên hội thoại", "error");
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
      showToast("Lỗi cập nhật trạng thái hiển thị", "error");
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
      showToast("Xóa phiên hội thoại hoàn tất", "success");
    } catch (err) {
      showToast("Lỗi xóa dữ liệu phiên hội thoại", "error");
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
      showToast("Dịch ngôn ngữ hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi thực thi luồng dịch thuật tự động", "error");
    }
  };

  const handleToggleMute = async () => {
    if (!selectedConv) return;
    try {
      const res = await toggleMuteAPI(selectedConv.other_user_id);
      setIsMuted((res.data || res).is_muted);
      showToast(
        (res.data || res).is_muted ? "Tắt thông báo hoàn tất" : "Bật thông báo hoàn tất",
        "success",
      );
    } catch (err: any) {
      showToast("Lỗi thiết lập trạng thái âm thanh", "error");
    }
  };

  const handleUpdateSelfDestruct = async (seconds: number) => {
    if (!selectedConv) return;
    try {
      await toggleSelfDestructAPI(selectedConv.other_user_id, seconds);
      setSelfDestructSeconds(seconds);
      setShowSelfDestructMenu(false);
      showToast(
        seconds > 0 ? `Cấu hình tự hủy sau ${seconds}s hoàn tất` : "Tắt chế độ tự hủy hoàn tất",
        "success",
      );
    } catch (err: any) {
      showToast("Lỗi cập nhật cấu hình tự hủy", "error");
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
    if (!groupName.trim()) return showToast("Tên nhóm không được để trống", "error");
    try {
      const res = await createGroupAPI(groupName.trim(), selectedMembers);
      const created = res.data || res;
      showToast("Khởi tạo nhóm trò chuyện hoàn tất", "success");
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
      showToast("Lỗi thiết lập nhóm trò chuyện mới", "error");
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
      showToast("Lỗi trích xuất thông tin người dùng", "error");
    } finally {
      setSearching(false);
    }
  };

  const handleGlobalSearch = async (q: string) => {
    setGlobalSearchQuery(q);
    if (q.length < 2) return setGlobalSearchResults([]);
    setIsGlobalSearching(true);
    try {
      const res = await globalSearchAPI(q);
      setGlobalSearchResults(res.data || res || []);
    } catch (err: any) {
      showToast("Lỗi tìm kiếm toàn cục", "error");
    } finally {
      setIsGlobalSearching(false);
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


  const loadQuickReplies = async (otherUserId: string) => {
    if (!user || (user.role !== "admin" && user.ai_tier !== "PRO" && user.ai_tier !== "PREMIUM")) {
      setQuickReplies([]);
      return;
    }
    try {
      setLoadingQuickReplies(true);
      const res = await getQuickRepliesAPI(otherUserId);
      setQuickReplies(res.data?.replies || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingQuickReplies(false);
    }
  };

  useEffect(() => {
    if (selectedConv) {
      loadQuickReplies(selectedConv.other_user_id);
    } else {
      setQuickReplies([]);
    }
  }, [selectedConv]);

  useEffect(() => {
    if (activeThreadParentId) {
      const loadThread = async () => {
        try {
          setLoadingThread(true);
          const res = await getThreadRepliesAPI(activeThreadParentId);
          setThreadMessages(res.data.reverse());
        } catch (e) {
          showToast(e instanceof Error ? e.message : "Lỗi tải luồng", "error");
        } finally {
          setLoadingThread(false);
        }
      };
      loadThread();
    } else {
      setThreadMessages([]);
    }
  }, [activeThreadParentId]);
  if (authLoading) return <PageLoader />;
  if (!user) return null;

  const isGroupConv = selectedConv?.other_user?.is_group || selectedConv?.other_user_id?.startsWith("group_") || false;

  const renderOnlineStatus = (userId: string, isGroup: boolean, participantCount?: number) => {
    if (isGroup) return `${participantCount || 0} thành viên`;
    const status = onlineUsers[userId];
    if (status === true) return "Trực tuyến";
    if (typeof status === "number") {
      const diffMinutes = Math.floor((Date.now() - status * 1000) / 60000);
      if (diffMinutes < 1) return `Hoạt động vừa xong`;
      if (diffMinutes < 60) return `Hoạt động từ ${diffMinutes} phút trước`;
      if (diffMinutes < 1440) return `Hoạt động từ ${Math.floor(diffMinutes / 60)} giờ trước`;
      const date = new Date(status * 1000);
      return `Hoạt động từ ${date.toLocaleDateString("vi-VN")}`;
    }
    return "Ngoại tuyến";
  };

  return (
    <div className="w-full h-full flex flex-col font-sans text-[#1D1D1F]">
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
              placeholder=""
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
                  className="flex items-center justify-between p-4 bg-white rounded-[10px] cursor-pointer hover:bg-[#F5F5F7]"
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
                        <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[9px] font-semibold uppercase">
                          {(u.full_name || u.username || "U").charAt(0)}
                        </div>
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

      <Modal isOpen={showGroupSettingsModal} onClose={() => setShowGroupSettingsModal(false)}>
        <ModalHeader>
          <ModalTitle>Cài đặt nhóm</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1D1D1F]">Hạn chế nhắn tin</span>
                <span className="text-[13px] text-[#6E6E73]">Chỉ trưởng nhóm và phó nhóm được gửi tin</span>
              </div>
              <input
                type="checkbox"
                checked={tempGroupSettings.messaging_restricted}
                onChange={(e) => setTempGroupSettings(prev => ({...prev, messaging_restricted: e.target.checked}))}
                className="w-5 h-5 rounded border-[#D2D2D7] text-[#0071E3] focus:ring-[#0071E3]"
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1D1D1F]">Yêu cầu phê duyệt</span>
                <span className="text-[13px] text-[#6E6E73]">Người mới dùng link tham gia cần được duyệt</span>
              </div>
              <input
                type="checkbox"
                checked={tempGroupSettings.requires_approval}
                onChange={(e) => setTempGroupSettings(prev => ({...prev, requires_approval: e.target.checked}))}
                className="w-5 h-5 rounded border-[#D2D2D7] text-[#0071E3] focus:ring-[#0071E3]"
              />
            </div>
            <button
              onClick={async () => {
                try {
                  const res = await fetch(`${API_URL}/tin-nhan/nhom/${selectedConv._id || selectedConv.id}/cai-dat`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getToken()}` },
                    body: JSON.stringify(tempGroupSettings)
                  });
                  const data = await res.json();
                  if (res.ok) {
                    showToast(data.message, "success");
                    setShowGroupSettingsModal(false);
                  } else {
                    showToast(data.message || "Có lỗi xảy ra", "error");
                  }
                } catch(e) {
                  showToast("Lỗi kết nối", "error");
                }
              }}
              className="w-full mt-4 bg-[#0071E3] text-white font-medium py-3 rounded-[980px] hover:bg-[#0055C6] transition-colors"
            >
              Lưu thay đổi
            </button>
          </div>
        </ModalContent>
      </Modal>

      <Modal isOpen={showLeaveGroupModal} onClose={() => setShowLeaveGroupModal(false)}>
        <ModalHeader>
          <ModalTitle>Rời khỏi nhóm</ModalTitle>
          <ModalDescription>Bạn có muốn rời khỏi nhóm này không?</ModalDescription>
        </ModalHeader>
        <ModalContent>
          <div className="flex flex-col gap-3">
            <button
              onClick={async () => {
                try {
                  const res = await fetch(`${API_URL}/tin-nhan/nhom/${selectedConv._id || selectedConv.id}/thanh-vien/${user?._id || (user as any)?.id}?silent=false`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${getToken()}` }
                  });
                  if (res.ok) {
                    showToast("Đã rời nhóm", "success");
                    setShowLeaveGroupModal(false);
                    setSelectedConv(null);
                  }
                } catch(e) {}
              }}
              className="w-full bg-red-500 text-white font-medium py-3 rounded-[980px] hover:bg-red-600 transition-colors"
            >
              Rời nhóm
            </button>
            <button
              onClick={async () => {
                try {
                  const res = await fetch(`${API_URL}/tin-nhan/nhom/${selectedConv._id || selectedConv.id}/thanh-vien/${user?._id || (user as any)?.id}?silent=true`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${getToken()}` }
                  });
                  if (res.ok) {
                    showToast("Đã rời nhóm trong im lặng", "success");
                    setShowLeaveGroupModal(false);
                    setSelectedConv(null);
                  }
                } catch(e) {}
              }}
              className="w-full bg-[#F5F5F7] text-[#1D1D1F] font-medium py-3 rounded-[980px] hover:bg-[#E8E8ED] transition-colors"
            >
              Rời nhóm trong im lặng
            </button>
          </div>
        </ModalContent>
      </Modal>

      <div className="flex flex-1 min-h-0 gap-6">
        <div
          className={`w-full md:w-[320px] bg-[#F5F5F7] rounded-[18px] flex flex-col overflow-hidden shrink-0 ${selectedConv ? "hidden md:flex" : "flex"}`}
        >
          <div className="p-6 md:px-0 pb-4 md:pt-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
                Tất cả tin nhắn
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowGlobalSearch(!showGlobalSearch)}
                  className="p-2 bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] rounded-full transition-colors"
                  title="Tìm kiếm"
                >
                  <Search className="w-4 h-4" />
                </button>
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
            {showGlobalSearch && (
              <div className="relative">
                <Search className="w-4 h-4 text-[#A1A1A6] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  value={globalSearchQuery}
                  onChange={(e) => handleGlobalSearch(e.target.value)}
                  placeholder="Tìm tin nhắn..."
                  className="w-full bg-[#E8E8ED] text-[#1D1D1F] placeholder:text-[#A1A1A6] pl-9 pr-4 py-2 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[#0071E3] transition-all text-[15px]"
                />
              </div>
            )}
          </div>
          <div className="flex-1 overflow-y-auto px-6 md:px-0 pb-4 space-y-2 hide-scrollbar">
            {isGlobalSearching ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-[#6E6E73]" />
              </div>
            ) : globalSearchQuery.length >= 2 ? (
              globalSearchResults.length > 0 ? (
                globalSearchResults.map((msg) => (
                  <div
                    key={msg._id || msg.id}
                    onClick={() => {
                      const otherId = msg.sender_id === (user as any)?._id ? msg.receiver_id : msg.sender_id;
                      const c = conversations.find(c => c.other_user_id === otherId);
                      if (c) setSelectedConv(c);
                    }}
                    className="p-4 bg-white rounded-[14px] cursor-pointer hover:bg-[#F5F5F7] border border-transparent hover:border-[#E8E8ED] transition-all"
                  >
                    <div className="text-[13px] text-[#6E6E73] mb-1">{formatRelativeTime(parseUTC(msg.created_at))}</div>
                    <div className="text-[15px] text-[#1D1D1F] line-clamp-2">{msg.content}</div>
                  </div>
                ))
              ) : (
                <p className="text-center text-[13px] text-[#6E6E73] py-12">
                  Không tìm thấy kết quả
                </p>
              )
            ) : loadingConv ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="p-4 rounded-[14px] flex items-center gap-4 animate-pulse bg-white/50 border border-transparent">
                    <div className="w-[48px] h-[48px] bg-[#E8E8ED] rounded-full shrink-0" />
                    <div className="flex-1 space-y-2.5">
                      <div className="h-3.5 bg-[#E8E8ED] rounded-full w-[40%]" />
                      <div className="h-2.5 bg-[#E8E8ED] rounded-full w-[70%]" />
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
                    <div className="w-10 h-10 rounded-full overflow-hidden shrink-0">
                      {conv.other_user?.avatar_url ? (
                        <img
                          src={conv.other_user.avatar_url}
                          alt=""
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[16px] font-semibold uppercase">
                          {(aliases[conv.other_user_id] || conv.other_user?.full_name || conv.other_user?.username || "U").charAt(0)}
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
                          {conv.last_message ? (conv.last_message.is_recalled ? "Tin nhắn đã thu hồi" : conv.last_message.content?.startsWith("Shared document preview and link to access") ? "[Tài liệu]" : (conv.last_message.content || (conv.last_message.image_url ? "[Hình ảnh]" : conv.last_message.poll_data ? "[Bình chọn]" : "[Đính kèm]"))) : "Chưa có tin nhắn"}
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
              <div className="flex-1 flex flex-col items-center justify-center h-full min-h-[300px] text-center">
                <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
              </div>
            )}
          </div>
        </div>

        <div
          className={`flex-1 flex min-w-0 rounded-[18px] overflow-hidden ${!selectedConv ? "hidden md:flex items-center justify-center bg-[#F5F5F7]" : ""}`}
        >
          {selectedConv ? (
            <>
              <div className="flex-1 flex flex-col min-w-0 bg-[#F5F5F7] relative">
              <div className="h-[64px] px-6 md:px-0 flex items-center justify-between bg-transparent">
                <div className="flex items-center gap-4">
                  {activeThreadParentId ? (
                    <button onClick={() => setActiveThreadParentId(null)} className="text-[#0071E3] flex items-center gap-1 hover:bg-[#F5F5F7] p-1.5 rounded-full transition-colors">
                      <ArrowLeft className="w-4 h-4" />
                      <span className="text-[14px] font-medium hidden sm:inline">Quay lại</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => setSelectedConv(null)}
                      className="md:hidden text-[#0071E3]"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                  )}
                  <button 
                    onClick={() => setShowSharedSidebar(!showSharedSidebar)}
                    className="flex items-center gap-3 text-left hover:bg-[#E8E8ED] p-1 -ml-1 rounded-[12px] transition-colors"
                  >
                    <div className="w-10 h-10 rounded-full overflow-hidden relative">
                      {isGroupConv ? (
                        selectedConv.group_avatar ? (
                          <img src={selectedConv.group_avatar} className="w-full h-full object-cover" alt="" />
                        ) : (
                          <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[18px] font-semibold uppercase">
                            {(selectedConv.group_name || selectedConv.other_user?.full_name || "G").charAt(0)}
                          </div>
                        )
                      ) : (
                        selectedConv.other_user?.avatar_url ? (
                          <img src={selectedConv.other_user.avatar_url} className="w-full h-full object-cover" alt="" />
                        ) : (
                          <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[18px] font-semibold uppercase">
                            {(aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username || "U").charAt(0)}
                          </div>
                        )
                      )}
                      {!isGroupConv && onlineUsers[selectedConv.other_user_id] === true && (
                        <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
                      )}
                    </div>
                    <div>
                      <h3 className="text-[16px] font-semibold text-[#1D1D1F]">
                        {isGroupConv 
                          ? (selectedConv.group_name || selectedConv.other_user?.full_name || "Nhóm trò chuyện") 
                          : (aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username)}
                      </h3>
                      <p className="text-[13px] text-[#6E6E73]">
                        {renderOnlineStatus(selectedConv.other_user_id, isGroupConv, selectedConv.participant_ids?.length)}
                      </p>
                    </div>
                  </button>
                </div>
                <div className="relative flex items-center gap-1 sm:gap-2">
                  <button
                    onClick={() => setShowSharedSidebar(!showSharedSidebar)}
                    className={`p-2 rounded-full transition-colors ${showSharedSidebar ? "bg-[#E8E8ED] text-[#1D1D1F]" : "text-[#0071E3] hover:bg-[#F5F5F7] "}`}
                    title="Thông tin đoạn chat"
                  >
                    <Info className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setShowSearchMsgBar(!showSearchMsgBar)}
                    className={`p-2 rounded-full transition-colors hidden sm:block ${showSearchMsgBar ? "bg-[#E8E8ED] text-[#1D1D1F]" : "text-[#0071E3] hover:bg-[#F5F5F7]"}`}
                    title="Tìm kiếm"
                  >
                    <Search className="w-4 h-4" />
                  </button>

                </div>
              </div>


              {showSearchMsgBar && (
                <div className="px-6 md:px-0 py-3 bg-[#F5F5F7]">
                  <div className="relative">
                    <Search className="w-4 h-4 text-[#6E6E73] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                      type="text"
                      value={searchMsgQuery}
                      onChange={(e) => handleSearchMessages(e.target.value)}
                      className="w-full bg-white border border-[#D2D2D7] text-[#1D1D1F] pl-9 pr-8 py-2 rounded-[10px] text-[15px] focus:outline-none focus:border-[#0071E3] transition-colors"
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

              <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-6 md:px-0 pt-6 pb-2 bg-transparent hide-scrollbar relative">
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
                    {activeThreadParentId && (() => {
                      const parentMessage = messages.find(m => m._id === activeThreadParentId || m.id === activeThreadParentId);
                      if (!parentMessage) return null;
                      const currentUserId = user?._id || (user as any)?.id;
                      const isSender = (parentMessage.sender_id || parentMessage.sender) === currentUserId;
                      return (
                        <div className="flex flex-col mb-4 w-full">
                          <div className={`flex flex-col w-full ${isSender ? "items-end" : "items-start"}`}>
                            <div className={`group relative max-w-[85%] flex flex-col ${isSender ? "items-end" : "items-start"}`}>
                              <div className="text-[12px] font-semibold text-[#6E6E73] mb-1 px-1">Bản tin gốc</div>
                              <div className={`rounded-[18px] p-4 ${isSender ? `${getThemeBgClass(conversationTheme)} text-white` : "bg-[#E8E8ED] text-[#1D1D1F]"} opacity-90`}>
                                <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{parentMessage.content || "[Đính kèm]"}</p>
                              </div>
                            </div>
                          </div>
                          <div className="w-full h-[1px] bg-[#E8E8ED] my-6 relative">
                            <span className="absolute left-1/2 -translate-x-1/2 -top-2.5 bg-[#F5F5F7] px-4 text-[12px] font-medium text-[#6E6E73]">
                              {threadMessages.length} phản hồi
                            </span>
                          </div>
                        </div>
                      );
                    })()}
                    {activeThreadParentId && loadingThread ? (
                      <div className="flex justify-center p-4">
                        <Circle className="w-6 h-6 animate-spin text-[#0071E3]" />
                      </div>
                    ) : (activeThreadParentId ? threadMessages : messages).map((msg, i) => {
                      const currentUserId = user?._id || (user as any)?.id;
                      const isSender = (msg.sender_id || msg.sender) === currentUserId;
                      const prevMsg = i > 0 ? messages[i-1] : null;
                      const showTime = !prevMsg || (new Date(msg.created_at).getTime() - new Date(prevMsg.created_at).getTime() > 30 * 60 * 1000);
                      if (msg.is_system) {
                        return (
                          <div key={msg._id || msg.id || i} className="flex justify-center w-full my-4">
                            <span className="bg-[#E8E8ED] text-[#1D1D1F] px-4 py-1.5 rounded-full text-[13px] font-medium">
                              {msg.content}
                            </span>
                          </div>
                        );
                      }

                      return (
                        <div
                          key={msg._id || msg.id || i}
                          ref={(el) => {
                            messageRefs.current[msg._id || msg.id] = el;
                          }}
                          className={`flex flex-col transition-colors duration-500 mb-2 ${msg.poll_data ? "items-center" : isSender ? "items-end" : "items-start"}`}
                        >
                          {showTime && (
                            <div className="flex justify-center w-full my-3">
                              <span className="text-[11px] font-medium text-[#6E6E73]">
                                {formatRelativeTime(parseUTC(msg.created_at))}
                              </span>
                            </div>
                          )}
                          <div 
                            className={`group relative flex flex-col ${msg.poll_data ? "w-full items-center" : `max-w-[85%] ${isSender ? "items-end" : "items-start"}`}`}
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
                                  : msg.poll_data || (msg.content && msg.content.startsWith("Shared document preview and link to access"))
                                  ? "bg-transparent p-0"
                                  : isSender
                                  ? `${getThemeBgClass(conversationTheme)} text-white p-4`
                                  : "bg-[#E8E8ED] text-[#1D1D1F] p-4"
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
                                    <a key={idx} href={att.url && att.url.startsWith("http") ? att.url : `${API_URL}/storage/${att.url}`} target="_blank" rel="noreferrer" className={`flex items-center gap-2 p-2 rounded-[10px] ${isSender ? "bg-[#0055C6] text-white" : "bg-[#E8E8ED] text-[#1D1D1F]"}`}>
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
                              
                              {msg.poll_data && (
                                <PollMessage 
                                  messageId={msg._id || msg.id}
                                  pollData={msg.poll_data}
                                  currentUserId={user?._id}
                                  onVote={handleVote}
                                />
                              )}

                              {!msg.is_recalled && !msg.poll_data && msg.content && msg.content !== "Tin nhắn thoại" && (
                                msg.content.startsWith("Shared document preview and link to access") ? (
                                  (() => {
                                    const match = msg.content.match(/access ([\s\S]+) at internal reference ([\s\S]+)/);
                                    if (match) {
                                      return (
                                        <a href={`/tai-lieu/${match[2]}`} target="_blank" rel="noreferrer" className={`flex flex-col gap-2 p-3 rounded-[16px] border shadow-sm ${isSender ? "bg-[#0071E3] border-white/20 text-white" : "bg-white border-[#D2D2D7] text-[#1D1D1F]"} transition-all hover:opacity-90 w-full min-w-[240px] max-w-[280px]`}>
                                          <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 shrink-0 rounded-[10px] flex items-center justify-center ${isSender ? "bg-white/20" : "bg-[#F5F5F7]"}`}>
                                              <FileText className={`w-5 h-5 ${isSender ? "text-white" : "text-[#0071E3]"}`} />
                                            </div>
                                            <div className="flex flex-col overflow-hidden">
                                              <span className="text-[14px] font-semibold truncate leading-tight">{match[1]}</span>
                                              <span className={`text-[12px] mt-0.5 ${isSender ? "text-white/80" : "text-[#6E6E73]"}`}>Tài liệu DocLib</span>
                                            </div>
                                          </div>
                                          <div className={`text-[12px] px-3 py-1.5 rounded-full text-center font-medium mt-1 ${isSender ? "bg-white/10 text-white" : "bg-[#F5F5F7] text-[#0071E3]"}`}>
                                            Xem chi tiết
                                          </div>
                                        </a>
                                      );
                                    }
                                    return <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">{msg.content}</p>;
                                  })()
                                ) : (
                                  <p className="text-[15px] leading-[1.4] whitespace-pre-wrap">{msg.content}</p>
                                )
                              )}
                              {msg.is_recalled && (
                                <span className="text-[13px] italic flex items-center h-full">Tin nhắn đã thu hồi</span>
                              )}
                            </div>
                            {!msg.poll_data && (
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
                            )}
                            </div>
                            
                            {!msg.poll_data && isSender && i === messages.length - 1 && (
                              <div className="flex justify-end mt-1 mr-1">
                                <div className="w-5 h-5 rounded-full overflow-hidden border-[1.5px] border-white shadow-sm">
                                  {selectedConv.other_user?.avatar_url ? (
                                    <img src={selectedConv.other_user.avatar_url} className="w-full h-full object-cover" alt="" />
                                  ) : (
                                    <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[12px] font-semibold uppercase">
                                      {(aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username || "U").charAt(0)}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                      );
                    })}
                    {typingUsers[selectedConv.other_user_id] && (
                      <div className="flex w-full mb-4 justify-start">
                        <div className="flex gap-2 items-end max-w-[70%]">
                          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#E8E8ED] flex items-center justify-center overflow-hidden">
                            {selectedConv.other_user?.avatar_url ? (
                              <img src={selectedConv.other_user.avatar_url} className="w-full h-full object-cover" alt="" />
                            ) : (
                              <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[11px] font-semibold uppercase">
                                {(aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username || "U").charAt(0)}
                              </div>
                            )}
                          </div>
                          <div className="px-4 py-3 rounded-[18px] bg-[#F5F5F7] rounded-bl-[4px]">
                            <div className="flex gap-1.5 h-2 items-center">
                              <span className="w-1.5 h-1.5 bg-[#86868B] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                              <span className="w-1.5 h-1.5 bg-[#86868B] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                              <span className="w-1.5 h-1.5 bg-[#86868B] rounded-full animate-bounce"></span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>


              <SmartQuickReplies 
                replies={quickReplies} 
                onSelect={(text) => handleSend(text)}
              />
              {(() => {
                const isGroupAdmin = isGroupConv && selectedConv?.created_by === (user?._id || (user as any)?.id);
                const isGroupDeputy = isGroupConv && selectedConv?.deputies?.includes(user?._id || (user as any)?.id);
                const cannotMessage = isGroupConv && selectedConv?.messaging_restricted && !isGroupAdmin && !isGroupDeputy;
                
                if (cannotMessage) {
                  return (
                    <div className="flex justify-center p-4 py-8">
                      <span className="text-[13px] text-[#6E6E73] bg-[#E8E8ED] px-4 py-2 rounded-full font-medium">Chỉ trưởng nhóm và phó nhóm mới được gửi tin nhắn</span>
                    </div>
                  );
                }
                
                return (
              <div className="px-4 pb-4 pt-2 bg-transparent relative">
                <ReplyBlock replyingTo={replyingTo} onCancel={() => setReplyingTo(null)} />
                {editingMsg && (
                  <div className="absolute bottom-full left-0 w-full bg-white/95 backdrop-blur-md border-t border-[#E8E8ED] px-4 py-2.5 flex items-center justify-between z-10 animate-in slide-in-from-bottom-2 fade-in duration-200">
                    <div className="flex flex-col flex-1 overflow-hidden pr-4 border-l-2 border-[#0071E3] pl-3">
                      <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#0071E3] mb-0.5">
                        <Edit2 className="w-3.5 h-3.5" />
                        <span>Đang chỉnh sửa tin nhắn</span>
                      </div>
                      <p className="text-[14px] text-[#6E6E73] truncate">
                        {editingMsg.content || (editingMsg.image_url ? "[Hình ảnh]" : editingMsg.poll_data ? "[Bình chọn]" : "[Đính kèm]")}
                      </p>
                    </div>
                    <button 
                      onClick={() => { setEditingMsg(null); setNewMessage(""); }}
                      className="w-7 h-7 flex items-center justify-center rounded-full hover:bg-[#F5F5F7] text-[#6E6E73] transition-colors shrink-0"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
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
                          className="absolute left-1.5 top-1/2 -translate-y-1/2 w-[36px] h-[36px] flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
                        >
                          <Paperclip className="w-[18px] h-[18px]" />
                        </button>
                        <button
                          onClick={openShareDoc}
                          className="absolute left-[40px] top-1/2 -translate-y-1/2 w-[36px] h-[36px] flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
                        >
                          <FileText className="w-[18px] h-[18px]" />
                        </button>
                        <button
                          onClick={() => setShowPollModal(true)}
                          className="absolute left-[78px] top-1/2 -translate-y-1/2 w-[36px] h-[36px] flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
                        >
                          <BarChart2 className="w-[18px] h-[18px]" />
                        </button>
                        <button
                          onClick={() => setShowScheduleModal(true)}
                          className="absolute left-[116px] top-1/2 -translate-y-1/2 w-[36px] h-[36px] flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
                        >
                          <Clock className="w-[18px] h-[18px]" />
                        </button>
                        <input
                          type="text"
                          value={newMessage}
                          onChange={handleTyping}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSend();
                          }}
                          placeholder=""
                          className="w-full h-[44px] bg-white border border-transparent rounded-[980px] pl-[158px] pr-[44px] text-[15px] focus:outline-none focus:border-[#D2D2D7]"
                        />
                        <button
                          onClick={handleStartRecording}
                          className="absolute right-1.5 top-1/2 -translate-y-1/2 w-[36px] h-[36px] flex items-center justify-center text-[#0071E3] hover:bg-[#F5F5F7] rounded-full z-10 transition-colors"
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
                    className={`w-[44px] h-[44px] flex-shrink-0 flex items-center justify-center ${getThemeBgClass(conversationTheme)} text-white rounded-full hover:opacity-80 disabled:opacity-50 transition-colors`}
                  >
                    <Send className="w-[20px] h-[20px] relative -left-[1px] top-[1px]" />
                  </button>
                </div>
              </div>
                );
              })()}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center w-full h-full min-h-[500px]">
              <span className="text-[17px] text-[#6E6E73]">
                Chưa có dữ liệu
              </span>
            </div>
          )}
        </div>
        



        {showSharedSidebar && selectedConv && (
          <div className="w-[300px] md:w-[320px] shrink-0 bg-[#F5F5F7] border-l border-[#D2D2D7] flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto hide-scrollbar pt-6">
              {/* Profile Section */}
              <div className="flex flex-col items-center px-4 pb-6">
                <div className="w-24 h-24 rounded-full bg-[#D2D2D7] overflow-hidden mb-3 relative shadow-sm group">
                  {isGroupConv ? (
                    (selectedConv.group_avatar || selectedConv.other_user?.avatar_url) ? (
                      <img src={selectedConv.group_avatar || selectedConv.other_user?.avatar_url} className="w-full h-full object-cover" alt="" />
                    ) : (
                      <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[40px] font-semibold uppercase">
                        {(selectedConv.group_name || selectedConv.other_user?.full_name || "G").charAt(0)}
                      </div>
                    )
                  ) : (
                    selectedConv.other_user?.avatar_url ? (
                      <img src={selectedConv.other_user.avatar_url} className="w-full h-full object-cover" alt="" />
                    ) : (
                      <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[40px] font-semibold uppercase">
                        {(aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username || "U").charAt(0)}
                      </div>
                    )
                  )}
                  {!isGroupConv && onlineUsers[selectedConv.other_user_id] === true && (
                    <span className="absolute bottom-1 right-1 w-4 h-4 bg-green-500 border-[3px] border-[#F5F5F7] rounded-full"></span>
                  )}
                  {isGroupConv && (
                    <div onClick={() => groupAvatarInputRef.current?.click()} className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                      <Camera className="w-8 h-8 text-white" />
                      <input 
                        type="file" 
                        accept="image/*" 
                        ref={groupAvatarInputRef} 
                        className="hidden" 
                        onChange={handleGroupAvatarUpload} 
                      />
                    </div>
                  )}
                </div>
                <h4 className="text-[20px] font-semibold text-[#1D1D1F] text-center leading-tight mt-1 mb-1">
                  {isGroupConv 
                    ? (selectedConv.group_name || selectedConv.other_user?.full_name || "Nhóm trò chuyện") 
                    : (aliases[selectedConv.other_user_id] || selectedConv.other_user?.full_name || selectedConv.other_user?.username)}
                </h4>
                <p className="text-[14px] text-[#6E6E73] mt-1 text-center px-4">
                  {renderOnlineStatus(selectedConv.other_user_id, isGroupConv, selectedConv.participant_ids?.length)}
                </p>
              </div>

              {/* Actions Section */}
              <div className="mt-2 px-3 space-y-4">
                <div className="bg-white rounded-[16px] shadow-sm border border-[#E8E8ED] overflow-hidden divide-y divide-[#E8E8ED]">
                  {!isGroupConv && (
                    <button onClick={() => { setAliasInput(aliases[selectedConv.other_user_id] || ""); setShowAliasModal(true); }} className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                      <span className="text-[15px] text-[#1D1D1F] font-medium">Đổi biệt danh</span>
                      <ChevronRight className="w-4 h-4 text-[#A1A1A6]" />
                    </button>
                  )}
                  <button onClick={handleToggleMute} className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                    <span className="text-[15px] text-[#1D1D1F] font-medium">Âm báo</span>
                    <span className="text-[14px] text-[#86868B]">{isMuted ? "Tắt" : "Bật"}</span>
                  </button>
                  <div className="px-4 py-3 flex items-center justify-between">
                    <span className="text-[15px] text-[#1D1D1F] font-medium">Chủ đề</span>
                    <div className="flex gap-2">
                      <button onClick={() => updateTheme("default")} className="w-5 h-5 rounded-full bg-[#0071E3] border border-transparent hover:border-black" />
                      <button onClick={() => updateTheme("red")} className="w-5 h-5 rounded-full bg-red-500 border border-transparent hover:border-black" />
                      <button onClick={() => updateTheme("green")} className="w-5 h-5 rounded-full bg-green-500 border border-transparent hover:border-black" />
                      <button onClick={() => updateTheme("purple")} className="w-5 h-5 rounded-full bg-purple-500 border border-transparent hover:border-black" />
                    </div>
                  </div>
                  <div>
                    <button onClick={() => setShowSelfDestructMenu(!showSelfDestructMenu)} className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                      <span className="text-[15px] text-[#1D1D1F] font-medium">Tự hủy tin</span>
                      <div className="flex items-center gap-1 text-[#86868B]">
                        <span className="text-[14px]">{selfDestructSeconds ? `${selfDestructSeconds}s` : "Tắt"}</span>
                        <ChevronRight className={`w-4 h-4 transition-transform ${showSelfDestructMenu ? "rotate-90" : ""}`} />
                      </div>
                    </button>
                    {showSelfDestructMenu && (
                      <div className="px-3 pb-2 pt-1 bg-[#F5F5F7]/50">
                        {[
                          { label: "Tắt", value: 0 },
                          { label: "5 giây", value: 5 },
                          { label: "10 giây", value: 10 },
                          { label: "1 phút", value: 60 },
                          { label: "5 phút", value: 300 },
                        ].map((opt) => (
                          <button
                            key={opt.value}
                            onClick={() => { setSelfDestructSeconds(opt.value); setShowSelfDestructMenu(false); }}
                            className={`w-full text-left py-2 px-3 rounded-[8px] flex items-center justify-between text-[14px] ${selfDestructSeconds === opt.value ? "bg-[#0071E3]/10 text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-black/5"}`}
                          >
                            {opt.label}
                            {selfDestructSeconds === opt.value && <Check className="w-4 h-4 text-[#0071E3]" />}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Media */}
                <div className="bg-white rounded-[16px] shadow-sm border border-[#E8E8ED] p-4">
                  <h5 className="text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wider mb-3">File phương tiện</h5>
                  {sharedAttachments.length > 0 ? (
                    <div className="grid grid-cols-3 gap-2">
                      {sharedAttachments.slice(0, 6).map((att: any, idx: number) => {
                        const url = att.url || "";
                        const href = url ? (url.startsWith("http") ? url : `${API_URL}/storage/${url}`) : "#";
                        const isImg = url.match(/\.(jpeg|jpg|gif|png)$/i);
                        return (
                          <a 
                            key={idx} 
                            href={href} 
                            target="_blank" 
                            rel="noreferrer"
                            className="aspect-square bg-[#F5F5F7] rounded-[8px] flex flex-col items-center justify-center text-[#A1A1A6] hover:bg-[#E8E8ED] transition-colors p-1 cursor-pointer overflow-hidden border border-[#D2D2D7]/50"
                          >
                            {isImg ? (
                              <img src={href} className="w-full h-full object-cover rounded-[6px]" alt="" />
                            ) : url.match(/\.(mp4|webm|mov)$/i) ? (
                              <Video className="w-6 h-6 mb-1 text-[#6E6E73]" />
                            ) : (
                              <FileText className="w-6 h-6 mb-1 text-[#6E6E73]" />
                            )}
                            {!isImg && (
                              <span className="text-[10px] text-[#6E6E73] truncate w-full text-center px-1">
                                {att.name || "File"}
                              </span>
                            )}
                          </a>
                        );
                      })}
                      {sharedAttachments.length > 6 && (
                        <div className="col-span-3 text-center mt-2 pt-2 border-t border-[#F5F5F7]">
                          <button className="text-[14px] text-[#0071E3] font-medium hover:underline">Xem tất cả ({sharedAttachments.length})</button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-4 bg-[#F5F5F7] rounded-[8px]">
                      <p className="text-[13px] text-[#6E6E73]">Chưa có file nào</p>
                    </div>
                  )}
                </div>

                {/* Group Settings / Info */}
                {isGroupConv && (
                  <>
                    <div className="mt-4 bg-white rounded-[16px] shadow-sm border border-[#E8E8ED] p-4">
                      <h5 className="text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wider mb-3">Thành viên ({selectedConv.participant_ids?.length || 0})</h5>
                      <div className="flex flex-col max-h-[150px] overflow-y-auto hide-scrollbar divide-y divide-[#E8E8ED]/50 -mx-2 px-2">
                        {(selectedConv.participant_ids || []).map((mId: string) => {
                          const mUser = Object.values(conversationsRef.current).find(c => c.other_user_id === mId)?.other_user || { _id: mId };
                          const isGroupAdmin = selectedConv.created_by === mId;
                          const isGroupDeputy = (selectedConv.deputies || []).includes(mId);
                          return (
                            <div key={mId} className="flex items-center gap-3 py-2 hover:bg-[#F5F5F7] rounded-[8px] transition-colors cursor-pointer px-2">
                              <div className="w-8 h-8 rounded-full bg-[#D2D2D7] overflow-hidden shrink-0">
                                {mUser?.avatar_url ? (
                                  <img src={mUser.avatar_url} className="w-full h-full object-cover" alt="" />
                                ) : (
                                  <div className="w-full h-full bg-[#0071E3] text-white flex items-center justify-center text-[12px] font-semibold uppercase">
                                    {(mUser?.full_name || mUser?.username || "U").charAt(0)}
                                  </div>
                                )}
                              </div>
                              <div className="flex flex-col flex-1 min-w-0">
                                <span className="text-[14px] font-medium text-[#1D1D1F] truncate">{mUser?.full_name || mUser?.username || "Thành viên"}</span>
                                {isGroupAdmin ? (
                                  <span className="text-[11px] text-[#0071E3] font-medium mt-0.5">Trưởng nhóm</span>
                                ) : isGroupDeputy ? (
                                  <span className="text-[11px] text-[#0071E3] mt-0.5">Phó nhóm</span>
                                ) : null}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                    
                    <div className="bg-white rounded-[16px] shadow-sm border border-[#E8E8ED] overflow-hidden divide-y divide-[#E8E8ED] mt-4 mb-2">
                       <button onClick={async () => {
                         try {
                           let token = selectedConv.invite_token;
                           if (!token) {
                             const res = await fetch(`${API_URL}/tin-nhan/nhom/${selectedConv._id || selectedConv.id}/link`, { method: "POST", headers: { "Authorization": `Bearer ${getToken()}` } });
                             const data = await res.json();
                             if (data.data?.invite_token) token = data.data.invite_token;
                           }
                           if (token) {
                             const link = `${window.location.origin}/tin-nhan/tham-gia/${token}`;
                             await navigator.clipboard.writeText(link);
                             showToast("Đã sao chép link mời nhóm", "success");
                           }
                         } catch (e) {
                           showToast("Không thể tạo link mời", "error");
                         }
                       }} className="w-full px-4 py-3 flex items-center gap-3 text-[15px] font-medium text-[#0071E3] hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                        <Share2 className="w-5 h-5" />
                        Sao chép link mời
                      </button>
                      <button onClick={() => {
                        const isGroupAdmin = selectedConv.created_by === (user?._id || (user as any)?.id);
                        const isGroupDeputy = (selectedConv.deputies || []).includes(user?._id || (user as any)?.id);
                        if (!isGroupAdmin && !isGroupDeputy) {
                          showToast("Chỉ trưởng nhóm và phó nhóm mới được đổi cài đặt", "error");
                          return;
                        }
                        setTempGroupSettings({
                          messaging_restricted: selectedConv.messaging_restricted || false,
                          requires_approval: selectedConv.requires_approval || false
                        });
                        setShowGroupSettingsModal(true);
                      }} className="w-full px-4 py-3 flex items-center gap-3 text-[15px] font-medium text-[#0071E3] hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                        <Settings2 className="w-5 h-5" />
                        Cài đặt nhóm
                      </button>
                      <button onClick={() => setShowLeaveGroupModal(true)} className="w-full px-4 py-3 flex items-center gap-3 text-[15px] font-medium text-red-500 hover:bg-red-50 active:bg-red-100 transition-colors">
                        <LogOut className="w-5 h-5" />
                        Rời nhóm
                      </button>
                    </div>
                  </>
                )}

                {/* Block */}
                {!isGroupConv && (
                  <div className="bg-white rounded-[16px] shadow-sm overflow-hidden border border-[#E8E8ED] mb-6">
                    <button onClick={handleBlockUser} className="w-full px-4 py-3 flex items-center gap-3 text-[15px] font-medium text-red-500 hover:bg-[#F5F5F7] active:bg-[#E8E8ED] transition-colors">
                      <ShieldAlert className="w-5 h-5" />
                      {isBlocked ? "Bỏ chặn người dùng" : "Chặn người dùng"}
                    </button>
                  </div>
                )}

              </div>
            </div>
          </div>
        )}
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
              placeholder=""
              className="apple-input w-full"
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
              className={`px-4 py-2 text-[14px] font-medium text-white ${getThemeBgClass(conversationTheme)} hover:opacity-80 rounded-full transition-colors`}
            >
              Lưu
            </button>
          </div>
        </ModalContent>
      </Modal>

      {activeMsgMenuId && activeMsgRect && activeMsgObj && (() => {
        const msgId = activeMsgObj._id || activeMsgObj.id;
        const isRecalled = activeMsgObj.is_recalled;
        const isSender = activeMsgRect.isSender;

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
            <div className="fixed inset-0 z-40 bg-black/25 backdrop-blur-[2px]" onClick={dismiss} />
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

            <div
              style={{ position: "fixed", zIndex: 60, ...hPos, ...vPos }}
              className={`flex w-max gap-2 ${showAbove ? "flex-col-reverse" : "flex-col"}`}
              onClick={(e) => e.stopPropagation()}
            >

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
                    onClick={() => { 
                      setActiveThreadParentId(msgId); 
                      dismiss(); 
                    }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    <MessageSquareReply className="w-[18px] h-[18px] text-[#6E6E73]" />
                    Phản hồi theo luồng {activeMsgObj?.thread_count > 0 ? `(${activeMsgObj.thread_count})` : ''}
                  </button>
                )}

                {!isRecalled && (
                  <button
                    onClick={() => { setShowForwardModal(msgId); dismiss(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 text-[15px] text-[#1D1D1F] hover:bg-[#F5F5F7] border-b border-[#F2F2F7] text-left transition-colors"
                  >
                    <Share2 className="w-[18px] h-[18px] text-[#6E6E73]" />
                    Chuyển tiếp
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
                        Thu hồi tin nhắn
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
      <ScheduleModal
        isOpen={showScheduleModal}
        onClose={() => setShowScheduleModal(false)}
        onSchedule={handleScheduleSend}
      />
    </div>
  );
}
