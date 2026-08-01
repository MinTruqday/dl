"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getTrashAPI,
  restoreDocumentAPI,
} from "@/features/content/services/document.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Trash2, FileText, RotateCcw } from "lucide-react";

export default function TrashPage() {
  const { showToast } = useToast();
  const [trash, setTrash] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTrash = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getTrashAPI();
      setTrash(data.data || data || []);
    } catch {
      showToast("Không thể tải dữ liệu lưu trữ tạm", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchTrash();
  }, [fetchTrash]);

  const handleRestoreDocument = async (docId: string) => {
    try {
      await restoreDocumentAPI(docId);
      showToast("Phục hồi dữ liệu tài liệu hoàn tất", "success");
      fetchTrash();
    } catch (e: any) {
      showToast(e.message || "Không thể khôi phục dữ liệu tài liệu", "error");
    }
  };

  return (
    <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6 font-sans text-ink">
      <div className="flex items-center justify-between">
        <h2 className="text-[20px] font-semibold text-ink">
          Thùng rác
        </h2>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex flex-col bg-white rounded-panel overflow-hidden animate-pulse border border-border">
              <div className="bg-border aspect-[4/3] w-full" />
              <div className="p-5 space-y-3">
                <div className="h-3 w-1/3 bg-border rounded-full" />
                <div className="h-4 w-full bg-border rounded-full" />
                <div className="h-4 w-2/3 bg-border rounded-full" />
              </div>
            </div>
          ))}
        </div>
      ) : !Array.isArray(trash) || trash.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center w-full text-center">
          <p className="text-[17px] text-ink-muted">Chưa có dữ liệu</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {trash.map((doc: any, idx: number) => (
            <div
              key={doc._id || doc.id || idx}
              className="group relative flex flex-col bg-white rounded-panel overflow-hidden transition-transform hover:scale-[1.02] border border-border"
            >
              <div className="aspect-[4/3] w-full bg-surface-quiet relative overflow-hidden">
                {doc.cover_url ? (
                  <img
                    src={doc.cover_url.startsWith("http") ? doc.cover_url : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/tai-len/luu-tru/${doc.cover_url}`}
                    alt={doc.title || "Tác phẩm chưa có tiêu đề"}
                    className="w-full h-full object-cover opacity-60"
                  />
                ) : (
                  <div className="w-full h-full bg-surface-quiet flex items-center justify-center">
                    <FileText className="w-12 h-12 text-border" />
                  </div>
                )}
              </div>

              <div className="p-5 flex flex-col gap-2">
                <h3 className="text-[17px] font-medium text-ink line-clamp-2 leading-snug">
                  {doc.title || "Tác phẩm chưa có tiêu đề"}
                </h3>
                <p className="text-[13px] text-danger">
                  Đã xóa {new Date(doc.updated_at).toLocaleString("vi-VN")}
                </p>
              </div>

              <button
                onClick={() => handleRestoreDocument(doc._id || doc.id)}
                title="Khôi phục"
                className="absolute top-2 right-2 p-2 bg-white rounded-full text-ink-muted hover:text-brand opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-sm border border-border"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
