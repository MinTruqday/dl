"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  Loader2,
  FileText,
  Calendar,
  PenTool,
  ArrowRight,
  FolderOpen,
} from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";

export default function DraftsPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [drafts, setDrafts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDrafts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getMyDocumentsAPI();
      const list = data.data || data || [];
      setDrafts(list.filter((d: any) => d.status === "draft"));
    } catch {
      showToast("Không thể tải danh sách bản thảo", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchDrafts();
  }, [fetchDrafts]);

  return (
    <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6 font-sans text-ink">
      <div className="flex items-center justify-between">
        <h2 className="text-[20px] font-semibold text-ink">
          Bản nháp
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
      ) : drafts.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {drafts.map((draft: any, idx: number) => (
            <div
              key={draft._id || draft.id || idx}
              onClick={() => router.push(`/soan-thao?tai-lieu=${draft._id || draft.id}`)}
              className="group relative flex flex-col bg-white rounded-panel overflow-hidden transition-transform hover:scale-[1.02] cursor-pointer border border-border"
            >
              <div className="aspect-[4/3] w-full bg-surface-quiet relative overflow-hidden">
                {draft.cover_url ? (
                  <img
                    src={draft.cover_url.startsWith("http") ? draft.cover_url : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/tai-len/luu-tru/${draft.cover_url}`}
                    alt={draft.title || "Tác phẩm chưa có tiêu đề"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-surface-quiet" />
                )}
              </div>

              <div className="p-5 flex flex-col gap-2">
                <h3 className="text-[17px] font-medium text-ink line-clamp-2 leading-snug">
                  {draft.title || "Tác phẩm chưa có tiêu đề"}
                </h3>
                <p className="text-[13px] text-ink-muted">
                  Cập nhật {new Date(draft.updated_at || draft.created_at).toLocaleDateString("vi-VN")}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center w-full text-center">
          <p className="text-[17px] text-ink-muted">Chưa có dữ liệu</p>
        </div>
      )}
    </div>
  );
}
