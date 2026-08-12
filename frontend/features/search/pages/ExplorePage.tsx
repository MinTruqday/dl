"use client";

import { Button } from "@/shared/components/ui/Button";
import DocumentResults from "@/shared/components/documents/DocumentResults";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import { useExploreDocuments } from "../hooks/useExploreDocuments";

export default function ExplorePage() {
  const {
    documents,
    recommendations,
    categories,
    category,
    setCategory,
    loading,
    error,
    reload,
  } = useExploreDocuments();

  return (
    <div className="w-full">
      <PageHeader
        title="Khám phá"
      />
      <div className="mb-7">
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

      {recommendations.length > 0 && (
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
            Tài liệu
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
        />
      </section>
    </div>
  );
}
