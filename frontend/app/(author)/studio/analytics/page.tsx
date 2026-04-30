"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "@/app/lib/api";
import { 
  Brain, 
  Sparkles, 
  Loader2, 
  Eye, 
  Star,
  TrendingUp,
  BarChart3,
  BookOpen,
  Award
} from "lucide-react";
import { formatError } from "@/app/lib/api";
import { Notification } from "@/app/components/NotificationToast";

export default function AuthorAnalyticsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [revenue, setRevenue] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const fetchData = useCallback(async () => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    try {
      const [docRes, revRes] = await Promise.all([
        fetch(`${API_URL}/author/documents`, { headers }),
        fetch(`${API_URL}/author/revenue`, { headers }),
      ]);
      
      if (docRes.ok) {
        const json = await docRes.json();
        setDocuments(json.data || json || []);
      }
      
      if (revRes.ok) {
        const json = await revRes.json();
        setRevenue(json.data || json);
      }
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu phân tích:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [API_URL]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const analyzeSentiment = async () => {
    if (!selectedDocumentId) return;
    setProcessing(true);
    setSentiment(null);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/sentiment`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        setSentiment(await res.json());
        setNotification({ type: "success", text: "Đã hoàn thành phân tích cảm xúc AI." });
      } else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Không thể phân tích lúc này." });
      }
    } catch (e) {
      setNotification({ type: "error", text: "Lỗi kết nối máy chủ phân tích." });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Header */}
      <div 
        className="mb-16 border-b border-zinc-100 pb-12 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="space-y-4">
          <h1 className="text-6xl font-bold tracking-tighter leading-none text-black">
            Phân tích dữ liệu
          </h1>
          <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-3">
            AI-Driven Insights & Global Metrics <Award className="w-4 h-4 text-zinc-100" />
          </p>
        </div>
      </div>

      {/* Global Stats Grid */}
      <div 
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20 transition-all duration-700 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        {[
          { label: "Lượt xem tổng", val: revenue?.total_views || 0, icon: Eye, color: "text-zinc-100" },
          { label: "Đánh giá TB", val: revenue?.avg_rating || 0, icon: Star, color: "text-zinc-100" },
          { label: "Doanh thu (dl)", val: revenue?.total_revenue || 0, icon: TrendingUp, color: "text-black" },
          { label: "Tổng tác phẩm", val: documents.length, icon: BookOpen, color: "text-zinc-100" },
        ].map((item, i) => (
          <div
            key={i}
            className="p-10 border border-zinc-100 bg-white hover:border-black transition-all duration-500 group"
          >
            <item.icon className={`w-5 h-5 mb-8 group-hover:text-black transition-colors ${item.color}`} />
            <h3 className="text-4xl font-bold text-black tracking-tighter mb-2">
               {typeof item.val === 'number' && item.val > 1000 ? `${(item.val / 1000).toFixed(1)}K` : item.val}
            </h3>
            <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{item.label}</p>
          </div>
        ))}
      </div>

      <div 
        className="grid lg:grid-cols-12 gap-16 transition-all duration-700 delay-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        {/* Left Column - Configuration */}
        <div className="lg:col-span-5 space-y-12">
           <div className="border border-zinc-100 p-10 bg-white space-y-10">
              <div className="space-y-6">
                <div className="flex items-center gap-4 mb-2">
                   <div className="w-8 h-8 bg-black flex items-center justify-center">
                      <Brain className="w-4 h-4 text-white" />
                   </div>
                   <h3 className="text-sm font-bold uppercase tracking-widest">Phân tích cảm xúc AI</h3>
                </div>
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Lựa chọn tác phẩm</label>
                  <select
                    value={selectedDocumentId}
                    onChange={(e) => setSelectedDocumentId(e.target.value)}
                    className="w-full h-16 px-6 border border-zinc-100 bg-zinc-50/30 text-sm font-bold focus:outline-none focus:border-black transition-all appearance-none cursor-pointer rounded-none"
                  >
                    <option value="">Chọn một tài liệu để bắt đầu</option>
                    {documents.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.title}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={analyzeSentiment}
                  disabled={processing || !selectedDocumentId}
                  className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 disabled:opacity-50 transition-all flex items-center justify-center gap-4 active:scale-[0.98] shadow-xl shadow-black/5"
                >
                  {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                  Khởi tạo phân tích AI
                </button>
              </div>
              <div className="pt-6 border-t border-zinc-50">
                 <p className="text-[10px] text-zinc-300 font-medium leading-relaxed italic uppercase tracking-wider">
                   Hệ thống sẽ tổng hợp hàng nghìn đánh giá và bình luận để đưa ra cái nhìn tổng quan nhất về cảm xúc của độc giả đối với tác phẩm này.
                 </p>
              </div>
           </div>
        </div>

        {/* Right Column - Results */}
        <div className="lg:col-span-7">
           {sentiment ? (
              <div className="space-y-8 animate-in fade-in slide-in-from-right-8 duration-700">
                 <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[
                      { label: "Cảm xúc chung", val: sentiment.sentiment, color: "text-black" },
                      { label: "Tích cực", val: `${sentiment.positive_pct}%`, color: "text-zinc-400" },
                      { label: "Tiêu cực", val: `${sentiment.negative_pct}%`, color: "text-zinc-200" },
                      { label: "Tổng phản hồi", val: sentiment.total_reviews || 0, color: "text-black" },
                    ].map((s, i) => (
                      <div key={i} className="p-8 border border-zinc-100 bg-white">
                        <h4 className={`text-2xl font-bold tracking-tighter capitalize ${s.color}`}>{s.val}</h4>
                        <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest mt-2">{s.label}</p>
                      </div>
                    ))}
                 </div>

                 <div className="border border-zinc-100 p-12 bg-white relative">
                    <div className="absolute top-0 right-0 p-8 opacity-[0.03]">
                       <Brain className="w-32 h-32" />
                    </div>
                    <h3 className="text-[10px] font-bold text-black uppercase tracking-[0.2em] mb-10">Tóm tắt trí tuệ nhân tạo</h3>
                    <p className="text-xl text-zinc-600 leading-relaxed font-medium italic relative z-10">
                      "{sentiment.summary}"
                    </p>
                 </div>
              </div>
           ) : (
              <div className="h-full flex flex-col items-center justify-center py-32 border border-dashed border-zinc-100 bg-zinc-50/10 opacity-30">
                 <BarChart3 className="w-16 h-16 text-zinc-100 mb-8" />
                 <p className="text-[11px] font-bold uppercase tracking-widest">Dữ liệu phân tích chi tiết sẽ hiển thị tại đây</p>
              </div>
           )}
        </div>
      </div>
    </div>
  );
}
