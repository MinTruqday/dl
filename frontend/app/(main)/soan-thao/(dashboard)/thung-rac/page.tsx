"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    fetchTrash();
  }, []);

  const fetchTrash = async () => {
    setLoading(true);
    try {
      const data = await getTrashAPI();
      setTrash(data.data || data || []);
    } catch {
      showToast("Không thể tải danh sách thùng rác", "error");
    } finally {
      setLoading(false);
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
    <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-6 font-sans text-[#1D1D1F]">
      <div className="flex items-center justify-between">
        <h2 className="text-[20px] font-semibold text-[#1D1D1F]">
          Thùng rác
        </h2>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex flex-col bg-white rounded-[18px] overflow-hidden animate-pulse border border-[#E8E8ED]">
              <div className="bg-[#D2D2D7] aspect-[4/3] w-full" />
              <div className="p-5 space-y-3">
                <div className="h-3 w-1/3 bg-[#D2D2D7] rounded-full" />
                <div className="h-4 w-full bg-[#D2D2D7] rounded-full" />
                <div className="h-4 w-2/3 bg-[#D2D2D7] rounded-full" />
              </div>
            </div>
          ))}
        </div>
      ) : !Array.isArray(trash) || trash.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center w-full text-center">
          <p className="text-[17px] text-[#6E6E73]">Chưa có dữ liệu</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {trash.map((doc: any, idx: number) => (
            <div
              key={doc._id || doc.id || idx}
              className="group relative flex flex-col bg-white rounded-[18px] overflow-hidden transition-transform hover:scale-[1.02] border border-[#E8E8ED]"
            >
              <div className="aspect-[4/3] w-full bg-[#F5F5F7] relative overflow-hidden">
                {doc.cover_url ? (
                  <img
                    src={doc.cover_url.startsWith("http") ? doc.cover_url : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/storage/${doc.cover_url}`}
                    alt={doc.title || "Tác phẩm chưa có tiêu đề"}
                    className="w-full h-full object-cover opacity-60"
                  />
                ) : (
                  <div className="w-full h-full bg-[#F5F5F7] flex items-center justify-center">
                    <FileText className="w-12 h-12 text-[#E8E8ED]" />
                  </div>
                )}
              </div>

              <div className="p-5 flex flex-col gap-2">
                <h3 className="text-[17px] font-medium text-[#1D1D1F] line-clamp-2 leading-snug">
                  {doc.title || "Tác phẩm chưa có tiêu đề"}
                </h3>
                <p className="text-[13px] text-[#FF3B30]">
                  Đã xóa {new Date(doc.updated_at).toLocaleString("vi-VN")}
                </p>
              </div>

              <button
                onClick={() => handleRestoreDocument(doc._id || doc.id)}
                title="Khôi phục"
                className="absolute top-2 right-2 p-2 bg-white rounded-full text-[#6E6E73] hover:text-[#34C759] opacity-0 group-hover:opacity-100 transition-opacity z-10 shadow-sm border border-[#E8E8ED]"
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
