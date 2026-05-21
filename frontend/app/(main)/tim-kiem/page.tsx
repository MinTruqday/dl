"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/services/document.service";
import {
  Search,
  Filter,
  FileText,
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div className="mb-8 border-b border-zinc-200 pb-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold text-black">Kết quả tìm kiếm</h1>
            <p className="text-zinc-500 text-sm font-medium">
              Từ khóa: "{query}" • Tìm thấy {results.length} tài liệu phù hợp
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <aside className="lg:col-span-3 space-y-12 animate-in fade-in ">
          <div className="space-y-6">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2 flex items-center justify-between">
              Bộ lọc nâng cao
              <Filter className="w-4 h-4 text-zinc-500" />
            </div>

            <div className="space-y-8">
              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-500">Sắp xếp theo</label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "newest", label: "Mới nhất", icon: Clock },
                    { id: "most_viewed", label: "Xem nhiều nhất", icon: ArrowUpDown },
                    { id: "highest_rated", label: "Đánh giá cao", icon: Star },
                  ].map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setFilters({ ...filters, sort: s.id })}
                      className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none   ${
                        filters.sort === s.id
                          ? "bg-zinc-100 text-black border-zinc-300"
                          : "bg-white text-zinc-500 border-transparent "
                      }`}
                    >
                      {s.label}
                      <s.icon className="w-4 h-4" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-500">Thời gian xuất bản</label>
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
                      className={`text-left px-3 py-2 text-sm font-medium border rounded-none   ${
                        filters.time === t.id
                          ? "bg-zinc-100 text-black border-zinc-300"
                          : "bg-white text-zinc-500 border-transparent "
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-500">Giá tài liệu</label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "all", label: "Tất cả" },
                    { id: "free", label: "Miễn phí" },
                    { id: "paid", label: "Có phí" },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setFilters({ ...filters, price: p.id })}
                      className={`text-left px-3 py-2 text-sm font-medium border rounded-none   ${
                        filters.price === p.id
                          ? "bg-zinc-100 text-black border-zinc-300"
                          : "bg-white text-zinc-500 border-transparent "
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-semibold text-zinc-500">Đánh giá tối thiểu</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 0, label: "Tất cả" },
                    { id: 3, label: "Từ 3 sao" },
                    { id: 4, label: "Từ 4 sao" },
                    { id: 5, label: "5 sao" },
                  ].map((r) => (
                    <button
                      key={r.id}
                      onClick={() => setFilters({ ...filters, rating: r.id })}
                      className={`text-center px-3 py-2 text-sm font-medium border rounded-none   ${
                        filters.rating === r.id
                          ? "bg-zinc-100 text-black border-zinc-300"
                          : "bg-white text-zinc-500 border-zinc-200 "
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {history.length > 0 && (
            <div className="space-y-4 pt-6 border-t border-zinc-200">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-zinc-500">Tìm kiếm gần đây</h3>
                <button
                  onClick={clearHistory}
                  className="text-xs font-medium text-zinc-400  "
                >
                  Xóa lịch sử
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <div key={h} className="group/item relative">
                    <Link
                      href={`/tim-kiem?q=${h}`}
                      className="block text-xs font-medium px-3 py-1.5 bg-white border border-zinc-200     rounded-none pr-8"
                    >
                      {h}
                    </Link>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        const newHistory = history.filter((item) => item !== h);
                        setHistory(newHistory);
                        localStorage.setItem("doclib_search_history", JSON.stringify(newHistory));
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400  opacity-0 group-hover/item:opacity-100 "
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="lg:col-span-9 space-y-6 animate-in slide-in-from-bottom-4 ">
          <div className="grid grid-cols-1 gap-6">
            {loading ? (
              <div className="grid grid-cols-1 gap-6">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="h-40 bg-zinc-50 animate-pulse border border-zinc-200 rounded-none"
                  />
                ))}
              </div>
            ) : results.length > 0 ? (
              results.map((document, i) => (
                <Link
                  key={`doc-${document._id || i}`}
                  href={`/tai-lieu/${document.slug}`}
                  className="group flex flex-row gap-6 p-4 border border-zinc-200 bg-white rounded-none   "
                >
                  <div className="w-24 h-36 shrink-0 border border-zinc-200 bg-zinc-100 relative overflow-hidden">
                    {document.cover_url ? (
                      <img
                        src={document.cover_url}
                        alt={document.title}
                        className="w-full h-full object-cover grayscale mix-blend-multiply group-  "
                      />
                    ) : (
                      <div className="w-full h-full bg-zinc-100" />
                    )}
                  </div>

                  <div className="flex flex-col flex-1 gap-2 py-1">
                    {document.categories && document.categories.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {document.categories.slice(0, 3).map((tag: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 text-[10px] font-medium text-zinc-600 border border-zinc-200 bg-white"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    <h3 className="text-base font-semibold text-black line-clamp-2 leading-snug group- underline-offset-2">
                      {document.title}
                    </h3>

                    <div className="text-xs text-zinc-500 flex items-center gap-1.5">
                      <span className="truncate text-black font-medium">
                        {document.author_name || document.author?.full_name || document.author?.username || "Ẩn danh"}
                      </span>
                      <span>•</span>
                      <span className="shrink-0">
                        {document.created_at
                          ? new Date(document.created_at).toLocaleDateString("vi-VN")
                          : "Gần đây"}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-zinc-500">
                      <div className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5" />
                        <span>{document.views_count?.toLocaleString("vi-VN") || document.views || 0} lượt xem</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5" />
                        <span>{document.average_rating?.toFixed(1) || "0.0"} sao</span>
                      </div>
                    </div>

                    <div className="mt-auto pt-3 flex items-center justify-between">
                      <span className="text-xs font-semibold text-black">
                        {document.price_dl > 0 ? `${document.price_dl} dl` : "Miễn phí"}
                      </span>
                      <div className="text-xs font-semibold text-black border border-black px-3 py-1.5 uppercase tracking-wider group- group-  ">
                        Xem
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white rounded-none">
                <p className="text-sm font-medium text-zinc-500">Chưa có kết quả nào phù hợp</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
