"use client";
import React, { useCallback, useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/features/content/services/document.service";
import {
  Filter,
  Clock,
  X,
  ArrowUpDown,
  BookOpen,
  Eye,
  LayoutGrid,
  List as ListIcon,
  List,
} from "lucide-react";
import PageHeader from "@/shared/components/common/PageHeader";

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

  const saveToHistory = useCallback((q: string) => {
    setHistory((current) => {
      const updated = [q, ...current.filter((item) => item !== q)].slice(0, 10);
      localStorage.setItem("doclib_search_history", JSON.stringify(updated));
      return updated;
    });
  }, []);
  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("doclib_search_history");
  };

  const loadResults = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getDocumentsAPI(query);
      let filtered = data || [];
      if (filters.price === "free")
        filtered = filtered.filter((b: any) => !b.price_dl || b.price_dl === 0);
      if (filters.price === "paid")
        filtered = filtered.filter((b: any) => b.price_dl > 0);

      const now = new Date();
      if (filters.time === "today")
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setDate(now.getDate() - 1)),
        );
      else if (filters.time === "this_week")
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setDate(now.getDate() - 7)),
        );
      else if (filters.time === "this_month")
        filtered = filtered.filter(
          (b: any) =>
            new Date(b.created_at) > new Date(now.setMonth(now.getMonth() - 1)),
        );

      if (filters.sort === "most_viewed")
        filtered.sort((a: any, b: any) => (b.views || 0) - (a.views || 0));
      else
        filtered.sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );

      setResults(filtered);
    } catch (err: any) {
      console.error("Error executing document search query:", err);
    } finally {
      setLoading(false);
    }
  }, [filters, query]);

  useEffect(() => {
    if (query) {
      loadResults();
      saveToHistory(query);
    }
  }, [loadResults, query, saveToHistory]);

  return (
    <div className="app-page gap-6">
      <PageHeader title="Tìm kiếm" />
      <div className="flex flex-col md:flex-row gap-6">
        <aside className="w-full md:w-[320px] shrink-0 space-y-6">
          <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
            <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
              Giao diện
            </p>
            <div className="flex bg-[var(--border)] p-0.5 rounded-full shrink-0">
              <button
                onClick={() => setViewMode("grid")}
                className={`p-1.5 rounded-full transition-colors ${viewMode === "grid" ? "bg-white text-[var(--brand)] font-medium" : "text-[var(--ink-muted)] hover:text-[var(--ink)]"}`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`p-1.5 rounded-full transition-colors ${viewMode === "list" ? "bg-white text-[var(--brand)] font-medium" : "text-[var(--ink-muted)] hover:text-[var(--ink)]"}`}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6">
            <div className="flex items-center justify-between mb-6">
              <span className="text-[15px] font-semibold text-[var(--ink)]">
                Bộ lọc nâng cao
              </span>
            </div>

            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink-muted)] block mb-2">
                  Sắp xếp theo
                </label>
                <div className="flex flex-col gap-1">
                  {[
                    { id: "newest", label: "Mới nhất" },
                    { id: "most_viewed", label: "Xem nhiều nhất" },
                  ].map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setFilters({ ...filters, sort: s.id })}
                      className={`flex items-center justify-between px-3 py-2 text-[14px] rounded-[var(--radius-control)] transition-colors ${filters.sort === s.id ? "bg-white text-[var(--brand)] font-medium" : "text-[var(--ink)] hover:bg-[var(--border)]"}`}
                    >
                      <span>{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink-muted)] block mb-2">
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
                      className={`flex items-center justify-between px-3 py-2 text-[14px] rounded-[var(--radius-control)] transition-colors ${filters.time === t.id ? "bg-white text-[var(--brand)] font-medium" : "text-[var(--ink)] hover:bg-[var(--border)]"}`}
                    >
                      <span>{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink-muted)] block mb-2">
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
                      className={`flex items-center justify-between px-3 py-2 text-[14px] rounded-[var(--radius-control)] transition-colors ${filters.price === p.id ? "bg-white text-[var(--brand)] font-medium" : "text-[var(--ink)] hover:bg-[var(--border)]"}`}
                    >
                      <span>{p.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {history.length > 0 && (
            <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[15px] font-semibold text-[var(--ink)]">
                  Tìm kiếm gần đây
                </span>
                <button
                  onClick={clearHistory}
                  className="text-[13px] text-[var(--brand)] hover:underline font-medium"
                >
                  Xóa lịch sử
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <div key={h} className="group relative">
                    <Link
                      href={`/tim-kiem?q=${h}`}
                      className="block text-[13px] font-medium px-4 py-2 bg-[var(--surface-quiet)] text-[var(--ink)] rounded-full pr-8 hover:bg-[var(--border)] transition-colors"
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
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--ink-muted)] opacity-0 group-hover:opacity-100 hover:text-[var(--danger)] transition-opacity"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <main className="flex-1 min-w-0">
          {loading ? (
            <div
              className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-2 md:grid-cols-3 lg:grid-cols-4" : "grid-cols-1"}`}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                <div
                  key={i}
                  className={`flex ${viewMode === "grid" ? "flex-col" : "flex-row gap-6 p-4"} bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] overflow-hidden animate-pulse`}
                >
                  <div
                    className={`bg-[var(--border)] ${viewMode === "grid" ? "aspect-[3/4] w-full" : "w-24 h-32 shrink-0 rounded-[var(--radius-control)]"}`}
                  />
                  <div
                    className={`${viewMode === "grid" ? "p-4" : "flex-1"} space-y-3`}
                  >
                    <div className="h-3 w-1/3 bg-[var(--border)] rounded-full" />
                    <div className="h-4 w-full bg-[var(--border)] rounded-full" />
                    <div className="h-4 w-2/3 bg-[var(--border)] rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : results.length > 0 ? (
            <div
              className={`grid gap-6 ${viewMode === "grid" ? "grid-cols-2 md:grid-cols-3 lg:grid-cols-4" : "grid-cols-1"}`}
            >
              {results.map((document, i) => (
                <Link
                  key={`doc-${document._id || i}`}
                  href={`/tai-lieu/${document.slug}`}
                  className={`flex ${viewMode === "grid" ? "flex-col" : "flex-row gap-6 p-4 items-center"} bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] overflow-hidden transition-transform hover:scale-[1.02]`}
                >
                  <div
                    className={`${viewMode === "grid" ? "aspect-[4/3] w-full" : "w-[120px] h-[120px] shrink-0 rounded-[var(--radius-control)]"} bg-white relative overflow-hidden`}
                  >
                    {document.cover_url ? (
                      <img
                        src={document.cover_url}
                        alt={document.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-white" />
                    )}
                  </div>
                  <div
                    className={`${viewMode === "grid" ? "p-5" : "flex-1"} flex flex-col gap-2`}
                  >
                    {document.categories && document.categories.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-1">
                        {document.categories
                          .slice(0, 2)
                          .map((tag: string, idx: number) => (
                            <span
                              key={idx}
                              className="text-[12px] font-medium text-[var(--brand)]"
                            >
                              {tag}
                            </span>
                          ))}
                      </div>
                    )}
                    <h3
                      className={`${viewMode === "grid" ? "text-[17px]" : "text-[17px]"} font-medium text-[var(--ink)] line-clamp-2 leading-snug`}
                    >
                      {document.title}
                    </h3>
                    <div className="text-[13px] text-[var(--ink-muted)] flex items-center gap-2">
                      <span className="truncate">
                        {document.author_name ||
                          document.author?.full_name ||
                          document.author?.username ||
                          "Ẩn danh"}
                      </span>
                      <span>•</span>
                      <span className="shrink-0">
                        {document.created_at
                          ? new Date(document.created_at).toLocaleDateString(
                              "vi-VN",
                            )
                          : "Gần đây"}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-[13px] text-[var(--ink-muted)] mt-1">
                      <span className="flex items-center gap-1.5">
                        <Eye className="w-3.5 h-3.5" />{" "}
                        {document.views_count?.toLocaleString("vi-VN") ||
                          document.views ||
                          0}
                      </span>
                    </div>
                    <div className="mt-4 pt-4 flex items-center justify-between">
                      <span className="text-[15px] font-medium text-[var(--ink)]">
                        {document.price_dl > 0
                          ? `${document.price_dl} dl`
                          : "Miễn phí"}
                      </span>
                      <span className="text-[15px] text-[var(--brand)] font-medium">
                        Xem chi tiết
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="py-32 flex flex-col items-center justify-center bg-[var(--surface-quiet)] rounded-[var(--radius-panel)]">
              <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4">
                <BookOpen className="w-8 h-8 text-[var(--border-strong)]" />
              </div>
              <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4 mb-2">
                Chưa có kết quả
              </p>
              <p className="text-[17px] text-[var(--ink-muted)]">
                Thử thay đổi từ khóa hoặc bộ lọc để tìm kiếm lại.
              </p>
            </div>
          )}
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
