"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import { Loader2, FileText, Calendar, PenTool, ArrowRight, FolderOpen } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";

export default function DraftsPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    fetchDrafts();
  }, []);

  const fetchDrafts = async () => {
    setLoading(true);
    try {
      const data = await getMyDocumentsAPI();
      const list = data.data || data || [];
      setDrafts(list.filter((d: any) => d.status === "draft"));
    } catch (err) {
      showToast("Không thể tải danh sách bản nháp", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
          Kho lưu trữ nháp
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Quản lý các tác phẩm đang trong quá trình sáng tác
        </p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        {loading ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl">
            <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang đồng bộ dữ liệu...</p>
          </div>
        ) : drafts.length === 0 ? (
          <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-zinc-50/50 border border-zinc-100 rounded-3xl p-12 text-center">
            <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
              <FolderOpen className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-2">Chưa có bản nháp nào</h3>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm mb-6">
              Bạn chưa có tác phẩm nào đang trong quá trình soạn thảo. Bắt đầu sáng tác ngay.
            </p>
            <button
              onClick={() => router.push("/provision")}
              className="h-10 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md flex items-center gap-2"
            >
              <PenTool className="w-3.5 h-3.5" />
              Tạo tác phẩm mới
            </button>
          </div>
        ) : (
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 pb-6">
            {drafts.map((draft: any) => (
              <button
                key={draft._id || draft.id}
                onClick={() =>
                  router.push(`/compose?tai-lieu=${draft._id || draft.id}`)
                }
                className="group flex flex-col bg-white border border-zinc-100 rounded-3xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden text-left hover:-translate-y-1"
              >
                <div className="aspect-[3/4] w-full border-b border-zinc-100 bg-zinc-50 relative overflow-hidden flex items-center justify-center">
                  {draft.cover_url ? (
                    <img
                      src={draft.cover_url}
                      alt={draft.title}
                      className="w-full h-full object-cover grayscale mix-blend-multiply transition-transform duration-700 group-hover:scale-105"
                    />
                  ) : (
                    <div className="w-full h-full bg-zinc-50 flex items-center justify-center transition-transform duration-700 group-hover:scale-105">
                      <FileText className="w-12 h-12 text-zinc-200 stroke-[1.5]" />
                    </div>
                  )}
                  <div className="absolute top-3 left-3 px-2.5 py-1 bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-lg shadow-sm">
                    <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-600 flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"></div>
                      Bản nháp
                    </span>
                  </div>
                  
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-300 flex items-center justify-center">
                    <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-lg opacity-0 translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 delay-100 text-black">
                      <ArrowRight className="w-5 h-5" />
                    </div>
                  </div>
                </div>

                <div className="p-5 flex flex-col flex-1 gap-4 w-full bg-white">
                  <h3 className="text-sm font-bold text-zinc-900 line-clamp-2 leading-relaxed group-hover:text-black">
                    {draft.title || "Tác phẩm chưa có tiêu đề"}
                  </h3>

                  <div className="mt-auto pt-4 border-t border-zinc-100 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-zinc-400">
                      <Calendar className="w-3.5 h-3.5" />
                      <span className="text-[9px] font-bold uppercase tracking-widest">
                        {new Date(
                          draft.updated_at || draft.created_at,
                        ).toLocaleDateString("vi-VN")}
                      </span>
                    </div>
                    <div className="w-6 h-6 rounded-full bg-zinc-50 flex items-center justify-center group-hover:bg-black transition-colors">
                      <PenTool className="w-3 h-3 text-zinc-400 group-hover:text-white transition-colors" />
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
