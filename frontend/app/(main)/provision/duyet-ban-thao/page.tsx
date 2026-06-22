"use client";

import { useEffect, useState } from "react";
import {
  getApprovalQueueAPI,
  moderateDocumentAPI,
} from "@/features/content/services/document_drafts.service";
import { Loader2, ShieldCheck, Eye, CheckCircle, XCircle, FileText, AlertOctagon } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";

export default function ApprovalPage() {
  const { showToast } = useToast();
  const [pendingDocs, setPendingDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [visible, setVisible] = useState(false);
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
      requestAnimationFrame(() => setVisible(true));
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
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              Duyệt bản thảo
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Kiểm duyệt các tác phẩm mới xuất bản
            </p>
          </div>
          {pendingDocs.length > 0 && (
            <div className="px-3 py-1.5 bg-orange-50 border border-orange-100 rounded-xl flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
              <span className="text-[9px] font-bold uppercase tracking-widest text-orange-700">{pendingDocs.length} chờ duyệt</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang đồng bộ dữ liệu...</p>
          </div>
        ) : pendingDocs.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl p-12 text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
              <ShieldCheck className="w-8 h-8 text-green-500 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-2">Hàng đợi trống</h3>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
              Tất cả bản thảo đã được kiểm duyệt. Hệ thống hiện không có tác phẩm nào đang chờ xử lý.
            </p>
          </div>
        ) : (
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 pb-6">
            {pendingDocs.map((doc: any) => (
              <div
                key={doc._id}
                className="bg-white/90 backdrop-blur-md border border-zinc-100 p-5 rounded-3xl shadow-sm flex flex-col group hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-[8px] font-bold uppercase tracking-widest rounded-md">
                        Chờ duyệt
                      </span>
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                        {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-zinc-900 line-clamp-2 leading-relaxed">
                      {doc.title || "Tác phẩm chưa có tiêu đề"}
                    </h4>
                    <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest truncate">
                      Tác giả: <span className="text-zinc-900">{doc.author_name || "Ẩn danh"}</span>
                    </p>
                  </div>
                  <button
                    onClick={() => window.open(`/document/viewer/${doc._id}`, "_blank")}
                    className="w-8 h-8 bg-zinc-50 hover:bg-black text-zinc-400 hover:text-white rounded-xl flex items-center justify-center shrink-0 transition-colors shadow-sm"
                    title="Xem chi tiết"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="bg-zinc-50 p-3 rounded-2xl border border-zinc-100 mb-5 flex-1">
                  <p className="text-xs text-zinc-600 line-clamp-3 leading-relaxed font-medium">
                    {doc.description || "Không có mô tả chi tiết cho bản thảo này. Vui lòng xem chi tiết nội dung."}
                  </p>
                </div>

                <div className="flex gap-2 mt-auto pt-4 border-t border-zinc-100">
                  <button
                    onClick={() => setConfirmModal({ type: "reject", data: doc })}
                    className="flex-1 h-10 bg-white border border-red-200 text-red-600 hover:bg-red-50 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-colors flex items-center justify-center gap-1.5"
                  >
                    <XCircle className="w-3.5 h-3.5" /> Từ chối
                  </button>
                  <button
                    onClick={() => setConfirmModal({ type: "approve", data: doc })}
                    className="flex-1 h-10 bg-black text-white hover:bg-zinc-800 text-[10px] font-bold uppercase tracking-widest rounded-xl transition-colors flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <CheckCircle className="w-3.5 h-3.5" /> Phê duyệt
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isProcessing && setConfirmModal(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className={`border-b border-zinc-100 p-6 ${confirmModal?.type === 'reject' ? 'bg-red-50/50' : 'bg-green-50/50'}`}>
          <ModalTitle className={`text-sm font-bold tracking-tight flex items-center gap-2 ${confirmModal?.type === 'reject' ? 'text-red-600' : 'text-green-600'}`}>
            {confirmModal?.type === "approve" ? (
              <><ShieldCheck className="w-5 h-5" /> Xác nhận phê duyệt</>
            ) : (
              <><AlertOctagon className="w-5 h-5" /> Xác nhận từ chối</>
            )}
          </ModalTitle>
          <ModalDescription className={`text-[10px] font-bold uppercase tracking-widest mt-1 ml-7 ${confirmModal?.type === 'reject' ? 'text-red-400' : 'text-green-400'}`}>
            Kiểm duyệt bản thảo
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="bg-zinc-50 border border-zinc-100 p-4 rounded-2xl mb-4">
            <h4 className="text-sm font-bold text-black mb-1 line-clamp-1">{confirmModal?.data?.title}</h4>
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Tác giả: {confirmModal?.data?.author_name}</p>
          </div>
          <p className="text-xs font-medium text-zinc-700 leading-relaxed">
            {confirmModal?.type === "approve"
              ? "Tác phẩm này sẽ được xuất bản công khai và có thể được tìm thấy bởi độc giả. Bạn chắc chắn chứ?"
              : "Tác phẩm này sẽ bị trả về cho tác giả. Họ sẽ cần chỉnh sửa và gửi lại yêu cầu phê duyệt."}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setConfirmModal(null)}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl transition-all hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() =>
              handleReview(
                confirmModal?.data._id,
                confirmModal?.type === "approve" ? "PUBLISHED" : "REJECTED",
              )
            }
            disabled={isProcessing}
            className={`flex-1 h-11 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center disabled:opacity-50 transition-all hover:scale-[1.02] shadow-md gap-2 ${
              confirmModal?.type === "approve" ? "bg-black hover:bg-zinc-800" : "bg-red-600 hover:bg-red-700"
            }`}
          >
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />}
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
