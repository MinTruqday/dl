"use client";

import Link from "next/link";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import { useAuthorAnalytics } from "./useAuthorAnalytics";

const number = new Intl.NumberFormat("vi-VN");

export default function AuthorAnalyticsPage() {
  const { data, loading, error, reload } = useAuthorAnalytics();

  if (loading) return <PageLoader rows={4} />;

  return (
    <div className="w-full">
      <PageHeader
        title="Phân tích"
        actions={
          <Link href="/soan-thao" className="secondary-button">
            Quản lý bản thảo
          </Link>
        }
      />

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tải số liệu"
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

      <MetricStrip
        items={[
          { label: "Lượt xem", value: number.format(data.total_views) },
          {
            label: "Lượt mua",
            value: number.format(
              data.documents.reduce((sum, item) => sum + item.purchases, 0),
            ),
          },
          {
            label: "Doanh thu",
            value: `${number.format(data.total_revenue)} dl`,
          },
          {
            label: "Số dư",
            value: `${number.format(data.available_balance)} dl`,
          },
        ]}
      />

      <section className="mt-8" aria-labelledby="document-performance">
        <div className="mb-3 flex items-end justify-between gap-4">
          <h2
            id="document-performance"
            className="text-[18px] font-semibold text-ink"
          >
            Theo tài liệu
          </h2>
          <p className="text-[13px] text-ink-muted">
            {number.format(data.documents.length)} tài liệu
          </p>
        </div>

        {data.documents.length === 0 ? (
          <EmptyState
            text="Chưa có số liệu tài liệu"
            description="Xuất bản tài liệu đầu tiên để bắt đầu ghi nhận lượt xem và lượt mua"
            actionLabel="Mở trình soạn thảo"
            actionHref="/soan-thao/khoi-tao"
          />
        ) : (
          <div className="overflow-x-auto rounded-panel border border-border bg-surface">
            <table className="w-full min-w-[680px] border-collapse text-left">
              <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
                <tr>
                  <th className="px-4 py-3">Tài liệu</th>
                  <th className="px-4 py-3 text-right">Lượt xem</th>
                  <th className="px-4 py-3 text-right">Lượt mua</th>
                  <th className="px-4 py-3 text-right">Giá</th>
                  <th className="px-4 py-3 text-right">Doanh thu</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.documents.map((document) => (
                  <tr
                    key={document.id}
                    className="text-[14px] hover:bg-surface-raised"
                  >
                    <td className="max-w-[28rem] px-4 py-3.5 font-medium text-ink">
                      <Link
                        href={`/tai-lieu/${document.slug || document.id}`}
                        className="block truncate hover:text-brand"
                      >
                        {document.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums text-ink-muted">
                      {number.format(document.views)}
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums text-ink-muted">
                      {number.format(document.purchases)}
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums text-ink-muted">
                      {number.format(document.price)} dl
                    </td>
                    <td className="px-4 py-3.5 text-right tabular-nums font-semibold text-ink">
                      {number.format(document.revenue)} dl
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
