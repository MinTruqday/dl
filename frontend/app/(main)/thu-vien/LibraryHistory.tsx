"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import { Button } from "@/shared/components/ui/Button";
import type { ReadingHistoryItem } from "./useLibrary";

type LibraryHistoryProps = {
  history: ReadingHistoryItem[];
  processing: boolean;
  onDelete: (id: string) => Promise<boolean>;
  onClear: () => void;
};

function formatDate(value?: string) {
  if (!value) return "Chưa ghi nhận";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Chưa ghi nhận"
    : new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

export default function LibraryHistory({
  history,
  processing,
  onDelete,
  onClear,
}: LibraryHistoryProps) {
  if (!history.length)
    return (
      <EmptyState
        text="Chưa có lịch sử đọc"
        description="Tài liệu đã mở sẽ xuất hiện tại đây"
        actionLabel="Khám phá tài liệu"
        actionHref="/kham-pha"
      />
    );

  return (
    <section aria-labelledby="reading-history-title">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2
          id="reading-history-title"
          className="text-[18px] font-semibold text-ink"
        >
          Lịch sử đọc
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClear}
          disabled={processing}
        >
          Xóa lịch sử
        </Button>
      </div>
      <div className="overflow-hidden rounded-panel border border-border bg-surface">
        {history.map((item) => (
          <div
            key={item.document_id}
            className="grid gap-3 border-b border-border px-4 py-4 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_9rem_6rem] sm:items-center"
          >
            <div className="min-w-0">
              <Link
                href={`/tai-lieu/${item.document_slug || item.document_id}`}
                className="block truncate font-semibold text-ink hover:text-brand"
              >
                {item.document_title || "Tài liệu chưa có tiêu đề"}
              </Link>
              <p className="mt-1 text-[12px] text-ink-muted">
                Đã đọc {Math.round(Number(item.progress_percentage || 0))}%
              </p>
            </div>
            <time className="text-[12px] text-ink-muted">
              {formatDate(item.last_read_at)}
            </time>
            <div className="flex sm:justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(item.document_id)}
                disabled={processing}
              >
                Xóa
              </Button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
