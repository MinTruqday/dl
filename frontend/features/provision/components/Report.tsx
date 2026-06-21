"use client";

import { useState } from "react";
import { Send, Loader2, ShieldAlert } from "lucide-react";
import { submitReportAPI } from "@/features/provision/services/system_report.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

interface ReportProps {
  itemId: string;
  itemType: "document" | "comment" | "post" | "user";
  onClose: () => void;
}

export default function Report({ itemId, itemType, onClose }: ReportProps) {
  const [reason, setReason] = useState("");
  const [detail, setDetail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  const handleSubmit = async () => {
    if (!reason.trim()) {
      showToast("Vui lòng cung cấp lý do báo cáo", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      await submitReportAPI({
        item_id: itemId,
        item_type: itemType,
        reason: reason,
        detail: detail,
      });

      showToast("Báo cáo đã được gửi tới hội đồng điều hành", "success");
      setTimeout(onClose, 2000);
    } catch (err: any) {
      showToast(err.message || "Gửi báo cáo thất bại", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose}>
      <ModalHeader>
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-black flex items-center justify-center rounded-sm">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <ModalTitle>Báo cáo vi phạm</ModalTitle>
            <ModalDescription>
              Duy trì tiêu chuẩn nội dung của hệ thống
            </ModalDescription>
          </div>
        </div>
      </ModalHeader>

      <ModalContent>
        <div className="space-y-3">
          <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">
            Lý do chính
          </label>
          <input
            type="text"
            className="w-full h-14 px-6 bg-white border border-zinc-100 text-sm font-medium focus:outline-none focus:border-black rounded-sm"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-3">
          <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">
            Chi tiết bổ sung
          </label>
          <textarea
            className="w-full p-6 bg-white border border-zinc-100 text-sm font-medium h-32 resize-none focus:outline-none focus:border-black rounded-sm"
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="pt-4">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.4em] active:scale-95 flex items-center justify-center gap-4 rounded-sm disabled:opacity-50 "
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Gửi báo cáo hệ thống
          </button>
        </div>
      </ModalContent>

      <ModalFooter>
        <p className="text-[9px] text-zinc-300 font-bold uppercase tracking-widest">
          Hành động này sẽ được ghi nhận và xem xét bởi đội ngũ điều hành trong
          vòng 24 giờ làm việc
        </p>
      </ModalFooter>
    </Modal>
  );
}
