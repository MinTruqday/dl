"use client";

import { useEffect, useState } from "react";
import { getTrashAPI, restoreDocumentAPI } from "@/features/content/services/document_metadata.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Trash2, FileText, RotateCcw } from "lucide-react";

export default function TrashPage() {
  const { showToast } = useToast();
  const [trash, setTrash] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  useEffect(() => { fetchTrash(); }, []);

  const fetchTrash = async () => {
    setLoading(true);
    try {
      const data = await getTrashAPI();
      setTrash(data.data || data || []);
    } catch { showToast("Không thể tải danh sách thùng rác", "error"); } finally { setLoading(false); requestAnimationFrame(() => setVisible(true)); }
  };

  const handleRestoreDocument = async (docId: string) => {
    try {
      await restoreDocumentAPI(docId);
      showToast("Đã khôi phục tài liệu thành công", "success"); fetchTrash();
    } catch (e: any) { showToast(e.message || "Lỗi khôi phục tài liệu", "error"); }
  };

  return (
    <div className="flex flex-col h-full font-sans">
      <div className={`flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] border border-[#E8E8ED] rounded-[24px]">
            <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
            <p className="text-[13px] font-medium text-[#6E6E73]">Đang tải dữ liệu...</p>
          </div>
        ) : !Array.isArray(trash) || trash.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#F5F5F7] border border-[#E8E8ED] rounded-[24px] p-12 text-center">
            <div className="w-16 h-16 bg-[#F5F5F7] border-[#E8E8ED] flex items-center justify-center rounded-[18px] mb-4">
              <Trash2 className="w-8 h-8 text-[#C7C7CC]" />
            </div>
            <h3 className="text-[17px] font-medium text-[#1D1D1F] mb-2">Thùng rác trống</h3>
            <p className="text-[15px] text-[#6E6E73] max-w-sm">Không có tài liệu nào bị xóa gần đây. Các tài liệu trong thùng rác có thể được khôi phục.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 pb-6">
            {trash.map((doc: any) => (
              <div key={doc._id} className="bg-[#F5F5F7] border-[#E8E8ED] p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-[24px] hover: transition-all duration-300 group hover:-translate-y-0.5">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-[#F5F5F7] flex items-center justify-center rounded-[14px] border border-[#E8E8ED] shrink-0 group-hover:bg-white group-hover:border-[#0071E3] transition-all">
                    <FileText className="w-6 h-6 text-[#6E6E73] group-hover:text-[#0071E3] transition-colors" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-[15px] font-semibold text-[#1D1D1F] line-clamp-1">{doc.title || "Tác phẩm chưa có tiêu đề"}</h4>
                    <p className="text-[13px] text-[#6E6E73] flex items-center gap-1.5">
                      <span>Ngày xóa:</span><span className="font-medium text-[#1D1D1F]">{new Date(doc.updated_at).toLocaleString("vi-VN")}</span>
                    </p>
                  </div>
                </div>
                <button onClick={() => handleRestoreDocument(doc._id || doc.id)} className="w-full sm:w-auto h-[44px] px-6 bg-white border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] rounded-full flex items-center justify-center gap-2 hover:bg-[#F5F5F7] hover:text-[#0071E3] transition-colors sm:opacity-0 sm:group-hover:opacity-100">
                  <RotateCcw className="w-4 h-4" /> Khôi phục
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
