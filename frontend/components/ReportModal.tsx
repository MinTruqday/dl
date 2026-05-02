"use client";

import { useState } from "react";
import { AlertTriangle, X, Send, Loader2, ShieldAlert } from "lucide-react";
import { createReportAPI } from "@/services/moderation.service";
import { getToken } from "@/services/auth.service";
import { useToast } from "@/contexts/ToastContext";

interface ReportModalProps {
  itemId: string;
  itemType: "document" | "comment" | "post" | "user";
  onClose: () => void;
}

export default function ReportModal({ itemId, itemType, onClose }: ReportModalProps) {
  const [reason, setReason] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async () => {
    if (!reason.trim()) {
        showToast("Vui lòng nhập lý do báo cáo", "error");
        return;
    }
    
    setIsSubmitting(true);
    try {
      await createReportAPI({
        item_id: itemId,
        item_type: itemType,
        reason: reason,
        description: description
      });

      showToast("Báo cáo đã được gửi tới hội đồng điều hành", "success");
      setTimeout(onClose, 2000);
    } catch (err: any) {
      showToast(err.message || "Mất kết nối với hệ thống điều hành", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-[1001] animate-in fade-in duration-300 p-6 font-sans">
      
      
      <div className="bg-white p-12 w-full max-w-lg border border-zinc-100 animate-in zoom-in-95 duration-300 rounded-sm">
        <div className="flex justify-between items-center mb-12">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-zinc-50 flex items-center justify-center rounded-sm">
                <ShieldAlert className="w-5 h-5 text-black" />
            </div>
            <div>
                <h3 className="text-sm font-bold text-black uppercase tracking-widest">Báo cáo vi phạm</h3>
                <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest mt-1">Bảo vệ sự trong sạch của mạng lưới tri thức</p>
            </div>
          </div>
          <button onClick={onClose} className="p-3 hover:bg-zinc-50 transition-all active:scale-90 rounded-sm">
            <X className="w-5 h-5 text-zinc-300" />
          </button>
        </div>

        <div className="space-y-8">
            <div className="space-y-3">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Lý do chính yếu</label>
                <input
                    type="text"
                    className="w-full h-14 px-6 bg-zinc-50 border border-zinc-50 text-sm font-medium focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm placeholder:text-zinc-200"
                    placeholder=""
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    disabled={isSubmitting}
                />
            </div>

            <div className="space-y-3">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Mô tả chi tiết (Tùy chọn)</label>
                <textarea
                    className="w-full p-6 bg-zinc-50 border border-zinc-50 text-sm font-medium h-32 resize-none focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm placeholder:text-zinc-200"
                    placeholder=""
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={isSubmitting}
                />
            </div>

            <div className="pt-4">
                <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.4em] hover:bg-zinc-800 transition-all active:scale-95 flex items-center justify-center gap-4 rounded-sm disabled:opacity-50"
                >
                    {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    Gửi báo cáo hệ thống
                </button>
            </div>
        </div>
        
        <p className="text-[9px] text-center text-zinc-300 font-bold uppercase tracking-widest mt-10">
            Hành động này sẽ được ghi nhận và xem xét bởi đội ngũ điều hành trong 24h
        </p>
      </div>
    </div>
  );
}