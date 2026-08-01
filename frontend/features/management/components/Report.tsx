"use client";

import { useState } from "react";
import { Send, Loader2, ShieldAlert } from "lucide-react";
import { submitReportAPI } from "@/features/management/services/user_feedback.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
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
      showToast("Chọn lý do báo cáo", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      await submitReportAPI({
        item_id: itemId,
        item_type: itemType,
        reason: reason,
        description: detail,
      });

      showToast("Đã gửi báo cáo", "success");
      onClose();
    } catch (err: any) {
      showToast(err.message || "Không thể gửi báo cáo", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose}>
      <ModalHeader>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-control bg-danger-soft">
            <ShieldAlert className="h-5 w-5 text-danger" />
          </div>
          <div>
            <ModalTitle>Báo cáo vi phạm</ModalTitle>
          </div>
        </div>
      </ModalHeader>

      <ModalContent>
        <div className="space-y-3">
          <label className="text-[14px] font-medium text-ink">
            Lý do chính
          </label>
          <input
            type="text"
            className="apple-input"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-3">
          <label className="text-[14px] font-medium text-ink">
            Chi tiết bổ sung
          </label>
          <textarea
            className="min-h-28 w-full resize-y rounded-control border border-border bg-surface px-3 py-3 text-[15px] text-ink outline-none focus:border-brand focus:ring-2 focus:ring-brand-soft"
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <button onClick={onClose} disabled={isSubmitting} className="secondary-button">Hủy</button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="pill-button gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            Gửi báo cáo
          </button>
        </div>
      </ModalContent>

    </Modal>
  );
}
