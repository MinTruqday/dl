"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import { Loader2, FolderOpen, FileText, ArrowRight } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";

export default function DraftsPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
    }
  };

  return (
    <div className="space-y-6">
      {loading ? (
        <div className="py-24 flex justify-center border border-zinc-200 bg-white rounded-2xl">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : drafts.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-2xl">
          <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
        </div>
      ) : (
        <div
          className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 animate-in fade-in slide-in-from-bottom-8 duration-300"
          style={{ animationDelay: "150ms", animationFillMode: "both" }}
        >
          {drafts.map((draft: any) => (
            <button
              key={draft._id || draft.id}
              onClick={() =>
                router.push(`/compose?tai-lieu=${draft._id || draft.id}`)
              }
              className="group flex flex-col border border-zinc-200 bg-white rounded-2xl hover:border-black transition-colors overflow-hidden text-left"
            >
              <div className="aspect-[2/3] w-full border-b border-zinc-200 bg-zinc-100 relative overflow-hidden">
                {draft.cover_url ? (
                  <img
                    src={draft.cover_url}
                    alt={draft.title}
                    className="w-full h-full object-cover grayscale mix-blend-multiply group-hover:scale-105 transition-transform duration-500"
                  />
                ) : (
                  <div className="w-full h-full bg-zinc-100 flex items-center justify-center">
                    <FileText className="w-8 h-8 text-zinc-300" />
                  </div>
                )}
              </div>

              <div className="p-3 flex flex-col flex-1 gap-2 w-full">
                <div className="flex flex-wrap gap-1.5">
                  <span className="px-1.5 py-0.5 text-[10px] font-medium text-zinc-600 bg-zinc-100 rounded-md">
                    Bản nháp
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-black line-clamp-2 leading-snug">
                  {draft.title}
                </h3>

                <div className="text-xs text-zinc-500 flex items-center gap-1.5 mt-auto pt-3 border-t border-zinc-100">
                  <span className="truncate text-black font-medium">
                    Cập nhật
                  </span>
                  <span>•</span>
                  <span className="shrink-0">
                    {new Date(
                      draft.updated_at || draft.created_at,
                    ).toLocaleDateString("vi-VN")}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
