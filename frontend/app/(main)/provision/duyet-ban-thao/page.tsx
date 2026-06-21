"use client";

import { useEffect, useState } from "react";
import {
  getApprovalQueueAPI,
  moderateDocumentAPI,
} from "@/features/content/services/document_drafts.service";
import { Loader2, ShieldCheck, Eye } from "lucide-react";
import { useToast } from "@/shared/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

export default function ApprovalPage() {
  const { showToast } = useToast();
  const [pendingDocs, setPendingDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    type: "approve" | "reject";
    data: any;
  } | null>(null);

  useEffect(() => {
    fetchPending();
  }, []);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const data = await getApprovalQueueAPI();
      setPendingDocs(data.data || data || []);
    } catch (err) {
      showToast("Không thể tải danh sách phê duyệt", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (documentId: string, status: string) => {
    setIsProcessing(true);
    try {
      await moderateDocumentAPI(
        documentId,
        status,
        status === "PUBLISHED"
          ? "Đã phê duyệt dựa trên tiêu chuẩn nội dung."
          : "Nội dung không đáp ứng yêu cầu hệ thống.",
      );
      showToast(
        status === "PUBLISHED"
          ? "Đã phê duyệt tài liệu."
          : "Đã từ chối tài liệu.",
        "success",
      );
      fetchPending();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi thao tác phê duyệt.", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="py-24 flex justify-center border border-zinc-200 bg-white rounded-2xl">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : pendingDocs.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl">
          <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
        </div>
      ) : (
        <div
          className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-300"
          style={{ animationDelay: "150ms", animationFillMode: "both" }}
        >
          {pendingDocs.map((doc: any) => (
            <div
              key={doc._id}
              className="p-6 border border-zinc-200 bg-white space-y-4  "
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <h4 className="font-semibold text-base text-black">
                    {doc.title}
                  </h4>
                  <div className="flex items-center gap-3 text-xs font-medium text-zinc-400">
                    <span>
                      Tác giả:{" "}
                      <span className="text-black">{doc.author_name}</span>
                    </span>
                    <span>•</span>
                    <span>
                      {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() =>
                    window.open(`/document/viewer/${doc._id}`, "_blank")
                  }
                  className="p-2 border border-zinc-200 text-zinc-400   "
                >
                  <Eye className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-zinc-600 line-clamp-2 leading-relaxed">
                {doc.description || "Không có mô tả chi tiết cho bản thảo này."}
              </p>
              <div className="flex justify-end gap-3 pt-4 border-t border-zinc-100">
                <button
                  onClick={() => setConfirmModal({ type: "reject", data: doc })}
                  className="px-4 py-2 text-xs font-semibold text-zinc-400  "
                >
                  Từ chối
                </button>
                <button
                  onClick={() =>
                    setConfirmModal({ type: "approve", data: doc })
                  }
                  className="px-4 py-2 bg-black text-white text-xs font-semibold border border-black  "
                >
                  Phê duyệt
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isProcessing && setConfirmModal(null)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>
            {confirmModal?.type === "approve" ? "Phê duyệt" : "Từ chối"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500">
            {confirmModal?.type === "approve"
              ? `Phê duyệt "${confirmModal?.data?.title}"?`
              : `Từ chối "${confirmModal?.data?.title}"?`}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmModal(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-none"
          >
            Hủy
          </button>
          <button
            onClick={() =>
              handleReview(
                confirmModal?.data._id,
                confirmModal?.type === "approve" ? "PUBLISHED" : "REJECTED",
              )
            }
            disabled={isProcessing}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black flex items-center justify-center gap-2 rounded-none"
          >
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin" />} Xác
            nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
