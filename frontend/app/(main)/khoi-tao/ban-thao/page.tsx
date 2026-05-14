"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMyDocumentsAPI } from "@/services/document.service";
import { Loader2, FolderOpen, FileText, ArrowRight } from "lucide-react";
import { useToast } from "@/contexts/ToastContext";

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
        <div className="py-24 flex justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        </div>
      ) : drafts.length === 0 ? (
        <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
          <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {drafts.map((draft: any) => (
            <button
              key={draft._id || draft.id}
              onClick={() => router.push(`/sang-tac?tai-lieu=${draft._id || draft.id}`)}
              className="group flex items-center justify-between p-4 border border-zinc-200 bg-white text-left rounded-none hover:border-black transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 border border-zinc-200 bg-zinc-50 flex items-center justify-center shrink-0 rounded-none">
                  <FileText className="w-4 h-4 text-zinc-400" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-semibold text-sm text-black truncate max-w-sm">{draft.title}</h4>
                  <p className="text-xs font-medium text-zinc-500">Lần cuối: {new Date(draft.updated_at || draft.created_at).toLocaleDateString("vi-VN")}</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-zinc-400 group-hover:text-black transition-colors" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
