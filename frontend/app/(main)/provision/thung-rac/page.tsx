"use client";

import { useEffect, useState } from "react";
import {
  getTrashAPI,
  restoreDocumentAPI,
} from "@/features/content/services/document_metadata.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Trash2, X, FileText, RotateCcw } from "lucide-react";

export default function TrashPage() {
  const { showToast } = useToast();
  const [trash, setTrash] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    fetchTrash();
  }, []);

  const fetchTrash = async () => {
    setLoading(true);
    try {
      const data = await getTrashAPI();
      setTrash(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách thùng rác", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  };

  const handleRestoreDocument = async (docId: string) => {
    try {
      await restoreDocumentAPI(docId);
      showToast("Đã khôi phục tài liệu thành công", "success");
      fetchTrash();
    } catch (e: any) {
      showToast(e.message || "Lỗi khôi phục tài liệu", "error");
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              Thùng rác
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Quản lý các tài liệu đã bị gỡ bỏ tạm thời
            </p>
          </div>
          <div className="w-10 h-10 bg-red-50 border border-red-100 rounded-2xl flex items-center justify-center shrink-0">
            <Trash2 className="w-5 h-5 text-red-500" />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải dữ liệu...</p>
          </div>
        ) : !Array.isArray(trash) || trash.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl p-12 text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
              <Trash2 className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-2">Thùng rác trống</h3>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
              Không có tài liệu nào bị xóa gần đây. Các tài liệu trong thùng rác có thể được khôi phục.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 pb-6">
            {trash.map((doc: any) => (
              <div
                key={doc._id}
                className="bg-white/90 backdrop-blur-md border border-zinc-100 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-3xl shadow-sm hover:shadow-md transition-all duration-300 group hover:-translate-y-0.5"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-zinc-50 flex items-center justify-center rounded-2xl border border-zinc-100 shrink-0 group-hover:bg-white group-hover:shadow-sm transition-all">
                    <FileText className="w-5 h-5 text-zinc-400" />
                  </div>
                  <div className="space-y-1.5">
                    <h4 className="text-sm font-bold text-zinc-900 line-clamp-1">
                      {doc.title || "Tác phẩm chưa có tiêu đề"}
                    </h4>
                    <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
                      <span>Ngày xóa:</span>
                      <span className="text-zinc-900">
                        {new Date(doc.updated_at).toLocaleString("vi-VN")}
                      </span>
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleRestoreDocument(doc._id || doc.id)}
                  className="w-full sm:w-auto h-11 px-6 bg-white border border-zinc-200 text-[10px] font-bold uppercase tracking-widest text-zinc-700 rounded-2xl flex items-center justify-center gap-2 hover:bg-black hover:text-white hover:border-black transition-all shadow-sm sm:opacity-0 sm:group-hover:opacity-100"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Khôi phục
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
