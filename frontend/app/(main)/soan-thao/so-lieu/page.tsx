"use client";

import { useEffect, useState } from "react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import { useDocumentStatistics } from "./useDocumentStatistics";
import DocumentWorkspaceNavigation from "../_components/DocumentWorkspaceNavigation";

const format = new Intl.NumberFormat("vi-VN");

export default function DocumentStatisticsPage() {
  const state = useDocumentStatistics();
  const [price, setPrice] = useState(0);
  useEffect(() => setPrice(state.selected?.price ?? 0), [state.selected]);
  if (state.loading) return <PageLoader rows={6} />;
  return (
    <div className="w-full">
      <DocumentWorkspaceNavigation />
      <PageHeader title="Số liệu tài liệu" />
      {state.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể xử lý số liệu"
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
      {state.notice && (
        <div className="mb-6">
          <InlineState
            title={state.notice}
            action={
              <Button variant="ghost" onClick={state.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}
      <MetricStrip
        items={[
          { label: "Lượt xem", value: format.format(state.data.total_views) },
          {
            label: "Doanh thu",
            value: `${format.format(state.data.total_revenue)} dl`,
          },
          {
            label: "Số dư",
            value: `${format.format(state.data.available_balance)} dl`,
          },
          { label: "Tài liệu", value: state.data.documents.length },
        ]}
      />
      <section className="mt-8">
        <h2 className="mb-3 text-[17px] font-semibold text-ink">
          Hiệu suất theo tài liệu
        </h2>
        {state.data.documents.length ? (
          <div className="overflow-x-auto rounded-panel border border-border bg-surface">
            <table className="w-full min-w-[680px] text-left">
              <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
                <tr>
                  <th className="px-4 py-3">Tài liệu</th>
                  <th className="px-4 py-3 text-right">Lượt xem</th>
                  <th className="px-4 py-3 text-right">Lượt mua</th>
                  <th className="px-4 py-3 text-right">Giá</th>
                  <th className="px-4 py-3 text-right">Doanh thu</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {state.data.documents.map((document) => (
                  <tr key={document.id} className="text-[14px]">
                    <td className="max-w-80 truncate px-4 py-3.5 font-semibold text-ink">
                      {document.title}
                    </td>
                    <td className="px-4 py-3.5 text-right text-ink-muted">
                      {format.format(document.views)}
                    </td>
                    <td className="px-4 py-3.5 text-right text-ink-muted">
                      {format.format(document.purchases)}
                    </td>
                    <td className="px-4 py-3.5 text-right text-ink-muted">
                      {format.format(document.price)} dl
                    </td>
                    <td className="px-4 py-3.5 text-right font-semibold text-ink">
                      {format.format(document.revenue)} dl
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => state.inspect(document)}
                      >
                        Chi tiết
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <InlineState
            title="Chưa có số liệu"
            detail="Xuất bản tài liệu để bắt đầu ghi nhận lượt đọc"
          />
        )}
      </section>
      <Modal
        isOpen={Boolean(state.selected)}
        onClose={() => state.setSelected(null)}
      >
        <ModalHeader>
          <ModalTitle>
            {state.selected?.title || "Chi tiết tài liệu"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          {state.processing && !state.analytics ? (
            <PageLoader rows={3} />
          ) : (
            <div className="space-y-5">
              <dl className="grid grid-cols-2 gap-3">
                {[
                  [
                    "Lượt xem",
                    state.analytics?.views ?? state.selected?.views ?? 0,
                  ],
                  ["Thời gian đọc", state.analytics?.avg_read_time ?? "0 phút"],
                  ["Lượt lưu", state.analytics?.saves ?? 0],
                  ["Bình luận", state.analytics?.comments ?? 0],
                  ["Số từ", state.academic?.word_count ?? 0],
                  ["Điểm dễ đọc", state.academic?.readability_score ?? 0],
                ].map(([label, value]) => (
                  <div
                    key={String(label)}
                    className="rounded-control bg-surface-quiet p-4"
                  >
                    <dt className="text-[12px] text-ink-muted">{label}</dt>
                    <dd className="mt-1 text-[18px] font-semibold text-ink">
                      {typeof value === "number" ? format.format(value) : value}
                    </dd>
                  </div>
                ))}
              </dl>
              <div>
                <label
                  htmlFor="document-price"
                  className="mb-2 block text-[13px] font-semibold text-ink"
                >
                  Giá bán bằng dl
                </label>
                <input
                  id="document-price"
                  type="number"
                  min={0}
                  value={price}
                  onChange={(event) => setPrice(Number(event.target.value))}
                  className="apple-input w-full"
                />
              </div>
            </div>
          )}
        </ModalContent>
        <ModalFooter>
          <Button variant="secondary" onClick={() => state.setSelected(null)}>
            Đóng
          </Button>
          <Button
            disabled={price < 0 || state.processing}
            onClick={() => state.setPrice(price)}
          >
            {state.processing ? "Đang lưu" : "Lưu giá"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
