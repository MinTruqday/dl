"use client";

import DocumentCard from "../DocumentCard";
import ExploreSkeleton from "../ExploreSkeleton";
import { useExplore } from "../useExplore";
import EmptyState from "@/shared/components/common/EmptyState";
import { LayoutGrid, List } from "lucide-react";

export default function ExplorePage() {
  const {
    documents,
    recommendations,
    categories,
    category,
    setCategory,
    view,
    setView,
    loading,
  } = useExplore();

  return (
    <div className="app-page">
      <header className="flex flex-col gap-5 border-b border-[var(--border)] pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="page-heading">Khám phá</h1>
          <p className="page-description mt-2">
            Đọc tài liệu được chia sẻ bởi cộng đồng DocLib
          </p>
        </div>
        <div className="flex rounded-[var(--radius-control)] bg-[var(--surface-quiet)] p-1">
          <button
            type="button"
            onClick={() => setView("grid")}
            className={`flex size-9 items-center justify-center rounded-[calc(var(--radius-control)-2px)] text-[13px] font-medium ${
              view === "grid"
                ? "bg-[var(--surface)] text-[var(--ink)] shadow-sm"
                : "text-[var(--ink-muted)]"
            }`}
          >
            <LayoutGrid aria-hidden="true" className="size-4" strokeWidth={1.75} />
            <span className="sr-only">Lưới</span>
          </button>
          <button
            type="button"
            onClick={() => setView("list")}
            className={`flex size-9 items-center justify-center rounded-[calc(var(--radius-control)-2px)] text-[13px] font-medium ${
              view === "list"
                ? "bg-[var(--surface)] text-[var(--ink)] shadow-sm"
                : "text-[var(--ink-muted)]"
            }`}
          >
            <List aria-hidden="true" className="size-4" strokeWidth={1.75} />
            <span className="sr-only">Danh sách</span>
          </button>
        </div>
      </header>

      <div className="hide-scrollbar mt-6 flex gap-2 overflow-x-auto pb-2">
        <button
          type="button"
          onClick={() => setCategory(null)}
          className={`min-h-9 shrink-0 rounded-full px-4 text-[13px] font-medium ${
            category === null
              ? "bg-[var(--brand)] text-white"
              : "border border-[var(--border)] bg-[var(--surface)] text-[var(--ink-muted)]"
          }`}
        >
          Tất cả
        </button>
        {categories.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setCategory(item === category ? null : item)}
            className={`min-h-9 shrink-0 rounded-full px-4 text-[13px] font-medium ${
              category === item
                ? "bg-[var(--brand)] text-white"
                : "border border-[var(--border)] bg-[var(--surface)] text-[var(--ink-muted)]"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {recommendations.length > 0 && category === null && (
        <section className="mt-9">
          <h2 className="text-[18px] font-semibold tracking-[-0.02em]">
            Gợi ý cho bạn
          </h2>
          <div className="mt-4 grid gap-5 md:grid-cols-2">
            {recommendations.slice(0, 4).map((document) => (
              <DocumentCard
                key={`recommendation-${document._id || document.slug}`}
                document={document}
                view="list"
              />
            ))}
          </div>
        </section>
      )}

      <section className="mt-10">
        <h2 className="mb-5 text-[18px] font-semibold tracking-[-0.02em]">
          {category || "Tài liệu mới"}
        </h2>
        {loading ? (
          <ExploreSkeleton />
        ) : documents.length > 0 ? (
          <div
            className={
              view === "grid"
                ? "grid gap-5 sm:grid-cols-2 xl:grid-cols-3"
                : "grid gap-3"
            }
          >
            {documents.map((document) => (
              <DocumentCard
                key={document._id || document.slug}
                document={document}
                view={view}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            text="Chưa có tài liệu"
            description="Thử chọn một chủ đề khác hoặc quay lại sau"
          />
        )}
      </section>
    </div>
  );
}
