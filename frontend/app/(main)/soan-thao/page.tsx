"use client";

import Link from "next/link";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import ComposerNavigation from "./_components/ComposerNavigation";
import { useComposerDocuments } from "./_hooks/useComposerDocuments";

function formatDate(value?: string) {
  if (!value) return "Chưa ghi nhận";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function ComposerPage() {
  const state = useComposerDocuments("drafts");

  return (
    <div className="w-full">
      <h1 className="sr-only">Soạn thảo</h1>
      <ComposerNavigation />
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <p className="text-[13px] text-ink-muted">
          Chọn định dạng trước khi tạo tài liệu
        </p>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/soan-thao/khoi-tao?dinh-dang=json"
            className="pill-button-secondary"
          >
            Tài liệu chuẩn
          </Link>
          <Link
            href="/soan-thao/khoi-tao?dinh-dang=latex"
            className="pill-button"
          >
            Tài liệu LaTeX
          </Link>
        </div>
      </div>

      <MetricStrip
        items={[
          { label: "Bản thảo", value: state.documents.length },
          {
            label: "Chuẩn",
            value: state.documents.filter(
              (document) => document.content_format !== "doclibx",
            ).length,
          },
          {
            label: "LaTeX",
            value: state.documents.filter(
              (document) => document.content_format === "doclibx",
            ).length,
          },
        ]}
      />

      {state.error && (
        <div className="mt-5">
          <InlineState
            title="Không thể tải bản thảo"
            detail={state.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={state.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      <section className="mt-6" aria-labelledby="draft-list-title">
        <div className="mb-3 flex items-center justify-between">
          <h2 id="draft-list-title" className="text-[14px] font-semibold text-ink">
            Bản thảo gần đây
          </h2>
          <Link href="/soan-thao/ban-thao" className="text-[13px] font-semibold text-brand">
            Xem tất cả
          </Link>
        </div>
        {state.loading ? (
          <PageLoader rows={5} />
        ) : state.documents.length ? (
          <div className="overflow-hidden border-y border-border bg-surface">
            {state.documents.slice(0, 8).map((document) => {
              const id = document._id || document.id || "";
              return (
                <Link
                  key={id}
                  href={`/soan-thao/chinh-sua?tai-lieu=${id}`}
                  className="grid min-h-16 gap-1 border-b border-border px-3 py-3 last:border-b-0 hover:bg-surface-quiet sm:grid-cols-[minmax(0,1fr)_8rem_12rem] sm:items-center sm:gap-4"
                >
                  <span className="truncate text-[14px] font-semibold text-ink">
                    {document.title || "Tài liệu chưa có tiêu đề"}
                  </span>
                  <span className="text-[12px] text-ink-muted">
                    {document.content_format === "doclibx" ? "LaTeX" : "Chuẩn"}
                  </span>
                  <span className="text-[12px] text-ink-muted sm:text-right">
                    {formatDate(document.updated_at || document.created_at)}
                  </span>
                </Link>
              );
            })}
          </div>
        ) : (
          <InlineState
            title="Chưa có bản thảo"
            detail="Chọn một định dạng để tạo tài liệu đầu tiên"
          />
        )}
      </section>
    </div>
  );
}
