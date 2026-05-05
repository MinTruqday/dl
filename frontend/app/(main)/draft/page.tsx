"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getApprovalQueueAPI,
  moderateDocumentAPI,
} from "@/services/draft.service";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { useRouter } from "next/navigation";

export default function DraftPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();
  
  const [pendingDocuments, setPendingDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    type: "approve" | "reject";
    data: any;
  } | null>(null);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const docsRes = await getApprovalQueueAPI();
      setPendingDocuments(docsRes.data || docsRes || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách bản thảo.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user) {
      if (user.role !== "admin" && user.role !== "moderator") {
        router.push("/");
      } else {
        fetchData();
      }
    }
  }, [user, authLoading, fetchData, router]);

  const reviewDocument = async (documentId: string, status: string) => {
    setIsProcessing(true);
    try {
      await moderateDocumentAPI(
        documentId,
        status,
        status === "PUBLISHED"
          ? "Đã phê duyệt dựa trên tiêu chuẩn nội dung."
          : "Nội dung không đáp ứng yêu cầu cộng đồng."
      );
      showToast(
        status === "PUBLISHED"
          ? "Đã phê duyệt tài liệu thành công."
          : "Đã từ chối tài liệu.",
        "success"
      );
      fetchData();
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi thao tác phê duyệt.", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Duyệt bản thảo</h1>
            <p className="text-sm text-zinc-500 mt-1">Hàng đợi kiểm duyệt và phát hành tác phẩm</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="text-sm font-medium text-zinc-500 hover:text-black transition-colors disabled:opacity-50"
            >
              {isRefreshing ? "Đang đồng bộ" : "Đồng bộ dữ liệu"}
            </button>
          </div>
        </header>

        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-black">
              Bản thảo đang chờ ({pendingDocuments.length})
            </h2>
          </div>
          
          {pendingDocuments.length === 0 ? (
            <div className="py-24 text-center border border-zinc-200 bg-white">
              <p className="text-sm font-medium text-zinc-500">Hàng chờ hiện đang trống</p>
            </div>
          ) : (
            <div className="border border-zinc-200 bg-white">
              {pendingDocuments.map((doc: any, index: number) => (
                <div key={doc._id} className={`p-6 ${index !== pendingDocuments.length - 1 ? 'border-b border-zinc-200' : ''}`}>
                  <div className="flex flex-col md:flex-row gap-6">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <h3 className="font-semibold text-lg text-black truncate">{doc.title}</h3>
                        <button
                          onClick={() => window.open(`/documents/viewer/${doc._id}`, "_blank")}
                          className="text-xs font-medium text-zinc-500 hover:text-black whitespace-nowrap transition-colors"
                        >
                          Đọc nội dung ↗
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-4 text-xs font-medium text-zinc-500">
                        <span>Tác giả: <span className="text-black">{doc.author_name}</span></span>
                        <span>•</span>
                        <span>Gửi ngày: {new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                      </div>
                      <p className="text-sm text-zinc-600 line-clamp-3 leading-relaxed">
                        {doc.description || "Tác phẩm này chưa được tác giả cung cấp mô tả chi tiết."}
                      </p>
                    </div>
                  </div>
                  <div className="flex justify-end gap-4 mt-6 pt-6 border-t border-zinc-100">
                    <button
                      onClick={() => setConfirmModal({ type: "reject", data: doc })}
                      className="text-xs font-semibold text-zinc-500 hover:text-black transition-colors"
                    >
                      Từ chối phát hành
                    </button>
                    <button
                      onClick={() => setConfirmModal({ type: "approve", data: doc })}
                      className="text-xs font-semibold text-black hover:underline underline-offset-4"
                    >
                      Phê duyệt
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {confirmModal && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-white/80 backdrop-blur-sm p-4">
          <div className="bg-white border border-zinc-200 w-full max-w-md p-6 shadow-none">
            <h3 className="text-lg font-semibold text-black mb-2">
              {confirmModal.type === "approve" ? "Phê duyệt nội dung" : "Từ chối nội dung"}
            </h3>
            <p className="text-sm text-zinc-500 mb-6 leading-relaxed">
              {confirmModal.type === "approve" 
                ? `Bạn có chắc chắn muốn phê duyệt tác phẩm "${confirmModal.data?.title}" để phát hành công khai?` 
                : `Bạn có chắc chắn muốn từ chối phát hành tác phẩm "${confirmModal.data?.title}"?`
              }
            </p>
            <div className="flex items-center justify-end gap-4 mt-6">
              <button
                onClick={() => !isProcessing && setConfirmModal(null)}
                disabled={isProcessing}
                className="px-4 py-2 text-sm font-medium text-zinc-500 hover:text-black transition-colors disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={() => reviewDocument(confirmModal.data._id, confirmModal.type === "approve" ? "PUBLISHED" : "REJECTED")}
                disabled={isProcessing}
                className="px-4 py-2 bg-black text-white text-sm font-medium border border-black hover:bg-zinc-800 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />} Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
