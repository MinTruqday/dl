"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import Link from "next/link";
import { BarChart3, BookOpen, TrendingUp, Tag, Ticket, Layers, ChevronRight, Eye, Star, Clock, Brain, CheckCircle, Image, FolderOpen, Loader2, Trash2 } from "lucide-react";

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
  const [message, setMessage] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => { fetchAll(); }, []);

  const h = () => ({ Authorization: `Bearer ${getToken()}` });
  const jh = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` });

  const fetchAll = async () => {
    try {
      const [revenueR, documentsR, couponsR, seriesR, assetsR] = await Promise.all([
        fetch(`${API_URL}/author/revenue`, { headers: h() }),
        fetch(`${API_URL}/author/documents`, { headers: h() }),
        fetch(`${API_URL}/author/coupons`, { headers: h() }),
        fetch(`${API_URL}/author/series`, { headers: h() }),
        fetch(`${API_URL}/author/assets`, { headers: h() }),
      ]);
      if (revenueR.ok) setRevenue(await revenueR.json());
      if (documentsR.ok) setDocuments(await documentsR.json());
      if (couponsR.ok) setCoupons(await couponsR.json());
      if (seriesR.ok) setSeries(await seriesR.json());
      if (assetsR.ok) setAssets(await assetsR.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (msg: string) => { setMessage(msg); setTimeout(() => setMessage(""), 3000); };

  const analyzeSentiment = async () => {
    if (!selectedDocumentId) return;
    setProcessing(true);
    setSentiment(null);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/sentiment`, { headers: h() });
      if (res.ok) setSentiment(await res.json());
      else showMsg("Không thể phân tích cảm xúc");
    } catch (e) { showMsg("Lỗi kết nối"); }
    setProcessing(false);
  };

  const checkGrammar = async () => {
    if (!selectedDocumentId || !selectedChapterId) return;
    setProcessing(true);
    setGrammarResult(null);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/grammar/${selectedChapterId}`, {
        method: "POST", headers: h(),
      });
      if (res.ok) setGrammarResult(await res.json());
      else showMsg("Không thể kiểm tra ngữ pháp");
    } catch (e) { showMsg("Lỗi kết nối"); }
    setProcessing(false);
  };

  const generateCover = async () => {
    if (!selectedDocumentId) return;
    setProcessing(true);
    try {
      const res = await fetch(`${API_URL}/author/documents/${selectedDocumentId}/generate-cover`, {
        method: "POST", headers: jh(),
        body: JSON.stringify({ style: "minimalist" }),
      });
      if (res.ok) {
        const data = await res.json();
        showMsg(data.message || "Đã tạo ảnh bìa");
      } else showMsg("Không thể tạo ảnh bìa");
    } catch (e) { showMsg("Lỗi kết nối"); }
    setProcessing(false);
  };

  const deleteAsset = async (assetId: string) => {
    try {
      const res = await fetch(`${API_URL}/author/assets/${assetId}`, {
        method: "DELETE", headers: h(),
      });
      if (res.ok) { showMsg("Đã xóa tài nguyên"); fetchAll(); }
    } catch (e) { showMsg("Lỗi kết nối"); }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  const tabs: { key: TabKey; label: string; icon: any }[] = [
    { key: "overview", label: "Tổng quan", icon: BarChart3 },
    { key: "coupons", label: "Mã giảm giá", icon: Ticket },
    { key: "series", label: "Series tài liệu", icon: Layers },
    { key: "sentiment", label: "Cảm xúc AI", icon: Brain },
    { key: "grammar", label: "Ngữ pháp", icon: CheckCircle },
    { key: "cover", label: "Ảnh bìa AI", icon: Image },
    { key: "assets", label: "Tài nguyên", icon: FolderOpen },
  ];

  return (
    <div className="w-full max-w-[1100px] mx-auto px-6 lg:px-8 py-12 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[12px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <span className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-2">Bảng điều khiển</span>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Quản lý tài liệu</h1>
      </header>

      <div className="flex gap-1 mb-10 border-b border-border overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-3 text-[12px] font-bold tracking-widest transition-all border-b-2 whitespace-nowrap ${
              activeTab === tab.key ? "border-black text-black" : "border-transparent text-zinc-400 hover:text-black"
            }`}
          >
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="animate-in fade-in duration-300">
          {revenue && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
              <div className="border border-border p-5"><TrendingUp className="w-5 h-5 text-zinc-400 mb-3" /><span className="text-3xl font-bold text-black">{revenue.total_revenue || 0}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Doanh thu (Coin)</p></div>
              <div className="border border-border p-5"><Eye className="w-5 h-5 text-zinc-400 mb-3" /><span className="text-3xl font-bold text-black">{revenue.total_views || 0}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Lượt xem</p></div>
              <div className="border border-border p-5"><Star className="w-5 h-5 text-zinc-400 mb-3" /><span className="text-3xl font-bold text-black">{revenue.total_sales || 0}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Lượt mua</p></div>
              <div className="border border-border p-5"><BookOpen className="w-5 h-5 text-zinc-400 mb-3" /><span className="text-3xl font-bold text-black">{revenue.total_documents || 0}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tài liệu</p></div>
            </div>
          )}
          <h2 className="text-xs font-bold tracking-widest text-black mb-6 flex items-center gap-2"><BookOpen className="w-4 h-4" /> Tài liệu của bạn</h2>
          {documents.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border"><p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có tài liệu nào</p></div>
          ) : (
            <div className="space-y-3">{documents.map((doc: any) => (
              <Link key={doc.id} href={`/studio?document=${doc.id}`} className="group flex items-center justify-between p-5 border border-border hover:border-black transition-all duration-300">
                <div className="flex items-center gap-4 min-w-0">
                  <BookOpen className="w-5 h-5 text-zinc-300 group-hover:text-black transition-colors shrink-0" />
                  <div className="min-w-0">
                    <h3 className="font-bold text-black truncate group-hover:underline underline-offset-4">{doc.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-[12px] text-zinc-400 font-bold tracking-widest">
                      <span className={`px-2 py-0.5 border ${doc.status === "published" ? "border-black text-black" : "border-zinc-200 text-zinc-400"}`}>{doc.status === "published" ? "Xuất bản" : doc.status === "draft" ? "Bản nháp" : doc.status}</span>
                      <span>{doc.chapters_count || 0} chương</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-[12px] font-bold text-zinc-400 tracking-widest shrink-0">
                  <span className="flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" /> {doc.views || 0}</span>
                  <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            ))}</div>
          )}
        </div>
      )}

      {activeTab === "coupons" && (
        <div className="animate-in fade-in duration-300">
          <h2 className="text-xs font-bold tracking-widest text-black mb-6 flex items-center gap-2"><Ticket className="w-4 h-4" /> Mã giảm giá</h2>
          {coupons.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border"><p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có mã giảm giá</p></div>
          ) : (
            <div className="space-y-3">{coupons.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between p-5 border border-border">
                <div><span className="font-bold text-black text-lg tracking-widest">{c.code}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Giảm {c.discount_percent}% | Đã dùng {c.used_count}/{c.max_uses}</p></div>
                <span className={`text-[12px] font-bold tracking-widest px-3 py-1 border ${c.is_active ? "border-black text-black" : "border-zinc-200 text-zinc-400"}`}>{c.is_active ? "Hoạt động" : "Hết hạn"}</span>
              </div>
            ))}</div>
          )}
        </div>
      )}

      {activeTab === "series" && (
        <div className="animate-in fade-in duration-300">
          <h2 className="text-xs font-bold tracking-widest text-black mb-6 flex items-center gap-2"><Layers className="w-4 h-4" /> Series tài liệu</h2>
          {series.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border"><p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có Series</p></div>
          ) : (
            <div className="space-y-3">{series.map((s: any) => (
              <div key={s.id} className="p-5 border border-border"><h3 className="font-bold text-black">{s.title}</h3><p className="text-sm text-zinc-500 mt-1">{s.description}</p><span className="text-[12px] text-zinc-400 font-bold tracking-widest mt-2 block">{s.document_count} tài liệu</span></div>
            ))}</div>
          )}
        </div>
      )}

      {activeTab === "sentiment" && (
        <div className="animate-in fade-in duration-300 space-y-6">
          <div className="border border-border p-6">
            <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6 uppercase"><Brain className="w-4 h-4" /> Phân tích cảm xúc độc giả</h2>
            <select value={selectedDocumentId} onChange={(e) => setSelectedDocumentId(e.target.value)} className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all mb-4 bg-white">
              <option value="">Chọn tài liệu</option>
              {documents.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
            </select>
            <button onClick={analyzeSentiment} disabled={processing || !selectedDocumentId} className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 disabled:bg-zinc-300 transition-all flex items-center justify-center gap-2">
              {processing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />} Phân tích
            </button>
          </div>
          {sentiment && (
            <div className="border border-border p-6 animate-in fade-in duration-300">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div><span className="text-2xl font-bold text-black capitalize">{sentiment.sentiment}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Cảm xúc chung</p></div>
                <div><span className="text-2xl font-bold text-black">{sentiment.positive_pct}%</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tích cực</p></div>
                <div><span className="text-2xl font-bold text-black">{sentiment.negative_pct}%</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tiêu cực</p></div>
                <div><span className="text-2xl font-bold text-black">{sentiment.total_reviews || 0}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Đánh giá</p></div>
              </div>
              <p className="text-sm text-zinc-500 p-4 bg-zinc-50">{sentiment.summary}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "grammar" && (
        <div className="animate-in fade-in duration-300 space-y-6">
          <div className="border border-border p-6">
            <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6 uppercase"><CheckCircle className="w-4 h-4" /> Kiểm tra ngữ pháp tự động</h2>
            <select value={selectedDocumentId} onChange={(e) => setSelectedDocumentId(e.target.value)} className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all mb-4 bg-white">
              <option value="">Chọn tài liệu</option>
              {documents.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
            </select>
            <input type="text" placeholder="ID Chương cần kiểm tra" value={selectedChapterId} onChange={(e) => setSelectedChapterId(e.target.value)} className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all mb-4" />
            <button onClick={checkGrammar} disabled={processing || !selectedDocumentId || !selectedChapterId} className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 disabled:bg-zinc-300 transition-all flex items-center justify-center gap-2">
              {processing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />} Kiểm tra
            </button>
          </div>
          {grammarResult && (
            <div className="border border-border p-6 animate-in fade-in duration-300">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div><span className="text-2xl font-bold text-black">{grammarResult.score}/100</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Điểm ngữ pháp</p></div>
                <div><span className="text-2xl font-bold text-black">{grammarResult.word_count}</span><p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Số từ</p></div>
              </div>
              <p className="text-sm text-zinc-500 p-4 bg-zinc-50">{grammarResult.message}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === "cover" && (
        <div className="animate-in fade-in duration-300 border border-border p-6">
          <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6"><Image className="w-4 h-4" /> Tạo ảnh bìa AI</h2>
          <select value={selectedDocumentId} onChange={(e) => setSelectedDocumentId(e.target.value)} className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all mb-4 bg-white">
            <option value="">Chọn tài liệu</option>
            {documents.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
          </select>
          <button onClick={generateCover} disabled={processing || !selectedDocumentId} className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 disabled:bg-zinc-300 transition-all flex items-center justify-center gap-2">
            {processing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Image className="w-3.5 h-3.5" />} Tạo ảnh bìa tối giản
          </button>
          <p className="text-xs text-zinc-400 mt-4 text-center">Ảnh bìa được tạo dựa trên tiêu đề và mô tả tài liệu qua hệ thống AI</p>
        </div>
      )}

      {activeTab === "assets" && (
        <div className="animate-in fade-in duration-300">
          <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6"><FolderOpen className="w-4 h-4" /> Quản lý tài nguyên</h2>
          {assets.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-border">
              <FolderOpen className="w-12 h-12 text-zinc-200 mx-auto mb-4" />
              <p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có tài nguyên nào</p>
            </div>
          ) : (
            <div className="space-y-2">{assets.map((a: any) => (
              <div key={a.id} className="flex items-center justify-between p-4 border border-border hover:border-black transition-all">
                <div>
                  <span className="text-sm font-bold text-black">{a.filename}</span>
                  <span className="text-[12px] text-zinc-400 font-bold tracking-widest ml-3">{a.type}</span>
                  <span className="text-[12px] text-zinc-400 ml-3">{a.size_bytes > 0 ? `${(a.size_bytes / 1024).toFixed(1)} KB` : ""}</span>
                </div>
                <button onClick={() => deleteAsset(a.id)} className="text-zinc-300 hover:text-black transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}</div>
          )}
        </div>
      )}
    </div>
  );
}
