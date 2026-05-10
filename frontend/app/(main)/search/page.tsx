"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/services/document.service";
import {
  Search,
  Filter,
  DocumentOpen,
  User,
  Clock,
  Star,
  X,
  ArrowUpDown,
} from "lucide-react";

export default function SearchResultsPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    price: "all",
    rating: 0,
    time: "all",
    category: "Tất cả",
    sort: "newest",
  });

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
    const newHistory = [q, ...history.filter((h) => h !== q)].slice(0, 10);
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

      if (filters.price === "free")
        filtered = filtered.filter((b: any) => !b.price_dl || b.price_dl === 0);
      if (filters.price === "paid")
        filtered = filtered.filter((b: any) => b.price_dl > 0);

      if (filters.rating > 0)
        filtered = filtered.filter(
          (b: any) => (b.average_rating || 0) >= filters.rating,
        );

      const now = new Date();
      if (filters.time === "today") {
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setDate(now.getDate() - 1)),
        );
      } else if (filters.time === "this_week") {
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setDate(now.getDate() - 7)),
        );
      } else if (filters.time === "this_month") {
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setMonth(now.getMonth() - 1)),
        );
      }

      if (filters.sort === "most_viewed") {
        filtered.sort((a: any, b: any) => (b.views || 0) - (a.views || 0));
      } else if (filters.sort === "highest_rated") {
        filtered.sort(
          (a: any, b: any) => (b.average_rating || 0) - (a.average_rating || 0),
        );
      } else {
        filtered.sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
      }

      setResults(filtered);
    } catch (err: any) {
      console.error("Tìm kiếm thất bại:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 md:py-24 animate-in fade-in font-sans">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16">
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-10">
            <div className="flex items-center justify-between border-b border-black pb-4">
              <h3 className="text-xs font-bold">Bộ lọc nội dung</h3>
              <Filter className="w-3.5 h-3.5" />
            </div>

            <div className="space-y-10">
              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400">
                  Sắp xếp theo
                </label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "newest", label: "Mới nhất", icon: Clock },
                    {
                      id: "most_viewed",
                      label: "Xem nhiều nhất",
                      icon: ArrowUpDown,
                    },
                    { id: "highest_rated", label: "Đánh giá cao", icon: Star },
                  ].map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setFilters({ ...filters, sort: s.id })}
                      className={`text-[10px] font-bold px-4 py-3 border text-left flex items-center justify-between active:scale-95 ${filters.sort === s.id ? "bg-black text-white border-black" : " border-zinc-100 text-zinc-400"}`}
                    >
                      {s.label}
                      <s.icon className="w-3 h-3" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400">
                  Thời gian xuất bản
                </label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "all", label: "Tất cả thời gian" },
                    { id: "today", label: "Trong 24 giờ qua" },
                    { id: "this_week", label: "Tuần này" },
                    { id: "this_month", label: "Tháng này" },
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setFilters({ ...filters, time: t.id })}
                      className={`text-[10px] font-bold px-4 py-3 border text-left active:scale-95 ${filters.time === t.id ? "bg-black text-white border-black" : " border-zinc-100 text-zinc-400"}`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400">
                  Giá tài liệu
                </label>
                <div className="flex gap-1">
                  {["all", "free", "paid"].map((p) => (
                    <button
                      key={p}
                      onClick={() => setFilters({ ...filters, price: p })}
                      className={`flex-1 text-[9px] font-bold py-3 border active:scale-95 ${filters.price === p ? "bg-black text-white border-black" : " border-zinc-100 text-zinc-400"}`}
                    >
                      {p === "all"
                        ? "Tất cả"
                        : p === "free"
                          ? "Miễn phí"
                          : "Có phí"}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400">
                  Đánh giá tối thiểu
                </label>
                <div className="flex gap-1">
                  {[0, 3, 4, 5].map((r) => (
                    <button
                      key={r}
                      onClick={() => setFilters({ ...filters, rating: r })}
                      className={`flex-1 py-3 border text-[10px] font-bold active:scale-95 ${filters.rating === r ? "bg-black text-white border-black" : " border-zinc-100 text-zinc-400"}`}
                    >
                      {r === 0 ? "Tất cả" : `${r} sao`}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {history.length > 0 && (
            <div className="space-y-6 pt-12 border-t border-zinc-100">
              <div className="flex items-center justify-between">
                <h3 className="text-[10px] font-bold">Gần đây</h3>
                <button
                  onClick={clearHistory}
                  className="text-[9px] font-bold text-zinc-300 transition-colors active:scale-95"
                >
                  Xóa sạch
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <div key={h} className="group/item relative">
                    <Link
                      href={`/search?q=${h}`}
                      className="block text-[9px] font-bold px-3 py-2 bg-white border border-zinc-100 pr-8 active:scale-95"
                    >
                      {h}
                    </Link>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        const newHistory = history.filter((item) => item !== h);
                        setHistory(newHistory);
                        localStorage.setItem(
                          "doclib_search_history",
                          JSON.stringify(newHistory),
                        );
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 transition-opacity active:scale-90"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="lg:col-span-9 space-y-12 animate-in slide-in-from-bottom-4 ">
          <div className="flex items-center gap-6 border-b border-zinc-100 pb-10">
            <div className="w-16 h-16 bg-black flex items-center justify-center text-white">
              <Search className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h1 className="text-4xl font-bold tracking-tighter leading-none">
                Kết quả tìm kiếm
              </h1>
              <p className="text-zinc-400 text-[10px] font-bold">
                Từ khóa: "{query}" • Tìm thấy {results.length} tài liệu phù hợp
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8">
            {loading ? (
              <div className="space-y-8">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-48 bg-white animate-pulse border border-zinc-100 rounded-sm"
                  />
                ))}
              </div>
            ) : results.length > 0 ? (
              results.map((document) => (
                <Link
                  key={document._id}
                  href={`/tai-lieu/${document.slug}`}
                  className="group p-8 bg-white border border-zinc-100 flex gap-10 rounded-sm active:scale-[0.99]"
                >
                  <div className="w-32 h-44 bg-white border border-zinc-100 shrink-0 overflow-hidden relative rounded-sm">
                    {document.cover_url ? (
                      <img
                        src={document.cover_url}
                        alt={document.title}
                        className="w-full h-full object-cover transition-transform grayscale  "
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[10px] font-bold text-zinc-200 text-center p-6 tracking-tighter">
                        {document.title}
                      </div>
                    )}
                    <div className="absolute top-2 right-2 px-2 py-1 bg-white border border-zinc-100 text-[8px] font-bold">
                      {document.price_dl > 0
                        ? `${document.price_dl} dl`
                        : "Miễn phí"}
                    </div>
                  </div>
                  <div className="flex-1 space-y-4">
                    <div className="flex items-center gap-4 text-[9px] font-bold text-zinc-400">
                      <span className="flex items-center gap-1.5">
                        <DocumentOpen className="w-3.5 h-3.5" />{" "}
                        {document.categories?.[0] || "Tài liệu"}
                      </span>
                      <span className="w-1 h-1 bg-zinc-100" />
                      <span className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5" />{" "}
                        {document.author_name || "Tác giả DocLib"}
                      </span>
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight underline-offset-8 decoration-2 decoration-black ">
                      {document.title}
                    </h3>
                    <p className="text-sm text-zinc-500 line-clamp-2 leading-relaxed max-w-4xl font-medium">
                      {document.description}
                    </p>
                    <div className="pt-4 flex items-center gap-8">
                      <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-400">
                        <Clock className="w-4 h-4" />{" "}
                        {new Date(document.created_at).toLocaleDateString(
                          "vi-VN",
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[10px] font-bold text-black">
                        <Star className="w-4 h-4 fill-black" />{" "}
                        {document.average_rating?.toFixed(1) || "0.0"}
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
                <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
