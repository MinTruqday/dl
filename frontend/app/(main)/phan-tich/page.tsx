"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Brain,
  Sparkles,
  Loader2,
  Eye,
  Star,
  TrendingUp,
  BarChart3,
  Award,
  BookOpen,
} from "lucide-react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import { useToast } from "@/shared/contexts/ToastContext";

export default function AuthorAnalyticsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const docData = await getMyDocumentsAPI();
      setDocuments(docData.data || docData || []);
      setRevenue(null);
    } catch (err: any) {
      showToast("Không thể tải bộ sưu tập phân tích", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-ink-muted" />
      </div>
    );
  }

  return (
    <div className="w-full h-full font-sans text-ink flex flex-col gap-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          {
            label: "Lượt xem",
            val: revenue?.total_views || 0,
            icon: Eye,
            color: "text-brand",
            bg: "bg-brand/10",
          },
          {
            label: "Lượt đánh giá",
            val: 0,
            icon: Star,
            color: "text-warning",
            bg: "bg-warning/10",
          },
          {
            label: "Doanh thu (dl)",
            val: revenue?.total_revenue || 0,
            icon: TrendingUp,
            color: "text-brand",
            bg: "bg-brand/10",
          },
          {
            label: "Tác phẩm",
            val: documents.length,
            icon: BookOpen,
            color: "text-brand",
            bg: "bg-brand/10",
          },
        ].map((item, i) => (
          <div
            key={i}
            className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none border-border p-6 md:px-0 md:pt-6 flex flex-col gap-4"
          >
            <div
              className={`w-12 h-12 rounded-control flex items-center justify-center ${item.bg}`}
            >
              <item.icon className={`w-6 h-6 ${item.color}`} />
            </div>
            <div>
              <p className="text-[13px] font-medium text-ink-muted mb-4 tracking-tight leading-none mb-1">
                {typeof item.val === "number" && item.val > 1000
                  ? `${(item.val / 1000).toFixed(1)}K`
                  : item.val}
              </p>
              <p className="text-[14px] text-ink-muted font-medium">
                {item.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="flex-1 bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none border-border p-8 md:px-0 md:pt-8 flex flex-col items-center justify-center min-h-[300px] text-center">
        <div className="w-20 h-20 bg-surface-quiet flex items-center justify-center rounded-workspace mb-4">
          <BarChart3 className="w-10 h-10 text-ink-faint" />
        </div>
        <p className="text-[13px] font-medium text-ink-muted mb-2">
          Đang phân tích dữ liệu chuyên sâu
        </p>
        <p className="text-[15px] text-ink-muted max-w-md">
          Hệ thống AI đang thu thập và tính toán các chỉ số về tương tác và tăng
          trưởng của tác phẩm. Vui lòng quay lại sau.
        </p>
      </div>
    </div>
  );
}
