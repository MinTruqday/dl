"use client";

import { useCallback, useEffect, useState } from "react";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import { useToast } from "@/shared/contexts/ToastContext";
import EmptyState from "@/shared/components/common/EmptyState";
import PageHeader from "@/shared/components/common/PageHeader";
import PageSkeleton from "@/shared/components/common/PageSkeleton";

type DocumentSummary = {
  views?: number;
  rating_count?: number;
  revenue?: number;
};

export default function AuthorAnalyticsPage() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDocuments = useCallback(async () => {
    try {
      const response = await getMyDocumentsAPI();
      setDocuments(response.data || response || []);
    } catch {
      showToast("Không thể tải dữ liệu phân tích", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  if (loading) {
    return <PageSkeleton />;
  }

  const metrics = [
    {
      label: "Tác phẩm",
      value: documents.length,
    },
    {
      label: "Lượt xem",
      value: documents.reduce((total, item) => total + (item.views || 0), 0),
    },
    {
      label: "Lượt đánh giá",
      value: documents.reduce(
        (total, item) => total + (item.rating_count || 0),
        0,
      ),
    },
    {
      label: "Doanh thu",
      value: documents.reduce((total, item) => total + (item.revenue || 0), 0),
    },
  ];

  return (
    <div className="app-page gap-6">
      <PageHeader title="Phân tích" />
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <article className="surface p-5" key={metric.label}>
            <p className="text-[13px] font-medium text-[var(--ink-muted)]">
              {metric.label}
            </p>
            <p className="mt-3 text-[28px] font-semibold tracking-[-0.03em] text-[var(--ink)]">
              {metric.value.toLocaleString("vi-VN")}
            </p>
          </article>
        ))}
      </section>
      <EmptyState
        text="Chưa có dữ liệu theo thời gian"
        description="Biểu đồ sẽ xuất hiện khi tài liệu có lượt đọc hoặc giao dịch"
      />
    </div>
  );
}
