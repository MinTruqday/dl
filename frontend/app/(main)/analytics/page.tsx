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
import { useToast } from "@/shared/contexts/Toast";

export default function AuthorAnalyticsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
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
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-16 border-b border-zinc-100 pb-12 animate-in fade-in slide-in-from-bottom-8 duration-300">
        <div className="space-y-4">
          <h1 className="text-6xl font-bold tracking-tighter leading-none text-black">
            Phân tích dữ liệu
          </h1>
          <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-3">
            AI-Driven Insights & Global Metrics{" "}
            <Award className="w-4 h-4 text-zinc-100" />
          </p>
        </div>
      </div>

      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        {[
          {
            label: "Lượt xem tổng",
            val: revenue?.total_views || 0,
            icon: Eye,
            color: "text-zinc-100",
          },
          {
            label: "Đánh giá TB",
            val: revenue?.avg_rating || 0,
            icon: Star,
            color: "text-zinc-100",
          },
          {
            label: "Doanh thu (dl)",
            val: revenue?.total_revenue || 0,
            icon: TrendingUp,
            color: "text-black",
          },
          {
            label: "Tổng tác phẩm",
            val: documents.length,
            icon: BookOpen,
            color: "text-zinc-100",
          },
        ].map((item, i) => (
          <div key={i} className="p-10 border border-zinc-100 bg-white group">
            <item.icon className={`w-5 h-5 mb-8 ${item.color}`} />
            <h3 className="text-4xl font-bold text-black tracking-tighter mb-2">
              {typeof item.val === "number" && item.val > 1000
                ? `${(item.val / 1000).toFixed(1)}K`
                : item.val}
            </h3>
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
              {item.label}
            </p>
          </div>
        ))}
      </div>

    </div>
  );
}
