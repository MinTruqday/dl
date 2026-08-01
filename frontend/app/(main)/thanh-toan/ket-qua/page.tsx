"use client";

import Link from "next/link";
import { Suspense } from "react";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import { usePaymentResult } from "./usePaymentResult";

const money = new Intl.NumberFormat("vi-VN");

function PaymentResultContent() {
  const { status, data, error, verify } = usePaymentResult();

  if (status === "loading") return <PageLoader compact rows={2} />;

  const title =
    status === "success"
      ? "Nạp tiền hoàn tất"
      : status === "cancelled"
        ? "Giao dịch đã hủy"
        : "Không thể xác nhận giao dịch";
  const detail =
    status === "success"
      ? "Số dư ví đã được cập nhật theo kết quả từ cổng thanh toán"
      : status === "cancelled"
        ? "Giao dịch không làm thay đổi số dư ví"
        : error || "Cổng thanh toán chưa xác nhận giao dịch";
  const amount = Number(data?.amount_paid || data?.amount || 0);
  const credit = Number(data?.dl || 0);

  return (
    <div className="mx-auto w-full max-w-2xl">
      <PageHeader title={title} description={detail} showTitle />
      <InlineState
        title={
          status === "success"
            ? "Đã xác nhận"
            : status === "cancelled"
              ? "Đã hủy"
              : "Chưa xác nhận"
        }
        tone={status === "failed" ? "danger" : "neutral"}
      />

      {data && (
        <dl className="mt-6 overflow-hidden rounded-panel border border-border bg-surface">
          <div className="flex items-center justify-between gap-6 border-b border-border px-5 py-4">
            <dt className="text-[13px] text-ink-muted">Mã giao dịch</dt>
            <dd className="truncate font-mono text-[13px] font-semibold text-ink">
              {data.order_code || "Chưa có"}
            </dd>
          </div>
          <div className="flex items-center justify-between gap-6 border-b border-border px-5 py-4">
            <dt className="text-[13px] text-ink-muted">Số tiền</dt>
            <dd className="font-semibold tabular-nums text-ink">
              {amount ? `${money.format(amount)} VNĐ` : "Đang cập nhật"}
            </dd>
          </div>
          <div className="flex items-center justify-between gap-6 px-5 py-4">
            <dt className="text-[13px] text-ink-muted">Số dl</dt>
            <dd className="font-semibold tabular-nums text-ink">
              {credit ? `${money.format(credit)} dl` : "Đang cập nhật"}
            </dd>
          </div>
        </dl>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/vi-tien" className="secondary-button">
          Về ví tiền
        </Link>
        {status === "failed" && <Button onClick={verify}>Kiểm tra lại</Button>}
      </div>
    </div>
  );
}

export default function PaymentResultPage() {
  return (
    <Suspense fallback={<PageLoader compact rows={2} />}>
      <PaymentResultContent />
    </Suspense>
  );
}
