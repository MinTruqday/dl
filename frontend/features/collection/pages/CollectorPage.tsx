"use client";

import { useState } from "react";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/shared/components/common/InlineState";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import PageHeader from "@/shared/components/layout/PageHeader";
import { useCollector } from "../hooks/useCollector";

const sources = [
  { id: "AnnaArchive", label: "Anna Archive" },
  { id: "NXBST", label: "Nhà xuất bản Sự thật" },
  { id: "NXBGD", label: "Nhà xuất bản Giáo dục" },
  { id: "CTAN", label: "CTAN" },
];

export default function CollectorPage() {
  const [source, setSource] = useState("");
  const [pages, setPages] = useState<number | string>(1);
  const collector = useCollector();

  if (collector.loading) return <PageLoader rows={5} />;
  if (!collector.allowed)
    return (
      <InlineState
        title="Không có quyền truy cập"
        detail="Trang này chỉ dành cho quản trị viên"
        tone="danger"
      />
    );

  const start = async () => {
    if (!source) return;
    await collector.start(source, pages);
  };

  return (
    <div className="w-full">
      <PageHeader
        title="Thu thập"
        actions={
          <Button variant="secondary" onClick={() => collector.reload()}>
            Làm mới
          </Button>
        }
      />
      {collector.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể đồng bộ dữ liệu"
            detail={collector.error}
            tone="danger"
          />
        </div>
      )}
      <MetricStrip
        items={[
          {
            label: "Đã thu thập",
            value: Number(
              collector.stats?.total_documents_collected || 0,
            ).toLocaleString("vi-VN"),
          },
          { label: "Đang chạy", value: collector.jobs.length },
          {
            label: "Trạng thái",
            value:
              collector.stats?.status === "operational"
                ? "Hoạt động"
                : collector.stats?.status === "paused"
                  ? "Tạm dừng"
                  : "Không sẵn sàng",
          },
          { label: "Bản ghi", value: collector.logs.length },
        ]}
      />
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {sources.map((item) => {
          const health = (collector.stats?.source_health || []).find(
            (row: any) => row.source === item.id,
          );
          return (
            <div
              key={item.id}
              className="rounded-panel border border-border bg-surface px-4 py-3"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-[13px] font-semibold text-ink">
                  {item.label}
                </p>
                <span
                  className={`text-[12px] font-semibold ${health?.reachable ? "text-brand" : "text-danger"}`}
                >
                  {health?.reachable ? "Sẵn sàng" : "Không sẵn sàng"}
                </span>
              </div>
              <p className="mt-1 text-[12px] text-ink-muted">
                Phát hiện {Number(health?.documents_detected || 0)}
              </p>
            </div>
          );
        })}
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[20rem_minmax(0,1fr)]">
        <section aria-labelledby="collector-form-title">
          <h2
            id="collector-form-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Nhiệm vụ mới
          </h2>
          <div className="space-y-5 rounded-panel border border-border bg-surface p-5">
            <div>
              <label
                htmlFor="collector-source"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Nguồn
              </label>
              <select
                id="collector-source"
                className="apple-input w-full"
                value={source}
                onChange={(event) => {
                  const value = event.target.value;
                  setSource(value);
                  setPages(value === "CTAN" ? "a" : 1);
                }}
              >
                <option value="">Chọn nguồn</option>
                {sources.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            {source === "CTAN" ? (
              <div>
                <label
                  htmlFor="collector-letter"
                  className="mb-2 block text-[13px] font-semibold text-ink"
                >
                  Chữ cái
                </label>
                <select
                  id="collector-letter"
                  className="apple-input w-full"
                  value={pages}
                  onChange={(event) => setPages(event.target.value)}
                >
                  {Array.from({ length: 26 }, (_, index) =>
                    String.fromCharCode(97 + index),
                  ).map((letter) => (
                    <option key={letter} value={letter}>
                      {letter.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            ) : source === "NXBGD" ? (
              <div>
                <label
                  htmlFor="collector-grade"
                  className="mb-2 block text-[13px] font-semibold text-ink"
                >
                  Lớp
                </label>
                <select
                  id="collector-grade"
                  className="apple-input w-full"
                  value={pages}
                  onChange={(event) => setPages(Number(event.target.value))}
                >
                  {Array.from({ length: 12 }, (_, index) => index + 1).map(
                    (grade) => (
                      <option key={grade} value={grade}>
                        {grade}
                      </option>
                    ),
                  )}
                </select>
              </div>
            ) : (
              <div>
                <label
                  htmlFor="collector-pages"
                  className="mb-2 block text-[13px] font-semibold text-ink"
                >
                  Số trang
                </label>
                <input
                  id="collector-pages"
                  type="number"
                  min={1}
                  max={100}
                  className="apple-input w-full"
                  value={pages}
                  onChange={(event) =>
                    setPages(
                      Math.max(
                        1,
                        Math.min(100, Number(event.target.value) || 1),
                      ),
                    )
                  }
                />
              </div>
            )}
            <Button
              className="w-full"
              onClick={start}
              disabled={!source || collector.processing}
            >
              {collector.processing ? "Đang xử lý" : "Bắt đầu"}
            </Button>
            {collector.jobs.length > 0 && (
              <Button
                className="w-full"
                variant="danger"
                onClick={collector.stop}
                disabled={collector.processing}
              >
                Dừng tiến trình
              </Button>
            )}
          </div>
          {collector.jobs.length > 0 && (
            <div className="mt-4 overflow-hidden rounded-panel border border-border bg-surface">
              {collector.jobs.map((job: any) => {
                const target =
                  job.source === "CTAN"
                    ? String(job.parameters?.pages || "").toUpperCase()
                    : String(job.parameters?.pages || 0);
                return (
                  <div
                    key={job.id}
                    className="border-b border-border px-4 py-3 text-[13px] last:border-b-0"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <span className="font-semibold text-ink">
                        {job.source} {target}
                      </span>
                      <span className="tabular-nums text-ink-muted">
                        {Number(job.progress || 0)}%
                      </span>
                    </div>
                    <div className="mt-1 flex gap-4 text-[12px] text-ink-faint">
                      <span>Phát hiện {Number(job.documents_detected || 0)}</span>
                      <span>Đã lưu {Number(job.completed_items || 0)}</span>
                      <span>Lỗi {Number(job.failed_items || 0)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section aria-labelledby="collector-log-title">
          <h2
            id="collector-log-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Nhật ký
          </h2>
          <div className="max-h-[34rem] min-h-72 overflow-y-auto rounded-panel border border-border bg-surface p-4 font-mono text-[12px] leading-relaxed text-ink-muted">
            {collector.logs.length ? (
              collector.logs.map((log, index) => (
                <p
                  key={`${index}-${log.slice(0, 18)}`}
                  className="border-b border-border py-2 last:border-b-0"
                >
                  {log}
                </p>
              ))
            ) : (
              <p className="font-sans text-[14px]">Chưa có bản ghi</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
