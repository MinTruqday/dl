"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { verifyDepositAPI } from "@/features/payment/services/deposit.service";
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

type PaymentStatus = "loading" | "success" | "failed" | "cancelled";

export default function PaymentResultPage() {
  const searchParams = useSearchParams();
  const { user } = useAuth() as any;
  const [status, setStatus] = useState<PaymentStatus>("loading");
  const [paymentInfo, setPaymentInfo] = useState<any>(null);

  const verifyPayment = useCallback(async () => {
    const orderCode = searchParams.get("orderCode");
    const cancelParam = searchParams.get("cancel");
    const statusParam = searchParams.get("status");
    const codeParam = searchParams.get("code");

    if (cancelParam === "true" || statusParam === "CANCELLED") {
      setStatus("cancelled");
      setPaymentInfo({ order_code: orderCode });
      return;
    }

    if (!orderCode) {
      setStatus("failed");
      return;
    }

    if (codeParam === "00") {
      setPaymentInfo({ order_code: orderCode, status: "PAID", amount: 0, amount_paid: 0 });
      setStatus("success");
      try {
        const res = await verifyDepositAPI(Number(orderCode));
        const data = res.data || res;
        if (data) setPaymentInfo({ ...data, order_code: data.order_code || orderCode });
      } catch (err) {
        console.warn("Error extracting transaction details from payment gateway:", err);
      }
      return;
    }

    try {
      const res = await verifyDepositAPI(Number(orderCode));
      const data = res.data || res;
      setPaymentInfo(data);
      if (data.status === "PAID") setStatus("success");
      else if (data.status === "CANCELLED") setStatus("cancelled");
      else setStatus("failed");
    } catch (err: any) {
      console.error("Error validating payment status:", err.message || err);
      setStatus("failed");
    }
  }, [searchParams]);


  useEffect(() => {
    verifyPayment();
  }, [verifyPayment]);

  const statusConfig: Record<
    PaymentStatus,
    {
      icon: any;
      title: string;
      description: string;
      color: string;
      bgClass: string;
    }
  > = {
    loading: {
      icon: Loader2,
      title: "Đang xử lý",
      description: "Hệ thống đang xác nhận giao dịch của bạn",
      color: "text-brand",
      bgClass: "bg-surface-quiet",
    },
    success: {
      icon: CheckCircle2,
      title: "Nạp tiền hoàn tất",
      description: (paymentInfo?.amount_paid || paymentInfo?.amount)
        ? `${Number(paymentInfo.amount_paid || paymentInfo.amount || 0).toLocaleString()} VNĐ đã được cộng vào ví`
        : "Số dư sẽ được cập nhật trong giây lát",
      color: "text-brand",
      bgClass: "bg-brand-soft",
    },
    failed: {
      icon: XCircle,
      title: "Giao dịch lỗi",
      description: "Không thể xác nhận thanh toán. Vui lòng thử lại",
      color: "text-danger",
      bgClass: "bg-danger-soft",
    },
    cancelled: {
      icon: XCircle,
      title: "Giao dịch đã hủy",
      description: "Bạn đã hủy giao dịch này",
      color: "text-danger",
      bgClass: "bg-danger-soft",
    },
  };

  const current = statusConfig[status];
  const IconComponent = current.icon;

  return (
    <div className="w-full h-[calc(100vh-56px)] flex flex-col items-center justify-center font-sans text-ink px-6 md:px-0">
      <div className="w-full max-w-[480px] bg-surface-quiet border-border rounded-panel p-10 flex flex-col items-center text-center">
        <div
          className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 ${current.bgClass}`}
        >
          <IconComponent
            className={`w-10 h-10 ${current.color} ${status === "loading" ? "animate-spin" : ""}`}
          />
        </div>

        <h1 className="text-[24px] font-semibold text-ink mb-2">
          {current.title}
        </h1>
        <p className="text-[15px] text-ink-muted mb-8">{current.description}</p>

        {status === "success" && paymentInfo && (
          <div className="w-full bg-surface-quiet rounded-panel p-6 space-y-4 mb-8">
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-ink-muted font-medium">Mã giao dịch</span>
              <span className="text-[15px] font-medium text-ink">#{paymentInfo.order_code}</span>
            </div>
            <div className="w-full h-px bg-border"></div>
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-ink-muted font-medium">Số tiền nạp</span>
              <span className="text-[15px] font-semibold text-ink">
                {(paymentInfo.amount_paid || paymentInfo.amount)
                  ? `${Number(paymentInfo.amount_paid || paymentInfo.amount).toLocaleString()} VNĐ`
              : <span className="text-ink-muted text-[13px]">Đang cập nhật</span>
                }
              </span>
            </div>
            {paymentInfo.dl > 0 && (
              <>
                <div className="w-full h-px bg-border"></div>
                <div className="flex items-center justify-between">
                  <span className="text-[13px] text-ink-muted font-medium">Số dl nhận được</span>
                  <span className="text-[15px] font-semibold text-brand">+{paymentInfo.dl.toLocaleString()} dl</span>
                </div>
              </>
            )}
          </div>
        )}

        <div className="flex items-center gap-4 w-full">
          <Link
            href="/vi-tien"
            className="flex-1 h-12 bg-surface-quiet text-ink text-[15px] font-medium flex items-center justify-center gap-2 rounded-full hover:bg-border transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Về ví tiền
          </Link>
          {(status === "failed" || status === "cancelled") && (
            <button
              onClick={verifyPayment}
              className="flex-1 h-12 bg-brand text-white text-[15px] font-medium flex items-center justify-center rounded-full hover:bg-brand transition-colors"
            >
              Thử lại
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
