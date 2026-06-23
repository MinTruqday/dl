"use client";
import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/features/content/services/document_metadata.service";
import {
  Filter,
  User,
  Clock,
  X,
  ArrowUpDown,
  BookOpen,
  Eye,
  LayoutGrid,
  List as ListIcon,
} from "lucide-react";

function SearchResultsContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<string[]>([]);
  const [filters, setFilters] = useState({
    price: "all",
    time: "all",
    category: "Tất cả",
    sort: "newest",
  });
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

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
      } else {
        filtered.sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
      }

      setResults(filtered);
    } catch (err: any) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 font-sans text-zinc-900 selection:bg-zinc-900 selection:text-white">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-zinc-900">
            Kết quả tìm kiếm
          </h1>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
            Từ khóa: "{query}" • Tìm thấy {results.length} tài liệu phù hợp
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex border border-zinc-200 bg-zinc-50 rounded-2xl overflow-hidden p-0.5 gap-0.5">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${
                viewMode === "grid"
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "bg-transparent text-zinc-400"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-xl transition-all duration-200 hover:scale-110 ${
                viewMode === "list"
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "bg-transparent text-zinc-400"
              }`}
            >
              <ListIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3 space-y-4">
          <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Bộ lọc nâng cao</span>
              <Filter className="w-3.5 h-3.5 text-zinc-400" />
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-wider block ml-1">
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
                  ].map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setFilters({ ...filters, sort: s.id })}
                      className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                        filters.sort === s.id
                          ? "bg-zinc-900 text-white shadow-md"
                          : "text-zinc-500 hover:bg-zinc-50"
                      }`}
                    >
                      <span>{s.label}</span>
                      <s.icon className="w-3.5 h-3.5" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-wider block ml-1">
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
                      className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                        filters.time === t.id
                          ? "bg-zinc-900 text-white shadow-md"
                          : "text-zinc-500 hover:bg-zinc-50"
                      }`}
                    >
                      <span>{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-wider block ml-1">
                  Giá tài liệu
                </label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "all", label: "Tất cả" },
                    { id: "free", label: "Miễn phí" },
                    { id: "paid", label: "Có phí" },
                  ].map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setFilters({ ...filters, price: p.id })}
                      className={`flex items-center justify-between px-3 py-2.5 text-sm font-medium rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 ${
                        filters.price === p.id
                          ? "bg-zinc-900 text-white shadow-md"
                          : "text-zinc-500 hover:bg-zinc-50"
                      }`}
                    >
                      <span>{p.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {history.length > 0 && (
            <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tìm kiếm gần đây</span>
                <button
                  onClick={clearHistory}
                  className="text-[9px] font-bold text-zinc-400 hover:text-black uppercase tracking-widest"
                >
                  Xóa
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <div key={h} className="group/item relative">
                    <Link
                      href={`/search?q=${h}`}
                      className="block text-xs font-semibold px-3 py-1.5 bg-zinc-50 border border-zinc-100 text-zinc-600 rounded-xl pr-8 hover:bg-zinc-100 transition-colors"
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
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 opacity-0 group-hover/item:opacity-100 hover:text-red-500 transition-all"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="lg:col-span-9 space-y-6">
          <div className="bg-white/90 backdrop-blur-sm border border-zinc-100 rounded-3xl shadow-sm p-5">
            {loading ? (
              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                  <div
                    key={i}
                    className={`flex ${viewMode === "grid" ? "flex-col" : "flex-row gap-5 p-3"} bg-white border border-zinc-100 rounded-2xl overflow-hidden animate-pulse`}
                  >
                    <div className={`bg-zinc-100 ${viewMode === "grid" ? "aspect-[2/3] w-full" : "w-20 h-28 shrink-0 rounded-xl"}`} />
                    <div className={`${viewMode === "grid" ? "p-3" : "flex-1 py-0.5"} space-y-2`}>
                      <div className="h-2 w-1/3 bg-zinc-100 rounded-full" />
                      <div className="h-3 w-full bg-zinc-100 rounded-full" />
                      <div className="h-3 w-2/3 bg-zinc-100 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : results.length > 0 ? (
              <div
                className={`grid gap-5 ${
                  viewMode === "grid"
                    ? "grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                    : "grid-cols-1"
                }`}
              >
                {results.map((document, i) => (
                  <Link
                    key={`doc-${document._id || i}`}
                    href={`/document/${document.slug}`}
                    className={`flex ${
                      viewMode === "grid" ? "flex-col" : "flex-row gap-5 p-3"
                    } border border-zinc-100 bg-white rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md hover:border-zinc-200`}
                  >
                    <div
                      className={`${
                        viewMode === "grid"
                          ? "aspect-[2/3] w-full border-b border-zinc-100"
                          : "w-20 h-28 shrink-0 rounded-xl"
                      } bg-zinc-100 relative overflow-hidden`}
                    >
                      {document.cover_url ? (
                        <img
                          src={document.cover_url}
                          alt={document.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full bg-zinc-100" />
                      )}
                    </div>

                    <div
                      className={`${
                        viewMode === "grid" ? "p-3" : "flex-1 py-0.5"
                      } flex flex-col flex-1 gap-1.5`}
                    >
                      {document.categories && document.categories.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {document.categories
                            .slice(0, 2)
                            .map((tag: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 text-[9px] font-bold text-zinc-400 bg-zinc-100 rounded-lg uppercase tracking-wide"
                              >
                                {tag}
                              </span>
                            ))}
                        </div>
                      )}

                      <h3
                        className={`${
                          viewMode === "grid" ? "text-xs" : "text-sm"
                        } font-semibold text-zinc-900 line-clamp-2 leading-snug`}
                      >
                        {document.title}
                      </h3>

                      <div className="text-[10px] text-zinc-400 flex items-center gap-1">
                        <span className="truncate font-medium text-zinc-600">
                          {document.author_name ||
                            document.author?.full_name ||
                            document.author?.username ||
                            "Ẩn danh"}
                        </span>
                        <span className="text-zinc-200">•</span>
                        <span className="shrink-0">
                          {document.created_at
                            ? new Date(document.created_at).toLocaleDateString(
                                "vi-VN",
                              )
                            : "Gần đây"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2.5 text-[10px] text-zinc-400">
                        <div className="flex items-center gap-0.5">
                          <Eye className="w-3 h-3" />
                          <span>
                            {document.views_count?.toLocaleString("vi-VN") ||
                              document.views ||
                              0}
                          </span>
                        </div>
                      </div>

                      <div
                        className={`mt-auto pt-2 flex items-center justify-between ${
                          viewMode === "grid" ? "border-t border-zinc-50" : ""
                        }`}
                      >
                        <span className="text-[10px] font-bold text-zinc-900">
                          {document.price_dl > 0
                            ? `${document.price_dl} dl`
                            : "Miễn phí"}
                        </span>
                        <span className="text-[9px] font-bold text-zinc-500 bg-zinc-100 px-2.5 py-1 rounded-xl uppercase tracking-widest">
                          Xem
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="py-20 flex flex-col items-center justify-center border border-zinc-100 bg-zinc-50 rounded-2xl gap-3">
                <BookOpen className="w-8 h-8 text-zinc-200 stroke-[1.5]" />
                <p className="text-xs font-medium text-zinc-400">
                  Chưa có kết quả nào phù hợp
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <SearchResultsContent />
    </Suspense>
  );
}
