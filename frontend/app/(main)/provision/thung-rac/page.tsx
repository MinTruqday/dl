"use client";

import { useEffect, useState } from "react";
import {
  getTrashAPI,
  restoreDocumentAPI,
} from "@/features/content/services/document_metadata.service";
import { useToast } from "@/shared/contexts/Toast";
import { Loader2, Trash2, X, FileText, RotateCcw } from "lucide-react";

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
    } catch (err: any) {
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
    <div className="space-y-8">
      <div
        className="bg-white border border-zinc-200 p-8 rounded-2xl shadow-sm flex items-center justify-between animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        <div className="space-y-1">
          <h2 className="text-xl font-medium text-black">Thùng rác nội dung</h2>
          <p className="text-sm font-medium text-zinc-500">
            Tài liệu đã tạm thời bị gỡ bỏ
          </p>
        </div>
        <Trash2 className="w-6 h-6 text-zinc-400" />
      </div>

      <div
        className="space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        {loading ? (
          <div className="py-12 flex justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
          </div>
        ) : !Array.isArray(trash) || trash.length === 0 ? (
          <div className="bg-zinc-50 border border-zinc-200 p-16 text-center rounded-2xl shadow-sm flex flex-col items-center justify-center gap-3">
            <X className="w-6 h-6 text-zinc-400" />
            <p className="text-sm font-medium text-zinc-500">Thùng rác trống</p>
          </div>
        ) : (
          trash.map((doc: any) => (
            <div
              key={doc._id}
              className="bg-white border border-zinc-200 p-6 flex items-center justify-between rounded-2xl shadow-sm"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-zinc-50 flex items-center justify-center rounded-xl border border-zinc-200">
                  <FileText className="w-4 h-4 text-zinc-500" />
                </div>
                <div className="space-y-1">
                  <p className="text-base font-medium text-black">
                    {doc.title}
                  </p>
                  <p className="text-sm font-medium text-zinc-500">
                    Ngày xóa:{" "}
                    {new Date(doc.updated_at).toLocaleDateString("vi-VN")}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleRestoreDocument(doc._id || doc.id)}
                className="h-9 px-4 border border-zinc-200 text-sm font-medium text-black rounded-xl flex items-center gap-2 hover:bg-zinc-50 transition-colors"
              >
                <RotateCcw className="w-4 h-4" /> Khôi phục
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
