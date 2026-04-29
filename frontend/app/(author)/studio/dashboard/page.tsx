"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken } from "@/app/lib/api";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  Ticket,
  Layers,
  ChevronRight,
  Eye,
  Star,
  Brain,
  CheckCircle,
  Image as ImageIcon,
  FolderOpen,
  Loader2,
  Trash2,
  BookOpen,
  Filter,
  Sparkles,
  Award,
} from "lucide-react";
import { formatError } from "@/app/lib/api";
import { Notification } from "@/app/components/NotificationToast";

type TabKey = "overview" | "coupons" | "series" | "sentiment" | "grammar" | "cover" | "assets";

export default function AuthorDashboardPage() {
  const [revenue, setRevenue] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [coupons, setCoupons] = useState<any[]>([]);
  const [series, setSeries] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  const [sentiment, setSentiment] = useState<any>(null);
  const [grammarResult, setGrammarResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [selectedChapterId, setSelectedChapterId] = useState("");
  const [processing, setProcessing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  const fetchAll = useCallback(async () => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    try {
      const [revenueR, documentsR, couponsR, seriesR, assetsR] = await Promise.all([
        fetch(`${API_URL}/author/revenue`, { headers }),
        fetch(`${API_URL}/author/documents`, { headers }),
        fetch(`${API_URL}/author/coupons`, { headers }),
        fetch(`${API_URL}/author/series`, { headers }),
        fetch(`${API_URL}/author/assets`, { headers }),
      ]);
      if (revenueR.ok) setRevenue(await revenueR.json());
      if (documentsR.ok) setDocuments(await documentsR.json());
      if (couponsR.ok) setCoupons(await couponsR.json());
      if (seriesR.ok) setSeries(await seriesR.json());
      if (assetsR.ok) setAssets(await assetsR.json());
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu tổng quan:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [API_URL]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const analyzeSentiment = async () => {
    if (!selectedDocumentId) return;
    setProcessing(true);
    setSentiment(null);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/sentiment`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) setSentiment(await res.json());
      else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Không thể phân tích cảm xúc độc giả lúc này." });
      }
    } catch (e) {
      setNotification({ type: "error", text: "Lỗi kết nối máy chủ phân tích." });
    }
    setProcessing(false);
  };

  const checkGrammar = async () => {
    if (!selectedDocumentId || !selectedChapterId) return;
    setProcessing(true);
    setGrammarResult(null);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/grammar/${selectedChapterId}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) setGrammarResult(await res.json());
      else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Không thể kiểm tra ngữ pháp lúc này." });
      }
    } catch (e) {
      setNotification({ type: "error", text: "Lỗi kết nối máy chủ kiểm duyệt." });
    }
    setProcessing(false);
  };

  const generateCover = async () => {
    if (!selectedDocumentId) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/generate-cover`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ style: "minimalist" }),
      });
      if (res.ok) {
        const data = await res.json();
        setNotification({ type: "success", text: data.message || "Đã khởi tạo quá trình tạo ảnh bìa AI." });
      } else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Tạo ảnh bìa thất bại." });
      }
    } catch (e) {
      setNotification({ type: "error", text: "Lỗi kết nối máy chủ AI Cover." });
    }
    setProcessing(false);
  };

  const deleteAsset = async (assetId: string) => {
    try {
      const res = await fetch(`${API_URL}/author/assets/${assetId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã xóa tài nguyên vĩnh viễn." });
        fetchAll();
      }
    } catch (e) {
      setNotification({ type: "error", text: "Xóa tài nguyên thất bại." });
    }
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  const tabs: { key: TabKey; label: string; icon: any }[] = [
    { key: "overview", label: "Tổng quan", icon: BarChart3 },
    { key: "coupons", label: "Mã giảm giá", icon: Ticket },
    { key: "series", label: "Bộ sưu tập", icon: Layers },
    { key: "sentiment", label: "Cảm xúc AI", icon: Brain },
    { key: "grammar", label: "Ngữ pháp AI", icon: CheckCircle },
    { key: "cover", label: "Ảnh bìa AI", icon: ImageIcon },
    { key: "assets", label: "Kho tài nguyên", icon: FolderOpen },
  ];

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Header - Premium Standard */}
      <div 
        className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Quản trị nội dung
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Author Dashboard <Award className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          
          <Link 
            href="/studio/create"
            className="h-14 px-12 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all active:scale-95 flex items-center gap-4 rounded-none shadow-xl shadow-black/5"
          >
            <BookOpen className="w-5 h-5" />
            Viết tài liệu mới
          </Link>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Sidebar Controls */}
        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Filter className="w-4 h-4 text-zinc-300" /> Công cụ tác giả
            </div>
            <nav className="flex flex-col gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                    activeTab === tab.key
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <tab.icon className="w-4 h-4" /> {tab.label}
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeTab === tab.key ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/30 space-y-4">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Lời khuyên biên tập</div>
             <p className="text-[10px] font-medium text-zinc-400 leading-relaxed italic">
               "Sử dụng công cụ phân tích cảm xúc AI để thấu hiểu độc giả của bạn sâu sắc hơn."
             </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main 
          className="lg:col-span-9 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {activeTab === "overview" && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
              {revenue && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  {[
                    { label: "Doanh thu (dl)", val: revenue.total_revenue || 0, icon: TrendingUp },
                    { label: "Tổng lượt xem", val: revenue.total_views || 0, icon: Eye },
                    { label: "Đánh giá TB", val: revenue.avg_rating || 0, icon: Star },
                    { label: "Số lượng tài liệu", val: revenue.total_documents || 0, icon: BookOpen },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="p-8 border border-zinc-100 bg-white group hover:border-black transition-all duration-500"
                    >
                      <item.icon className="w-5 h-5 text-zinc-100 group-hover:text-black transition-colors mb-6" />
                      <h3 className="text-3xl font-bold text-black tracking-tighter mb-2">
                         {typeof item.val === 'number' && item.val > 1000 ? `${(item.val / 1000).toFixed(1)}K` : item.val}
                      </h3>
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{item.label}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-8">
                <div className="flex items-center gap-6">
                  <h2 className="text-sm font-bold text-black tracking-widest uppercase">Tài liệu đã số hóa</h2>
                  <div className="flex-1 h-px bg-zinc-50" />
                  <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.2em]">{documents.length} BẢN GHI</span>
                </div>

                {documents.length === 0 ? (
                  <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                    <BookOpen className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                    <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Bắt đầu bằng việc đăng tải tài liệu đầu tiên</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {documents.map((doc: any) => (
                      <Link
                        key={doc.id}
                        href={`/studio?document=${doc.id}`}
                        className="group flex flex-col md:flex-row md:items-center justify-between p-8 border border-zinc-100 hover:border-black transition-all duration-700 bg-white"
                      >
                        <div className="flex items-center gap-8 min-w-0">
                          <div className="w-14 h-14 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0 group-hover:bg-black group-hover:border-black transition-all duration-500">
                            <BookOpen className="w-7 h-7 text-zinc-200 group-hover:text-white transition-all" />
                          </div>
                          <div className="min-w-0 space-y-2">
                            <h3 className="font-bold text-xl text-black truncate tracking-tight group-hover:translate-x-1 transition-transform">{doc.title}</h3>
                            <div className="flex items-center gap-5 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                              <span
                                className={`px-3 py-1 border ${
                                  doc.status === "published"
                                    ? "bg-black text-white border-black"
                                    : "border-zinc-100 text-zinc-300"
                                }`}
                              >
                                {doc.status === "published" ? "Đã xuất bản" : "Bản nháp"}
                              </span>
                              <div className="w-1 h-1 bg-zinc-100" />
                              <span>{doc.chapters_count || 0} chương nội dung</span>
                            </div>
                          </div>
                        </div>
                        <div className="mt-6 md:mt-0 flex items-center gap-10 shrink-0">
                          <div className="flex items-center gap-3 text-[11px] font-bold text-black tracking-widest">
                            <Eye className="w-4 h-4 text-zinc-100" /> {doc.views || 0}
                          </div>
                          <ChevronRight className="w-6 h-6 text-zinc-100 group-hover:text-black group-hover:translate-x-2 transition-all duration-500" />
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "coupons" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
               <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Mã giảm giá & Ưu đãi</h2>
                <div className="flex-1 h-px bg-zinc-50" />
              </div>
              {coupons.length === 0 ? (
                <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                  <Ticket className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Hiện chưa có mã ưu đãi nào được thiết lập</p>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-8">
                  {coupons.map((c: any) => (
                    <div
                      key={c.id}
                      className="flex flex-col p-10 border border-zinc-100 bg-white hover:border-black transition-all duration-700 group"
                    >
                      <div className="flex justify-between items-start mb-10">
                        <div className="space-y-1">
                           <span className="text-3xl font-bold text-black tracking-tighter block">{c.code}</span>
                           <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Mã khuyến mãi</span>
                        </div>
                        <span
                          className={`text-[9px] font-bold px-4 py-1.5 border tracking-widest uppercase ${
                            c.is_active ? "bg-black text-white border-black" : "bg-zinc-50 border-zinc-100 text-zinc-300"
                          }`}
                        >
                          {c.is_active ? "Hoạt động" : "Hết hạn"}
                        </span>
                      </div>
                      <div className="space-y-6">
                        <div className="w-full h-1 bg-zinc-50 overflow-hidden">
                          <div
                            className="bg-black h-full transition-all duration-1000"
                            style={{ width: `${(c.used_count / (c.max_uses || 1)) * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between items-end">
                           <div className="text-[11px] font-bold text-black">GIẢM {c.discount_percent}%</div>
                           <div className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                             Sử dụng {c.used_count}/{c.max_uses} lượt
                           </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "series" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
               <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Bộ sưu tập biên tập</h2>
                <div className="flex-1 h-px bg-zinc-50" />
              </div>
              {series.length === 0 ? (
                <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                  <Layers className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có bộ sưu tập nào được khởi tạo</p>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {series.map((s: any) => (
                    <div
                      key={s.id}
                      className="p-10 border border-zinc-100 bg-white hover:border-black transition-all duration-700 group flex flex-col justify-between min-h-[300px]"
                    >
                      <div className="space-y-6">
                        <div className="w-12 h-12 border border-zinc-100 bg-zinc-50 flex items-center justify-center group-hover:bg-black group-hover:text-white group-hover:border-black transition-all">
                           <Layers className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-bold text-black tracking-tight group-hover:translate-x-1 transition-transform">{s.title}</h3>
                        <p className="text-[13px] text-zinc-400 line-clamp-3 leading-relaxed font-medium">
                          {s.description || "Danh sách này tập hợp các nội dung tri thức chuyên sâu phục vụ nhu cầu nghiên cứu."}
                        </p>
                      </div>
                      <div className="pt-8 border-t border-zinc-50 mt-8">
                        <span className="text-[10px] font-bold text-black uppercase tracking-widest flex items-center gap-2">
                          <BookOpen className="w-3.5 h-3.5" /> {s.document_count} TÀI LIỆU
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "sentiment" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
               <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Phân tích cảm xúc AI</h2>
                <div className="flex-1 h-px bg-zinc-50" />
              </div>
              <div className="max-w-2xl border border-zinc-100 p-12 bg-white space-y-10">
                <div className="space-y-8">
                  <div className="space-y-4">
                    <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Lựa chọn tài liệu phân tích</label>
                    <select
                      value={selectedDocumentId}
                      onChange={(e) => setSelectedDocumentId(e.target.value)}
                      className="w-full h-16 px-6 border border-zinc-100 bg-zinc-50/30 text-sm font-bold focus:outline-none focus:border-black transition-all appearance-none cursor-pointer rounded-none"
                    >
                      <option value="">Chọn một tài liệu</option>
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
                    {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Brain className="w-5 h-5" />}
                    Khởi tạo phân tích AI
                  </button>
                </div>
              </div>

              {sentiment && (
                <div className="border border-zinc-100 p-12 bg-white animate-in slide-in-from-top-6 duration-700 space-y-12 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8">
                     <Sparkles className="w-10 h-10 text-zinc-50" />
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-10 border-b border-zinc-50 pb-12">
                    {[
                      { label: "Cảm xúc chung", val: sentiment.sentiment },
                      { label: "Tích cực", val: `${sentiment.positive_pct}%` },
                      { label: "Tiêu cực", val: `${sentiment.negative_pct}%` },
                      { label: "Tổng phản hồi", val: sentiment.total_reviews || 0 },
                    ].map((s, i) => (
                      <div key={i} className="space-y-2">
                        <h4 className="text-3xl font-bold text-black tracking-tighter capitalize">{s.val}</h4>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">{s.label}</p>
                      </div>
                    ))}
                  </div>
                  <div className="bg-zinc-50 p-10 border-l-[6px] border-black">
                    <p className="text-base text-zinc-500 leading-relaxed font-medium italic">"{sentiment.summary}"</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "grammar" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
               <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Kiểm định ngữ pháp AI</h2>
                <div className="flex-1 h-px bg-zinc-50" />
              </div>
              <div className="max-w-2xl border border-zinc-100 p-12 bg-white space-y-10">
                <div className="space-y-8">
                  <div className="space-y-4">
                    <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Chọn tài liệu</label>
                    <select
                      value={selectedDocumentId}
                      onChange={(e) => setSelectedDocumentId(e.target.value)}
                      className="w-full h-16 px-6 border border-zinc-100 bg-zinc-50/30 text-sm font-bold focus:outline-none focus:border-black transition-all appearance-none cursor-pointer rounded-none"
                    >
                      <option value="">Lựa chọn</option>
                      {documents.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-4">
                    <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Mã chương nội dung</label>
                    <input
                      type="text"
                      placeholder=""
                      value={selectedChapterId}
                      onChange={(e) => setSelectedChapterId(e.target.value)}
                      className="w-full h-16 px-6 border border-zinc-100 bg-zinc-50/30 text-sm font-bold focus:outline-none focus:border-black transition-all placeholder:text-zinc-200 rounded-none"
                    />
                  </div>
                  <button
                    onClick={checkGrammar}
                    disabled={processing || !selectedDocumentId || !selectedChapterId}
                    className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 disabled:opacity-50 transition-all flex items-center justify-center gap-4 active:scale-[0.98] shadow-xl shadow-black/5"
                  >
                    {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
                    Bắt đầu kiểm định
                  </button>
                </div>
              </div>

              {grammarResult && (
                <div className="border border-zinc-100 p-12 bg-white animate-in slide-in-from-top-6 duration-700 space-y-12">
                  <div className="grid grid-cols-2 gap-12 border-b border-zinc-50 pb-12">
                    <div className="space-y-2">
                      <h4 className="text-5xl font-bold text-black tracking-tighter">{grammarResult.score}<span className="text-xl text-zinc-200">/100</span></h4>
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Điểm chuẩn ngôn từ</p>
                    </div>
                    <div className="space-y-2">
                      <h4 className="text-5xl font-bold text-black tracking-tighter">
                        {grammarResult.word_count.toLocaleString()}
                      </h4>
                      <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Quy mô từ vựng</p>
                    </div>
                  </div>
                  <div className="bg-zinc-50 p-10">
                    <p className="text-base text-zinc-500 leading-relaxed font-medium italic">"{grammarResult.message}"</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "cover" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
               <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Thiết kế bìa thông minh</h2>
                <div className="flex-1 h-px bg-zinc-50" />
              </div>
              <div className="max-w-2xl border border-zinc-100 p-12 bg-white space-y-12">
                <div className="space-y-10">
                  <div className="space-y-4">
                    <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Tài liệu mục tiêu</label>
                    <select
                      value={selectedDocumentId}
                      onChange={(e) => setSelectedDocumentId(e.target.value)}
                      className="w-full h-16 px-6 border border-zinc-100 bg-zinc-50/30 text-sm font-bold focus:outline-none focus:border-black transition-all appearance-none cursor-pointer rounded-none"
                    >
                      <option value="">Lựa chọn</option>
                      {documents.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={generateCover}
                    disabled={processing || !selectedDocumentId}
                    className="w-full h-20 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 disabled:opacity-50 transition-all flex items-center justify-center gap-4 active:scale-[0.98] shadow-2xl shadow-black/10"
                  >
                    {processing ? <Loader2 className="w-6 h-6 animate-spin" /> : <ImageIcon className="w-6 h-6" />}
                    TẠO ẢNH BÌA AI (MINIMALIST)
                  </button>
                  <div className="p-8 bg-zinc-50 border border-zinc-100 text-center">
                    <p className="text-[11px] text-zinc-400 font-medium leading-relaxed italic uppercase tracking-wider">
                      Hệ thống sẽ dựa trên nội dung tóm tắt để tạo ra một tác phẩm nghệ thuật tối giản độc bản.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "assets" && (
            <div className="animate-in slide-in-from-bottom-4 duration-700 space-y-12">
              <div className="flex items-center gap-6">
                <h2 className="text-sm font-bold text-black tracking-widest uppercase">Kho lưu trữ tài nguyên số</h2>
                <div className="flex-1 h-px bg-zinc-50" />
                <span className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">{assets.length} TẬP TIN</span>
              </div>

              {assets.length === 0 ? (
                <div className="py-48 text-center border border-dashed border-zinc-200 bg-zinc-50/20">
                  <FolderOpen className="w-16 h-16 text-zinc-100 mx-auto mb-10 stroke-[1]" />
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Chưa có dữ liệu phương tiện nào</p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {assets.map((a: any) => (
                    <div
                      key={a.id}
                      className="flex items-center justify-between p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-700 group"
                    >
                      <div className="flex items-center gap-8 min-w-0">
                        <div className="w-14 h-14 bg-zinc-50 border border-zinc-100 flex items-center justify-center shrink-0 group-hover:bg-black group-hover:text-white group-hover:border-black transition-all duration-500">
                          <ImageIcon className="w-6 h-6 text-zinc-200 group-hover:text-white transition-all" />
                        </div>
                        <div className="min-w-0 flex flex-col space-y-2">
                          <span className="text-lg font-bold text-black truncate tracking-tight group-hover:translate-x-1 transition-transform">{a.filename}</span>
                          <div className="flex items-center gap-4 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                            <span className="text-black">{a.type}</span>
                            <div className="w-1 h-1 bg-zinc-100" />
                            <span>
                              {a.size_bytes > 0 ? `${(a.size_bytes / 1024).toFixed(1)} KB` : "0 KB"}
                            </span>
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteAsset(a.id)}
                        className="w-14 h-14 flex items-center justify-center text-zinc-200 hover:text-black hover:bg-zinc-50 transition-all active:scale-95 group/trash"
                      >
                        <Trash2 className="w-5 h-5 group-hover/trash:scale-110 transition-transform" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
