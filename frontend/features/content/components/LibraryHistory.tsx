"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import { Button } from "@/shared/components/ui/Button";
import type { ReadingHistoryItem } from "../hooks/useLibrary";

type LibraryHistoryProps = {
  history: ReadingHistoryItem[];
  processing: boolean;
  onDelete: (id: string) => Promise<boolean>;
};

function formatDate(value?: string) {
  if (!value) return "Chưa có thông tin";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Chưa có thông tin"
    : new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

export default function LibraryHistory({
  history,
  processing,
  onDelete,
}: LibraryHistoryProps) {
  if (!history.length)
    return (
      <EmptyState
        text="Chưa có thông tin"
        actionLabel="Khám phá tài liệu"
        actionHref="/kham-pha"
      />
    );

  return (
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
                {item.document_title || "Chưa có thông tin"}
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
  );
}
