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
import PageHeader from "@/shared/components/common/PageHeader";

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
      showToast("Lỗi trích xuất danh sách bản thảo", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchDrafts();
  }, [fetchDrafts]);

  return (
    <div className="app-page gap-6">
      <PageHeader title="Bản nháp" />
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="flex flex-col bg-white rounded-[var(--radius-panel)] overflow-hidden animate-pulse border border-[var(--border)]">
              <div className="bg-[var(--border-strong)] aspect-[4/3] w-full" />
              <div className="p-5 space-y-3">
                <div className="h-3 w-1/3 bg-[var(--border-strong)] rounded-full" />
                <div className="h-4 w-full bg-[var(--border-strong)] rounded-full" />
                <div className="h-4 w-2/3 bg-[var(--border-strong)] rounded-full" />
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
              className="group relative flex flex-col bg-white rounded-[var(--radius-panel)] overflow-hidden transition-transform hover:scale-[1.02] cursor-pointer border border-[var(--border)]"
            >
              <div className="aspect-[4/3] w-full bg-[var(--surface-quiet)] relative overflow-hidden">
                {draft.cover_url ? (
                  <img
                    src={draft.cover_url.startsWith("http") ? draft.cover_url : `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/storage/${draft.cover_url}`}
                    alt={draft.title || "Tác phẩm chưa có tiêu đề"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-[var(--surface-quiet)]" />
                )}
              </div>

              <div className="p-5 flex flex-col gap-2">
                <h3 className="text-[17px] font-medium text-[var(--ink)] line-clamp-2 leading-snug">
                  {draft.title || "Tác phẩm chưa có tiêu đề"}
                </h3>
                <p className="text-[13px] text-[var(--ink-muted)]">
                  Cập nhật {new Date(draft.updated_at || draft.created_at).toLocaleDateString("vi-VN")}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 flex flex-col items-center justify-center w-full text-center">
          <p className="text-[17px] text-[var(--ink-muted)]">Chưa có dữ liệu</p>
        </div>
      )}
    </div>
  );
}
