"use client";

import Link from "next/link";
import InlineState from "@/shared/components/common/InlineState";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import PageLoader from "@/shared/components/common/PageLoader";
import PageHeader from "@/shared/components/layout/PageHeader";
import { Button } from "@/shared/components/ui/Button";
import ComposerNavigation from "../components/ComposerNavigation";
import { useComposerDocuments } from "../hooks/useComposerDocuments";

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
      <ComposerNavigation />
      <PageHeader
        title="Soạn thảo"
        actions={
          <Link href="/soan-thao/khoi-tao" className="pill-button">
            Tạo tài liệu
          </Link>
        }
      />

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
          <InlineState title="Chưa có bản thảo" />
        )}
      </section>
    </div>
  );
}
