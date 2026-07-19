import { useState } from "react";
import { X, Send, Search } from "lucide-react";
import { API_URL } from "@/core/config";
import { showToast } from "@/core/components/Toast";

interface ForwardModalProps {
  messageId: string;
  conversations: any[];
  user: any;
  onClose: () => void;
  onForward: (messageId: string, receiverIds: string[]) => Promise<void>;
}

export function ForwardModal({ messageId, conversations, user, onClose, onForward }: ForwardModalProps) {
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="bg-white rounded-[18px] w-full max-w-[400px] flex flex-col overflow-hidden shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#E8E8ED]">
          <h3 className="font-semibold text-[#1D1D1F] text-[17px]">Chuyển tiếp tin nhắn</h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-[#F5F5F7] text-[#6E6E73]">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 border-b border-[#E8E8ED]">
          <div className="relative">
            <Search className="w-4 h-4 text-[#6E6E73] absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text"
              placeholder="Tìm kiếm..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[#F5F5F7] text-[15px] rounded-[10px] pl-9 pr-4 py-2 outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto max-h-[300px] p-2">
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
                <img 
                  src={avatar || "https://i.pravatar.cc/150"} 
                  alt="" 
                  className="w-10 h-10 rounded-full object-cover border border-[#E8E8ED]" 
                />
                <span className="text-[15px] text-[#1D1D1F] font-medium truncate">{name || "Người dùng"}</span>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="p-4 text-center text-[#6E6E73] text-[15px]">Không tìm thấy cuộc trò chuyện nào</div>
          )}
        </div>

        <div className="p-4 border-t border-[#E8E8ED] bg-[#F5F5F7]">
          <button
            onClick={handleForward}
            disabled={selectedIds.length === 0 || isSubmitting}
            className="w-full bg-[#0071E3] text-white rounded-[10px] py-2.5 font-medium flex items-center justify-center gap-2 hover:bg-[#0055C6] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
            Gửi ({selectedIds.length})
          </button>
        </div>
      </div>
    </div>
  );
}
