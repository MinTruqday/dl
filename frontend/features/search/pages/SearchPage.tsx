"use client";

import Link from "next/link";
import { Suspense } from "react";
import { Button } from "@/shared/components/ui/Button";
import DocumentResults from "@/shared/components/documents/DocumentResults";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import { useDocumentSearch } from "../hooks/useDocumentSearch";

function SearchResultsContent() {
  const {
    query,
    documents,
    history,
    filters,
    setFilters,
    loading,
    error,
    reload,
    clearHistory,
  } = useDocumentSearch();

  return (
    <div className="w-full">
      <PageHeader
        title="Tìm kiếm"
        description={
          query
            ? `Kết quả cho ${query}`
            : "Nhập từ khóa trong thanh tìm kiếm phía trên"
        }
        meta={query && !loading ? `${documents.length} kết quả` : undefined}
      />

      {query && (
        <div className="mb-6 grid gap-4 rounded-panel border border-border bg-surface px-4 py-4 sm:grid-cols-3">
          <div>
            <label
              htmlFor="search-sort"
              className="mb-2 block text-[12px] font-semibold text-ink-muted"
            >
              Sắp xếp
            </label>
            <select
              id="search-sort"
              className="apple-input w-full"
              value={filters.sort}
              onChange={(event) =>
                setFilters({
                  ...filters,
                  sort: event.target.value as typeof filters.sort,
                })
              }
            >
              <option value="latest">Mới nhất</option>
              <option value="most_viewed">Xem nhiều nhất</option>
            </select>
          </div>
          <div>
            <label
              htmlFor="search-time"
              className="mb-2 block text-[12px] font-semibold text-ink-muted"
            >
              Thời gian
            </label>
            <select
              id="search-time"
              className="apple-input w-full"
              value={filters.time}
              onChange={(event) =>
                setFilters({
                  ...filters,
                  time: event.target.value as typeof filters.time,
                })
              }
            >
              <option value="all">Tất cả</option>
              <option value="day">24 giờ</option>
              <option value="week">7 ngày</option>
              <option value="month">30 ngày</option>
            </select>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tìm tài liệu"
            detail={error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      {!query && history.length > 0 ? (
        <section aria-labelledby="history-title">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2
              id="history-title"
              className="text-[18px] font-semibold text-ink"
            >
              Tìm kiếm gần đây
            </h2>
            <button
              type="button"
              onClick={clearHistory}
              className="text-[13px] font-semibold text-danger hover:underline"
            >
              Xóa lịch sử
            </button>
          </div>
          <div className="overflow-hidden rounded-panel border border-border bg-surface">
            {history.map((item) => (
              <Link
                key={item}
                href={`/tim-kiem?q=${encodeURIComponent(item)}`}
                className="block border-b border-border px-4 py-3.5 font-medium text-ink last:border-b-0 hover:bg-surface-raised"
              >
                {item}
              </Link>
            ))}
          </div>
        </section>
      ) : (
        <DocumentResults
          documents={documents}
          loading={loading}
          emptyTitle={query ? "Không tìm thấy tài liệu" : "Chưa có tìm kiếm"}
        />
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<DocumentResults documents={[]} loading />}>
      <SearchResultsContent />
    </Suspense>
  );
}
