"use client";

import { useState } from "react";
import InlineState from "@/shared/components/common/InlineState";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

export default function ReportDialog({
  onClose,
  onSubmit,
}: {
  onClose: () => void;
  onSubmit: (reason: string, detail: string) => Promise<boolean>;
}) {
  const [reason, setReason] = useState("");
  const [detail, setDetail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (!reason.trim()) {
      setError("Chọn lý do báo cáo");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const success = await onSubmit(reason.trim(), detail.trim());
      if (success) onClose();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể gửi báo cáo",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen onClose={onClose} className="max-w-md">
      <ModalHeader>
        <ModalTitle>Báo cáo tài liệu</ModalTitle>
      </ModalHeader>
      <ModalContent className="space-y-5">
        {error && (
          <InlineState title="Không thể gửi báo cáo" detail={error} tone="danger" />
        )}
        <label className="block">
          <span className="text-[13px] font-semibold text-ink">Lý do</span>
          <select
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="apple-input mt-2 w-full"
            disabled={submitting}
          >
            <option value="">Chọn lý do</option>
            <option value="Nội dung sai lệch">Nội dung sai lệch</option>
            <option value="Vi phạm bản quyền">Vi phạm bản quyền</option>
            <option value="Nội dung không phù hợp">Nội dung không phù hợp</option>
            <option value="Lý do khác">Lý do khác</option>
          </select>
        </label>
        <label className="block">
          <span className="text-[13px] font-semibold text-ink">Chi tiết</span>
          <textarea
            value={detail}
            onChange={(event) => setDetail(event.target.value)}
            className="apple-input mt-2 min-h-28 w-full resize-y"
            disabled={submitting}
          />
        </label>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={submitting}>
          Hủy
        </Button>
        <Button onClick={submit} disabled={submitting || !reason}>
          {submitting ? "Đang gửi" : "Gửi báo cáo"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
