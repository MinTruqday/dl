"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/app/lib/api";
import { Search, Filter, BookOpen, User, Clock, Star, Trash2, X } from "lucide-react";

export default function SearchResultsPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<string[]>([]);
  const [filters, setFilters] = useState({ price: "all", rating: 0, date: "all", category: "Tất cả" });

  useEffect(() => {
    const saved = localStorage.getItem("doclib_search_history");
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  useEffect(() => {
    if (query) {
      loadResults();
      saveToHistory(query);
    }
  }, [query, filters]);

  const saveToHistory = (q: string) => {
    const newHistory = [q, ...history.filter(h => h !== q)].slice(0, 10);
    setHistory(newHistory);
    localStorage.setItem("doclib_search_history", JSON.stringify(newHistory));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("doclib_search_history");
  };

  const loadResults = async () => {
    setLoading(true);
    try {
      const data = await getDocumentsAPI(query);
      let filtered = data || [];
      if (filters.price === "free") filtered = filtered.filter((d: any) => !d.price_coins || d.price_coins === 0);
      if (filters.price === "paid") filtered = filtered.filter((d: any) => d.price_coins > 0);
      if (filters.rating > 0) filtered = filtered.filter((d: any) => (d.average_rating || 0) >= filters.rating);
      setResults(filtered);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-300">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12">
           <div className="space-y-6">
              <h3 className="text-xs font-bold tracking-widest border-b border-zinc-100 pb-4">Bộ lọc tìm kiếm</h3>
              <div className="space-y-8">
                  <div className="space-y-3">
                    <label className="text-[12px] font-bold tracking-widest text-zinc-400">Chuyên mục</label>
                    <div className="flex flex-col gap-2">
                       {["Tất cả", "Công nghệ", "Kinh tế", "Văn học", "Nghệ thuật", "Khoa học"].map(c => (
                          <button 
                             key={c}
                             onClick={() => setFilters({...filters, category: c})}
                             className={`text-xs font-bold tracking-widest px-4 py-2 border text-left transition-all ${filters.category === c ? 'bg-black text-white border-black' : 'hover:bg-zinc-50 border-zinc-100'}`}
                          >
                             {c}
                          </button>
                       ))}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <label className="text-[12px] font-bold tracking-widest text-zinc-400">Giá tài liệu</label>
                    <div className="flex flex-col gap-2">
                       {["all", "free", "paid"].map(p => (
                          <button 
                             key={p}
                             onClick={() => setFilters({...filters, price: p})}
                             className={`text-xs font-bold tracking-widest px-4 py-2 border text-left transition-all ${filters.price === p ? 'bg-black text-white border-black' : 'hover:bg-zinc-50 border-zinc-100'}`}
                          >
                             {p === 'all' ? 'Tất cả' : p === 'free' ? 'Miễn phí' : 'Có phí'}
                          </button>
                       ))}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <label className="text-[12px] font-bold tracking-widest text-zinc-400">Xếp hạng tối thiểu</label>
                    <div className="flex gap-2">
                       {[0, 3, 4, 5].map(r => (
                          <button 
                             key={r}
                             onClick={() => setFilters({...filters, rating: r})}
                             className={`flex-1 py-2 border text-xs font-bold transition-all ${filters.rating === r ? 'bg-black text-white border-black' : 'hover:bg-zinc-50 border-zinc-100'}`}
                          >
                             {r === 0 ? 'Tất cả' : `${r}+`}
                          </button>
                       ))}
                    </div>
                 </div>
              </div>
           </div>

           {history.length > 0 && (
              <div className="space-y-4">
                 <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
                    <h3 className="text-xs font-bold tracking-widest">Lịch sử</h3>
                    <button onClick={clearHistory} className="text-[13px] font-bold tracking-widest text-zinc-400 hover:text-black">Xóa sạch</button>
                 </div>
                 <div className="flex flex-wrap gap-2">
                     {history.map(h => (
                        <div key={h} className="group/item relative">
                           <Link href={`/search?q=${h}`} className="block text-[12px] font-bold tracking-widest px-3 py-2 bg-zinc-50 border border-zinc-100 hover:border-black transition-all pr-8">
                              {h}
                           </Link>
                           <button 
                              onClick={(e) => {
                                 e.preventDefault();
                                 const newHistory = history.filter(item => item !== h);
                                 setHistory(newHistory);
                                 localStorage.setItem("doclib_search_history", JSON.stringify(newHistory));
                              }}
                              className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 transition-opacity hover:text-black"
                           >
                              <X className="w-3 h-3" />
                           </button>
                        </div>
                     ))}
                 </div>
              </div>
           )}
        </aside>

        <main className="lg:col-span-9 space-y-12">
          <div className="flex items-center gap-4 border-b border-zinc-100 pb-8">
            <div className="w-12 h-12 bg-black flex items-center justify-center">
              <Search className="w-5 h-5 text-white" />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold tracking-tighter leading-none">Tìm kiếm toàn cục</h1>
              <p className="text-muted-foreground text-[12px] font-bold tracking-widest">Kết quả cho "{query}" • Lọc theo nhu cầu tri thức</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {loading ? (
              <div className="space-y-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-zinc-50 animate-pulse border border-border" />
                ))}
              </div>
            ) : results.length > 0 ? (
              results.map((doc) => (
                <Link key={doc._id} href={`/document/${doc.slug}`} className="group p-6 bg-white border border-border hover:border-black transition-all duration-300 flex gap-6">
                  <div className="w-24 h-32 bg-zinc-100 border border-border shrink-0 overflow-hidden">
                    {doc.cover_url ? (
                       <img src={doc.cover_url} alt={doc.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                       <div className="w-full h-full flex items-center justify-center text-[12px] font-bold text-zinc-300 text-center p-4">
                          {doc.title}
                       </div>
                    )}
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3 text-[13px] font-bold tracking-widest text-zinc-400">
                      <span className="flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" /> {doc.categories?.[0] || "Tài liệu"}</span>
                      <span className="w-1 h-1 rounded-none bg-zinc-200" />
                      <span className="flex items-center gap-1"><User className="w-3.5 h-3.5" /> {doc.author_name || "Tác giả ẩn danh"}</span>
                    </div>
                    <h3 className="text-lg font-bold tracking-tight group-hover:underline underline-offset-4 decoration-2">{doc.title}</h3>
                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed max-w-3xl font-medium">
                      {doc.description}
                    </p>
                    <div className="pt-2 flex items-center gap-6">
                       <div className="flex items-center gap-1.5 text-[13px] font-bold tracking-widest text-zinc-300">
                          <Clock className="w-3.5 h-3.5" /> {new Date(doc.created_at).toLocaleDateString("vi-VN")}
                       </div>
                       <div className="flex items-center gap-1.5 text-[13px] font-bold tracking-widest text-black">
                          <Star className="w-3.5 h-3.5" /> {doc.average_rating?.toFixed(1) || "0.0"}
                       </div>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="h-[400px] flex flex-col items-center justify-center text-center border border-dashed border-border bg-zinc-50/50 p-12">
                 <div className="w-12 h-12 bg-zinc-100 flex items-center justify-center mb-4">
                    <Search className="w-6 h-6 text-zinc-300" />
                 </div>
                 <h3 className="text-sm font-bold tracking-widest mb-1">Không tìm thấy tài liệu nào</h3>
                 <p className="text-[12px] font-bold tracking-widest text-zinc-400">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
