"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import { useComposerDocuments } from "../_hooks/useComposerDocuments";
import ComposerNavigation from "./ComposerNavigation";

type ComposerDocumentListProps = {
  source: "drafts" | "trash";
};

function formatDate(value?: string) {
  if (!value) return "Chưa ghi nhận";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Chưa ghi nhận";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function ComposerDocumentList({
  source,
}: ComposerDocumentListProps) {
  const { documents, loading, error, restoringId, reload, restore } =
    useComposerDocuments(source);
  const isTrash = source === "trash";

  if (loading) return <PageLoader rows={5} />;

  return (
    <div className="w-full">
      <ComposerNavigation />
      <PageHeader
        title={isTrash ? "Thùng rác" : "Bản thảo"}
        description={
          isTrash
            ? "Tài liệu đã xóa có thể được khôi phục"
            : "Tài liệu đang được biên tập và chưa xuất bản"
        }
        actions={
          !isTrash && (
            <Link href="/soan-thao/khoi-tao" className="pill-button">
              Tạo tài liệu
            </Link>
          )
        }
        meta={`${documents.length} tài liệu`}
      />

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể hoàn tất yêu cầu"
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

      {documents.length === 0 ? (
        <EmptyState
          text={isTrash ? "Thùng rác đang trống" : "Chưa có bản thảo"}
          description={
            isTrash
              ? "Tài liệu đã xóa sẽ xuất hiện tại đây"
              : "Tạo tài liệu mới để bắt đầu biên tập"
          }
          actionLabel={isTrash ? undefined : "Tạo tài liệu"}
          actionHref={isTrash ? undefined : "/soan-thao/khoi-tao"}
        />
      ) : (
        <div className="overflow-hidden rounded-panel border border-border bg-surface">
          <div className="hidden min-h-11 grid-cols-[minmax(0,1fr)_12rem_8rem] items-center gap-4 border-b border-border bg-surface-quiet px-4 text-[12px] font-semibold text-ink-muted sm:grid">
            <span>Tài liệu</span>
            <span>Cập nhật</span>
            <span className="text-right">Thao tác</span>
          </div>
          <div className="divide-y divide-border">
            {documents.map((document) => {
              const id = document._id || document.id || "";
              return (
                <div
                  key={id}
                  className="grid min-h-16 gap-3 px-4 py-3 sm:grid-cols-[minmax(0,1fr)_12rem_8rem] sm:items-center sm:gap-4"
                >
                  <div className="min-w-0">
                    {isTrash ? (
                      <p className="truncate font-semibold text-ink">
                        {document.title || "Tài liệu chưa có tiêu đề"}
                      </p>
                    ) : (
                      <Link
                        href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                        className="block truncate font-semibold text-ink hover:text-brand"
                      >
                        {document.title || "Tài liệu chưa có tiêu đề"}
                      </Link>
                    )}
                    <p className="mt-1 text-[12px] text-ink-faint sm:hidden">
                      {formatDate(document.updated_at || document.created_at)}
                    </p>
                  </div>
                  <p className="hidden text-[13px] text-ink-muted sm:block">
                    {formatDate(document.updated_at || document.created_at)}
                  </p>
                  <div className="flex justify-start sm:justify-end">
                    {isTrash ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={restoringId === id}
                        onClick={() => restore(id)}
                      >
                        {restoringId === id ? "Đang khôi phục" : "Khôi phục"}
                      </Button>
                    ) : (
                      <Link
                        href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                        className="inline-flex min-h-9 items-center rounded-control px-3 text-[13px] font-semibold text-brand hover:bg-brand-soft"
                      >
                        Mở
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
