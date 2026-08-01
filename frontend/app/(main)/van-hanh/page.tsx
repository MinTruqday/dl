"use client";

import { useState } from "react";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import QuotaEditor from "./QuotaEditor";
import { useOperations } from "./useOperations";

type Tab = "overview" | "quotas";

function formatBytes(value: number) {
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1,
  );
  return `${(value / 1024 ** index).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} ${units[index]}`;
}

function statusLabel(value?: string) {
  return ["healthy", "connected"].includes(String(value || "").toLowerCase())
    ? "Hoạt động"
    : "Không sẵn sàng";
}

export default function OperationsPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const operations = useOperations();

  if (operations.loading) return <PageLoader rows={6} />;
  if (!operations.allowed)
    return (
      <InlineState
        title="Không có quyền truy cập"
        detail="Trang này chỉ dành cho quản trị viên"
        tone="danger"
      />
    );

  return (
    <div className="w-full">
      <PageHeader
        title="Vận hành"
        actions={
          <Button variant="secondary" onClick={operations.reload}>
            Làm mới
          </Button>
        }
      />
      {operations.error && (
        <div className="mb-6">
          <InlineState
            title="Một phần dữ liệu chưa sẵn sàng"
            detail={operations.error}
            tone="danger"
          />
        </div>
      )}
      {operations.notice && (
        <div className="mb-6">
          <InlineState title={operations.notice} />
        </div>
      )}
      <div className="mb-6">
        <SegmentedTabs<Tab>
          label="Nội dung vận hành"
          value={tab}
          onChange={setTab}
          tabs={[
            { id: "overview", label: "Tổng quan" },
            { id: "quotas", label: "Hạn mức AI" },
          ]}
        />
      </div>

      {tab === "overview" ? (
        <div className="space-y-8">
          <MetricStrip
            items={[
              {
                label: "Người dùng",
                value: Number(
                  operations.metrics.total_users || 0,
                ).toLocaleString("vi-VN"),
              },
              {
                label: "Tác giả",
                value: Number(
                  operations.metrics.total_authors || 0,
                ).toLocaleString("vi-VN"),
              },
              {
                label: "Tài liệu",
                value: Number(
                  operations.metrics.total_documents || 0,
                ).toLocaleString("vi-VN"),
              },
              {
                label: "Tải CPU",
                value: operations.health.resources?.cpu_load || "Chưa có",
              },
            ]}
          />

          <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <section aria-labelledby="service-health-title">
              <h2
                id="service-health-title"
                className="mb-4 text-[18px] font-semibold text-ink"
              >
                Dịch vụ
              </h2>
              <div className="overflow-hidden rounded-panel border border-border bg-surface">
                {[
                  { label: "Hệ thống", value: operations.health.status },
                  {
                    label: "Cơ sở dữ liệu",
                    value: operations.health.services?.database,
                  },
                  {
                    label: "Bộ nhớ đệm",
                    value: operations.health.services?.cache,
                  },
                  {
                    label: "Dịch vụ AI",
                    value: operations.health.services?.ai_agent,
                  },
                  { label: "Kho tệp", value: operations.storage.status },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="flex min-h-14 items-center justify-between gap-4 border-b border-border px-4 py-3 last:border-b-0"
                  >
                    <span className="font-medium text-ink">{item.label}</span>
                    <span
                      className={`text-[13px] font-semibold ${statusLabel(item.value) === "Hoạt động" ? "text-brand" : "text-danger"}`}
                    >
                      {statusLabel(item.value)}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section aria-labelledby="operation-actions-title">
              <h2
                id="operation-actions-title"
                className="mb-4 text-[18px] font-semibold text-ink"
              >
                Điều khiển
              </h2>
              <div className="space-y-4 rounded-panel border border-border bg-surface p-5">
                <div>
                  <p className="font-semibold text-ink">Đăng ký tài khoản</p>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    {operations.config.registration_enabled
                      ? "Đang mở"
                      : "Đang đóng"}
                  </p>
                  <Button
                    className="mt-3 w-full"
                    variant="secondary"
                    onClick={operations.toggleRegistration}
                    disabled={Boolean(operations.processing)}
                  >
                    {operations.processing === "registration"
                      ? "Đang cập nhật"
                      : operations.config.registration_enabled
                        ? "Đóng đăng ký"
                        : "Mở đăng ký"}
                  </Button>
                </div>
                <div className="border-t border-border pt-4">
                  <p className="font-semibold text-ink">Chế độ bảo trì</p>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    {operations.maintenance ? "Đang bật" : "Đang tắt"}
                  </p>
                  <Button
                    className="mt-3 w-full"
                    variant={operations.maintenance ? "danger" : "secondary"}
                    onClick={operations.toggleMaintenance}
                    disabled={Boolean(operations.processing)}
                  >
                    {operations.processing === "maintenance"
                      ? "Đang cập nhật"
                      : operations.maintenance
                        ? "Tắt bảo trì"
                        : "Bật bảo trì"}
                  </Button>
                </div>
                <div className="border-t border-border pt-4">
                  <p className="font-semibold text-ink">Sao lưu dữ liệu</p>
                  <Button
                    className="mt-3 w-full"
                    variant="secondary"
                    onClick={operations.backup}
                    disabled={Boolean(operations.processing)}
                  >
                    {operations.processing === "backup"
                      ? "Đang khởi chạy"
                      : "Khởi chạy sao lưu"}
                  </Button>
                </div>
              </div>
            </section>
          </div>

          <section aria-labelledby="storage-title">
            <h2
              id="storage-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Lưu trữ
            </h2>
            <MetricStrip
              items={[
                {
                  label: "Dung lượng",
                  value: formatBytes(
                    Number(operations.storage.total_size_bytes || 0),
                  ),
                },
                {
                  label: "Tệp",
                  value: Number(
                    operations.storage.total_objects_count || 0,
                  ).toLocaleString("vi-VN"),
                },
                {
                  label: "Bucket",
                  value: Number(
                    operations.storage.total_buckets ||
                      operations.storage.buckets?.length ||
                      0,
                  ).toLocaleString("vi-VN"),
                },
                {
                  label: "Thời gian chạy",
                  value: `${Math.floor(Number(operations.health.resources?.uptime_seconds || 0) / 3600)} giờ`,
                },
              ]}
            />
          </section>
        </div>
      ) : (
        <section aria-labelledby="quota-title">
          <h2
            id="quota-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Hạn mức theo gói
          </h2>
          <QuotaEditor
            quotas={operations.quotas}
            processing={operations.processing}
            onSave={operations.updateQuota}
          />
        </section>
      )}
    </div>
  );
}
