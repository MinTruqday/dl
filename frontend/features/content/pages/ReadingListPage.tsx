"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import { useReadingList } from "../hooks/useReadingList";

export default function ReadingListPage() {
  const id = String(useParams<{ id: string }>().id || "");
  const { list, loading, removing, error, reload, remove } = useReadingList(id);

  if (loading) return <PageLoader rows={5} />;

  const documents = list?.documents_detailed || [];

  return (
    <div className="w-full">
      <PageHeader
        title={list?.name || "Danh sách đọc"}
        showTitle
        description={list?.description || undefined}
        meta={`${documents.length} tài liệu`}
        actions={
          <Link href="/thu-vien" className="secondary-button">
            Về thư viện
          </Link>
        }
      />
      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể cập nhật danh sách"
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
      {!documents.length ? (
        <EmptyState
          text="Danh sách đang trống"
          actionLabel="Khám phá tài liệu"
          actionHref="/kham-pha"
        />
      ) : (
        <div className="overflow-hidden rounded-panel border border-border bg-surface">
          {documents.map((document) => {
            const documentId = document._id || document.id || "";
            return (
              <div
                key={documentId}
                className="grid min-h-16 gap-3 border-b border-border px-4 py-3 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_7rem] sm:items-center"
              >
                <div className="min-w-0">
                  <Link
                    href={`/tai-lieu/${document.slug || documentId}`}
                    className="block truncate font-semibold text-ink hover:text-brand"
                  >
                    {document.title || "Tài liệu chưa có tiêu đề"}
                  </Link>
                  <p className="mt-1 truncate text-[12px] text-ink-muted">
                    {document.author_name ||
                      document.author?.full_name ||
                      "Chưa rõ tác giả"}
                  </p>
                </div>
                <div className="flex sm:justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={Boolean(removing)}
                    onClick={() => remove(documentId)}
                  >
                    {removing === documentId ? "Đang gỡ" : "Gỡ"}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
