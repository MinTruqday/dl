"use client";

import { useState } from "react";
import { submitReportAPI } from "@/features/management/services/user_feedback.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
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
      showToast("Lỗi thiếu hụt nguyên nhân vi phạm", "error");
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

      showToast("Đồng bộ báo cáo tới hệ thống điều hành hoàn tất", "success");
      setTimeout(onClose, 2000);
    } catch (err: any) {
      showToast(err.message || "Lỗi đồng bộ báo cáo hệ thống", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose}>
      <ModalHeader>
        <ModalTitle>Báo cáo vi phạm</ModalTitle>
      </ModalHeader>

      <ModalContent>
        <div className="space-y-3">
          <label className="text-[13px] font-medium text-[var(--ink-muted)]">
            Lý do
          </label>
          <input
            type="text"
            className="field-control w-full"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-3">
          <label className="text-[13px] font-medium text-[var(--ink-muted)]">
            Chi tiết
          </label>
          <textarea
            className="field-control h-32 w-full resize-none"
            value={detail}
            onChange={(e) => setDetail(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

      </ModalContent>

      <ModalFooter>
        <button type="button" onClick={onClose} className="button-secondary">
          Hủy
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="button-primary disabled:opacity-50"
        >
          {isSubmitting ? "Đang gửi" : "Gửi báo cáo"}
        </button>
      </ModalFooter>
    </Modal>
  );
}
