"use client";

import { useEffect, useState } from "react";
import { getApprovalQueueAPI, moderateDocumentAPI } from "@/features/content/services/document_drafts.service";
import { Loader2, ShieldCheck, Eye, CheckCircle, XCircle, AlertOctagon } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter, ModalDescription } from "@/shared/components/ui/Modal";

export default function ApprovalPage() {
  const { showToast } = useToast();
  const [pendingDocs, setPendingDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [visible, setVisible] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{ type: "approve" | "reject"; data: any } | null>(null);

  useEffect(() => { fetchPending(); }, []);

  const fetchPending = async () => {
    setLoading(true);
    try {
      const data = await getApprovalQueueAPI();
      setPendingDocs(data.data || data || []);
    } catch { showToast("Không thể tải danh sách phê duyệt", "error"); } finally { setLoading(false); requestAnimationFrame(() => setVisible(true)); }
  };

  const handleReview = async (documentId: string, status: string) => {
    setIsProcessing(true);
    try {
      await moderateDocumentAPI(documentId, status, status === "PUBLISHED" ? "Đã phê duyệt dựa trên tiêu chuẩn nội dung." : "Nội dung không đáp ứng yêu cầu hệ thống.");
      showToast(status === "PUBLISHED" ? "Đã phê duyệt tài liệu." : "Đã từ chối tài liệu.", "success");
      fetchPending(); setConfirmModal(null);
    } catch (err: any) { showToast(err.message || "Lỗi thao tác phê duyệt.", "error"); } finally { setIsProcessing(false); }
  };

  return (
    <div className="flex flex-col h-full font-sans">
      <div className={`border-b border-[#E8E8ED] pb-6 mb-6 shrink-0 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[24px] font-semibold text-[#1D1D1F] mb-2 flex items-center gap-2">Duyệt bản thảo</h1>
            <p className="text-[15px] text-[#6E6E73]">Kiểm duyệt các tác phẩm mới xuất bản</p>
          </div>
          {pendingDocs.length > 0 && (
            <div className="px-4 py-2 bg-[#FF9F0A]/10 border border-[#FF9F0A]/20 rounded-full flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#FF9F0A] animate-pulse" />
              <span className="text-[13px] font-medium text-[#FF9F0A]">{pendingDocs.length} chờ duyệt</span>
            </div>
          )}
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] border border-[#E8E8ED] rounded-[24px]">
            <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
            <p className="text-[13px] font-medium text-[#6E6E73]">Đang đồng bộ dữ liệu...</p>
          </div>
        ) : pendingDocs.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] border border-[#E8E8ED] rounded-[24px] p-12 text-center">
            <div className="w-16 h-16 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-4">
              <ShieldCheck className="w-8 h-8 text-[#34C759]" />
            </div>
            <h3 className="text-[17px] font-semibold text-[#1D1D1F] mb-2">Hàng đợi trống</h3>
            <p className="text-[15px] text-[#6E6E73] max-w-sm">Tất cả bản thảo đã được kiểm duyệt. Hệ thống hiện không có tác phẩm nào đang chờ xử lý.</p>
          </div>
        ) : (
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 pb-6">
            {pendingDocs.map((doc: any) => (
              <div key={doc._id} className="bg-[#F5F5F7] border-[#E8E8ED] p-6 rounded-[24px] flex flex-col group hover: transition-all duration-300">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 bg-[#FF9F0A]/10 text-[#FF9F0A] text-[12px] font-medium rounded-md">Chờ duyệt</span>
                      <span className="text-[12px] text-[#6E6E73]">{new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                    </div>
                    <h4 className="font-semibold text-[17px] text-[#1D1D1F] line-clamp-2 leading-relaxed">{doc.title || "Tác phẩm chưa có tiêu đề"}</h4>
                    <p className="text-[13px] text-[#6E6E73] truncate">Tác giả: <span className="font-medium text-[#1D1D1F]">{doc.author_name || "Ẩn danh"}</span></p>
                  </div>
                  <button onClick={() => window.open(`/tai-lieu/viewer/${doc._id}`, "_blank")} className="w-10 h-10 bg-[#F5F5F7] hover:bg-[#0071E3] text-[#6E6E73] hover:text-white rounded-full flex items-center justify-center shrink-0 transition-colors shadow-sm" title="Xem chi tiết">
                    <Eye className="w-5 h-5" />
                  </button>
                </div>
                <div className="bg-[#F5F5F7] p-4 rounded-[14px] border border-[#E8E8ED] mb-6 flex-1">
                  <p className="text-[13px] text-[#1D1D1F] line-clamp-3 leading-relaxed font-medium">{doc.description || "Không có mô tả chi tiết cho bản thảo này."}</p>
                </div>
                <div className="flex gap-3 mt-auto pt-4 border-t border-[#E8E8ED]">
                  <button onClick={() => setConfirmModal({ type: "reject", data: doc })} className="flex-1 h-[44px] bg-white border border-[#FF3B30]/30 text-[#FF3B30] hover:bg-[#FFEBEB] text-[15px] font-medium rounded-full transition-colors flex items-center justify-center gap-2">
                    <XCircle className="w-4 h-4" /> Từ chối
                  </button>
                  <button onClick={() => setConfirmModal({ type: "approve", data: doc })} className="flex-1 h-[44px] bg-[#0071E3] text-white hover:bg-[#0077ED] text-[15px] font-medium rounded-full transition-colors flex items-center justify-center gap-2 shadow-sm">
                    <CheckCircle className="w-4 h-4" /> Phê duyệt
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal isOpen={!!confirmModal} onClose={() => !isProcessing && setConfirmModal(null)} className="max-w-md rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-0 shadow-lg overflow-hidden">
        <ModalHeader className={`border-b border-[#E8E8ED] p-6 ${confirmModal?.type === 'reject' ? 'bg-[#FF3B30]/10' : 'bg-[#34C759]/10'}`}>
          <ModalTitle className={`text-[17px] font-semibold flex items-center gap-2 ${confirmModal?.type === 'reject' ? 'text-[#FF3B30]' : 'text-[#34C759]'}`}>
            {confirmModal?.type === "approve" ? <><ShieldCheck className="w-5 h-5" /> Xác nhận phê duyệt</> : <><AlertOctagon className="w-5 h-5" /> Xác nhận từ chối</>}
          </ModalTitle>
          <ModalDescription className={`text-[13px] mt-2 ml-7 ${confirmModal?.type === 'reject' ? 'text-[#FF3B30]' : 'text-[#34C759]'}`}>Kiểm duyệt bản thảo</ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="bg-[#F5F5F7] border border-[#E8E8ED] p-4 rounded-[14px] mb-4">
            <h4 className="text-[15px] font-semibold text-[#1D1D1F] mb-1 line-clamp-1">{confirmModal?.data?.title}</h4>
            <p className="text-[13px] text-[#6E6E73]">Tác giả: {confirmModal?.data?.author_name}</p>
          </div>
          <p className="text-[15px] font-medium text-[#1D1D1F] leading-relaxed">
            {confirmModal?.type === "approve" ? "Tác phẩm này sẽ được xuất bản công khai và có thể được tìm thấy bởi độc giả. Bạn chắc chắn chứ?" : "Tác phẩm này sẽ bị trả về cho tác giả. Họ sẽ cần chỉnh sửa và gửi lại yêu cầu phê duyệt."}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-[#E8E8ED] p-6 bg-[#F5F5F7]">
          <button onClick={() => setConfirmModal(null)} className="flex-1 h-[44px] bg-white border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] rounded-full hover:bg-[#E8E8ED] transition-colors">Hủy bỏ</button>
          <button onClick={() => handleReview(confirmModal?.data._id, confirmModal?.type === "approve" ? "PUBLISHED" : "REJECTED")} disabled={isProcessing} className={`flex-1 h-[44px] text-white text-[15px] font-medium rounded-full flex items-center justify-center disabled:opacity-50 transition-colors gap-2 ${confirmModal?.type === "approve" ? "bg-[#0071E3] hover:bg-[#0077ED]" : "bg-[#FF3B30] hover:bg-[#E0332A]"}`}>
            {isProcessing && <Loader2 className="w-5 h-5 animate-spin" />} Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
