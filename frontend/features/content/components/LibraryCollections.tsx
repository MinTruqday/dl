"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import { Button } from "@/shared/components/ui/Button";
import type { BookmarkFolder, ReadingList } from "../hooks/useLibrary";

export function FolderList({
  folders,
  processing,
  onDelete,
}: {
  folders: BookmarkFolder[];
  processing: boolean;
  onDelete: (id: string) => Promise<boolean>;
}) {
  if (!folders.length)
    return (
      <EmptyState
        text="Chưa có thư mục"
      />
    );
  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      {folders.map((folder) => {
        const id = folder._id || folder.id || "";
        return (
          <div
            key={id}
            className="flex min-h-16 items-center justify-between gap-4 border-b border-border px-4 py-3 last:border-b-0"
          >
            <div className="min-w-0">
              <p className="truncate font-semibold text-ink">
                {folder.name || "Thư mục chưa có tên"}
              </p>
              <p className="mt-1 text-[12px] text-ink-muted">
                {folder.bookmark_ids?.length || 0} dấu trang
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              disabled={processing}
              onClick={() => onDelete(id)}
            >
              Xóa
            </Button>
          </div>
        );
      })}
    </div>
  );
}

export function ReadingListRows({ lists }: { lists: ReadingList[] }) {
  if (!lists.length)
    return (
      <EmptyState
        text="Chưa có danh sách đọc"
      />
    );
  return (
    <div className="overflow-hidden rounded-panel border border-border bg-surface">
      {lists.map((list) => {
        const id = list._id || list.id || "";
        return (
          <Link
            key={id}
            href={`/thu-vien/danh-sach/${id}`}
            className="flex min-h-16 items-center justify-between gap-4 border-b border-border px-4 py-3 last:border-b-0 hover:bg-surface-raised"
          >
            <div className="min-w-0">
              <p className="truncate font-semibold text-ink">
                {list.name || "Danh sách chưa có tên"}
              </p>
              <p className="mt-1 truncate text-[12px] text-ink-muted">
                {list.description || `${list.documents?.length || 0} tài liệu`}
              </p>
            </div>
            <span className="shrink-0 text-[13px] font-semibold text-brand">
              Mở
            </span>
          </Link>
        );
      })}
    </div>
  );
}
