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
  BookOpen,
  Award,
} from "lucide-react";
import { getMyDocumentsAPI } from "@/features/content/services/document_metadata.service";
import { getAuthorRevenueAPI as getRevenueAPI } from "@/features/finance/services/content_monetization.service";
import { useToast } from "@/shared/contexts/ToastContext";

export default function AuthorAnalyticsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [docData, revData] = await Promise.all([
        getMyDocumentsAPI(),
        getRevenueAPI(),
      ]);

      setDocuments(docData.data || docData || []);
      setRevenue(revData.data || revData);
    } catch (err: any) {
      showToast("Lỗi tải dữ liệu phân tích", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <div className="mb-6 md:mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
            Phân tích dữ liệu
          </h1>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
            AI-Driven Insights & Global Metrics <Award className="w-3.5 h-3.5 text-zinc-400" />
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        {[
          {
            label: "Lượt xem tổng",
            val: revenue?.total_views || 0,
            icon: Eye,
            color: "text-zinc-900",
          },
          {
            label: "Lượt đánh giá",
            val: 0,
            icon: Star,
            color: "text-zinc-900",
          },
          {
            label: "Doanh thu (dl)",
            val: revenue?.total_revenue || 0,
            icon: TrendingUp,
            color: "text-green-600",
          },
          {
            label: "Tổng tác phẩm",
            val: documents.length,
            icon: BookOpen,
            color: "text-zinc-900",
          },
        ].map((item, i) => (
          <div key={i} className="p-6 md:p-8 border border-zinc-100 bg-white/90 backdrop-blur-md rounded-3xl shadow-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-md group">
            <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-2xl mb-6 shadow-sm group-hover:bg-white transition-colors">
              <item.icon className={`w-5 h-5 ${item.color}`} />
            </div>
            <h3 className="text-4xl md:text-5xl font-bold text-zinc-900 tracking-tight mb-2">
              {typeof item.val === "number" && item.val > 1000
                ? `${(item.val / 1000).toFixed(1)}K`
                : item.val}
            </h3>
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
              {item.label}
            </p>
          </div>
        ))}
      </div>
      
      <div className="mt-8 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "150ms" }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
          <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
            <BarChart3 className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight mb-2">
            Đang phân tích dữ liệu chuyên sâu
          </h3>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
            Hệ thống AI đang thu thập và tính toán các chỉ số về tương tác và tăng trưởng của tác phẩm. Vui lòng quay lại sau.
          </p>
        </div>
      </div>
    </div>
  );
}
