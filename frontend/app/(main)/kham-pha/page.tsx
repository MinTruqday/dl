"use client";

import { FormEvent } from "react";
import { Button } from "@/shared/components/ui/Button";
import DocumentResults from "@/app/_components/DocumentResults";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import { useExploreDocuments } from "./useExploreDocuments";

export default function ExplorePage() {
  const {
    documents,
    recommendations,
    categories,
    category,
    setCategory,
    query,
    setQuery,
    semantic,
    setSemantic,
    loading,
    error,
    reload,
  } = useExploreDocuments();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    reload();
  };

  return (
    <div className="w-full">
      <PageHeader
        title="Khám phá"
      />
      <form
        onSubmit={submit}
        className="mb-6 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]"
      >
        <div>
          <label htmlFor="explore-query" className="sr-only">
            Nội dung tìm kiếm
          </label>
          <input
            id="explore-query"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="apple-input w-full"
            placeholder="Tên tài liệu, tác giả hoặc nội dung"
          />
        </div>
        <Button type="submit" variant="secondary">
          Tìm kiếm
        </Button>
      </form>

      <div className="mb-7 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <input
            id="semantic-search"
            type="checkbox"
            checked={semantic}
            onChange={(event) => setSemantic(event.target.checked)}
            className="h-4 w-4 accent-[hsl(var(--brand))]"
          />
          <label
            htmlFor="semantic-search"
            className="text-[13px] font-medium text-ink"
          >
            Tìm theo ý nghĩa nội dung
          </label>
        </div>
        <SegmentedTabs
          label="Chọn chủ đề"
          value={category}
          onChange={setCategory}
          tabs={[
            { id: "all", label: "Tất cả" },
            ...categories.map((item) => ({ id: item, label: item })),
          ]}
        />
      </div>

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tải tài liệu"
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

      {!query && recommendations.length > 0 && (
        <section className="mb-9" aria-labelledby="recommendation-title">
          <h2
            id="recommendation-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Được đề xuất
          </h2>
          <DocumentResults documents={recommendations} compact />
        </section>
      )}

      <section aria-labelledby="catalog-title">
        <div className="mb-4 flex items-end justify-between gap-4">
          <h2 id="catalog-title" className="text-[18px] font-semibold text-ink">
            Tài liệu công khai
          </h2>
          {!loading && (
            <p className="text-[13px] text-ink-muted">
              {documents.length} kết quả
            </p>
          )}
        </div>
        <DocumentResults
          documents={documents}
          loading={loading}
          emptyDescription="Thử chủ đề khác hoặc thay nội dung tìm kiếm"
        />
      </section>
    </div>
  );
}
