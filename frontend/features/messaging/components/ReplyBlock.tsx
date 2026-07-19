import { X, Reply as ReplyIcon } from "lucide-react";

interface ReplyBlockProps {
  replyingTo: any;
  onCancel: () => void;
}

export function ReplyBlock({ replyingTo, onCancel }: ReplyBlockProps) {
  if (!replyingTo) return null;

  return (
    <div className="absolute bottom-full left-0 w-full bg-white/95 backdrop-blur-md border-t border-[#E8E8ED] px-4 py-2.5 flex items-center justify-between z-10 animate-in slide-in-from-bottom-2 fade-in duration-200">
      <div className="flex flex-col flex-1 overflow-hidden pr-4 border-l-2 border-[#0071E3] pl-3">
        <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#0071E3] mb-0.5">
          <ReplyIcon className="w-3.5 h-3.5" />
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
