"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Clock, 
  Trash2, 
  Calendar, 
  Search, 
  Loader2, 
  Info, 
  Sparkles, 
  BookOpen, 
  ChevronRight,
  TrendingUp,
  FileText,
  Filter,
  CheckCircle2,
} from "lucide-react";
import { getReadingHistoryAPI } from "@/app/lib/api";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ReadingHistoryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "reading" | "completed">("all");

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getReadingHistoryAPI();
      setHistory(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error("Lỗi tải lịch sử:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const filteredHistory = history.filter((item) => {
    const matchesSearch = (item.document_title || "").toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === "all") return matchesSearch;
    if (activeTab === "reading") return matchesSearch && (item.progress_percentage || 0) < 100;
    if (activeTab === "completed") return matchesSearch && (item.progress_percentage || 0) === 100;
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {/* Header - Premium Standard */}
      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Lịch sử đọc
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Knowledge Reading Journey <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          
          <Button 
            className="h-14 px-8 bg-zinc-50 text-zinc-400 hover:text-black hover:bg-white border border-zinc-100 hover:border-black text-[10px] font-bold tracking-widest uppercase transition-all rounded-none"
          >
            <Trash2 className="w-4 h-4 mr-2" /> Xóa toàn bộ lịch sử
          </Button>
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
              <Filter className="w-4 h-4 text-zinc-300" /> Trạng thái đọc
            </div>
            <nav className="flex flex-col gap-1">
              {[
                { id: "all", label: "Tất cả hoạt động", icon: Clock },
                { id: "reading", label: "Đang đọc dở", icon: BookOpen },
                { id: "completed", label: "Đã hoàn thành", icon: CheckCircle2 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                    activeTab === tab.id
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <tab.icon className="w-4 h-4" /> {tab.label}
                  </div>
                  <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeTab === tab.id ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-[0.2em] px-1">
              <Search className="w-4 h-4 text-zinc-300" /> Tìm kiếm
            </div>
            <div className="relative">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300" />
              <Input 
                placeholder=""
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-14 h-14 bg-zinc-50/50 border-zinc-100 focus:bg-white focus:border-black transition-all text-xs font-bold rounded-none"
              />
            </div>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/30 space-y-4">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Thống kê hành trình</div>
             <div className="space-y-3">
                <div className="flex justify-between text-[11px] font-medium">
                   <span className="text-zinc-400">Đã đọc:</span>
                   <span className="text-black font-bold">{history.length} tài liệu</span>
                </div>
                <div className="flex justify-between text-[11px] font-medium">
                   <span className="text-zinc-400">Hoàn tất:</span>
                   <span className="text-black font-bold">{history.filter(h => h.progress_percentage === 100).length}</span>
                </div>
             </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div 
          className="lg:col-span-9 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {filteredHistory.length > 0 ? (
            <div className="space-y-4">
              {filteredHistory.map((item, index) => (
                <div
                  key={item.document_id + index}
                  className="group flex items-center justify-between p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-700"
                >
                  <div className="flex items-center gap-8 flex-1 min-w-0">
                    <div className="w-16 h-20 bg-zinc-50 border border-zinc-100 shrink-0 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-700">
                      {item.cover_url ? (
                        <img src={item.cover_url} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt={item.document_title} />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <FileText className="w-8 h-8 text-zinc-100 stroke-[1]" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-4 mb-2">
                        <span className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-wider">
                          <Calendar className="w-3.5 h-3.5" />
                          {item.last_read_at ? new Date(item.last_read_at).toLocaleDateString("vi-VN") : "Gần đây"}
                        </span>
                        <div className="w-1 h-1 bg-zinc-100" />
                        <span className="text-[10px] font-bold text-black uppercase tracking-widest truncate">
                          {item.author_name || "Tri thức DocLib"}
                        </span>
                      </div>
                      
                      <Link 
                        href={`/document/${item.document_slug}`}
                        className="text-xl font-bold text-black hover:underline underline-offset-4 decoration-1 tracking-tight truncate block mb-4 group-hover:translate-x-1 transition-transform"
                      >
                        {item.document_title}
                      </Link>

                      <div className="max-w-md space-y-2">
                         <div className="w-full bg-zinc-50 h-1 relative overflow-hidden">
                           <div 
                             className="bg-black h-full transition-all duration-1000"
                             style={{ width: `${item.progress_percentage || 0}%` }}
                           />
                         </div>
                         <div className="flex items-center justify-between">
                           <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Tiến độ tri thức</span>
                           <span className="text-[9px] font-bold text-black">{item.progress_percentage || 0}%</span>
                         </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 ml-8">
                    <Link
                      href={`/documents/viewer/${item.document_id}`}
                      className="bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase px-10 h-14 flex items-center justify-center hover:bg-zinc-800 transition-all active:scale-95 shadow-xl shadow-black/5 rounded-none"
                    >
                      Tiếp tục đọc
                    </Link>
                    <button className="w-14 h-14 border border-zinc-50 flex items-center justify-center text-zinc-200 hover:text-black hover:border-black transition-all active:scale-95 group/trash">
                      <Trash2 className="w-4 h-4 group-hover/trash:scale-110 transition-transform" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
              <div className="w-24 h-24 border border-zinc-100 bg-white flex items-center justify-center mb-10">
                <Clock className="w-10 h-10 text-zinc-100 stroke-[1]" />
              </div>
              <h2 className="text-3xl font-bold tracking-tighter text-black mb-4">Lịch sử trống</h2>
              <p className="text-sm font-medium text-zinc-400 mb-10 max-w-xs text-center uppercase tracking-widest leading-loose">
                Bạn chưa đọc tài liệu nào gần đây. Hãy bắt đầu khám phá kho tàng tri thức của DocLib.
              </p>
              <Link href="/">
                <Button className="h-16 px-14 bg-black text-white text-[11px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all shadow-2xl shadow-black/10 rounded-none">
                  Khám phá ngay
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
