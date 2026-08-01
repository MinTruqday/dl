"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { verifyDepositAPI } from "@/features/payment/services/deposit.service";

export type PaymentResultStatus =
  "loading" | "success" | "failed" | "cancelled";

export type PaymentResultData = {
  order_code?: string | number;
  status?: string;
  amount?: number;
  amount_paid?: number;
  dl?: number;
};

export function usePaymentResult() {
  const params = useSearchParams();
  const [status, setStatus] = useState<PaymentResultStatus>("loading");
  const [data, setData] = useState<PaymentResultData | null>(null);
  const [error, setError] = useState("");

  const verify = useCallback(async () => {
    const orderCode = params.get("orderCode");
    const cancelled =
      params.get("cancel") === "true" || params.get("status") === "CANCELLED";
    if (cancelled) {
      setData({ order_code: orderCode || undefined });
      setStatus("cancelled");
      return;
    }
    if (!orderCode || !Number.isFinite(Number(orderCode))) {
      setError("Thiếu mã giao dịch hợp lệ");
      setStatus("failed");
      return;
    }
    setStatus("loading");
    setError("");
    try {
      const response = await verifyDepositAPI(Number(orderCode));
      const result = response?.data || response || {};
      setData({ ...result, order_code: result.order_code || orderCode });
      if (String(result.status || "").toUpperCase() === "PAID")
        setStatus("success");
      else if (String(result.status || "").toUpperCase() === "CANCELLED")
        setStatus("cancelled");
      else setStatus("failed");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể xác nhận giao dịch",
      );
      setStatus("failed");
    }
  }, [params]);

  useEffect(() => {
    verify();
  }, [verify]);

  return { status, data, error, verify };
}
