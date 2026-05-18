"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/Auth";
import { verifyDepositAPI } from "@/services/deposit.service";
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

type PaymentStatus = "loading" | "success" | "failed" | "cancelled";

export default function PaymentResultPage() {
  const searchParams = useSearchParams();
  const { user } = useAuth() as any;
  const [status, setStatus] = useState<PaymentStatus>("loading");
  const [paymentInfo, setPaymentInfo] = useState<any>(null);
  const [visible, setVisible] = useState(false);

  const verifyPayment = useCallback(async () => {
    const orderCode = searchParams.get("orderCode");
    const cancelParam = searchParams.get("cancel");
    const statusParam = searchParams.get("status");

    if (cancelParam === "true" || statusParam === "CANCELLED") {
      setStatus("cancelled");
      requestAnimationFrame(() => setVisible(true));
      return;
    }

    if (!orderCode) {
      setStatus("failed");
      requestAnimationFrame(() => setVisible(true));
      return;
    }

    try {
      const res = await verifyDepositAPI(Number(orderCode));
      const data = res.data || res;

      setPaymentInfo(data);

      if (data.status === "PAID") {
        setStatus("success");
      } else if (data.status === "CANCELLED") {
        setStatus("cancelled");
      } else {
        setStatus("failed");
      }
    } catch {
      setStatus("failed");
    } finally {
      requestAnimationFrame(() => setVisible(true));
    }
  }, [searchParams]);

  useEffect(() => {
    verifyPayment();
  }, [verifyPayment]);

  const statusConfig: Record<
    PaymentStatus,
    { icon: any; title: string; description: string; bgClass: string }
  > = {
    loading: {
      icon: Loader2,
      title: "Đang xử lý",
      description: "Hệ thống đang xác nhận giao dịch của bạn",
      bgClass: "border-zinc-200 bg-white text-zinc-400",
    },
    success: {
      icon: CheckCircle2,
      title: "Nạp tiền thành công",
      description: paymentInfo
        ? `${Number(paymentInfo.amount_paid || paymentInfo.amount || 0).toLocaleString()} VNĐ đã được cộng vào ví`
        : "Số dư đã được cập nhật",
      bgClass: "border-black bg-black text-white",
    },
    failed: {
      icon: XCircle,
      title: "Giao dịch thất bại",
      description: "Không thể xác nhận thanh toán. Vui lòng thử lại",
      bgClass: "border-zinc-200 bg-zinc-50 text-zinc-400",
    },
    cancelled: {
      icon: XCircle,
      title: "Giao dịch đã hủy",
      description: "Bạn đã hủy giao dịch này",
      bgClass: "border-zinc-200 bg-zinc-50 text-zinc-400",
    },
  };

  const current = statusConfig[status];
  const IconComponent = current.icon;

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="flex flex-col items-center justify-center min-h-[60vh] gap-8 transition-opacity duration-500"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <div
          className={`w-20 h-20 flex items-center justify-center border ${current.bgClass} rounded-none`}
        >
          <IconComponent
            className={`w-8 h-8 ${status === "loading" ? "animate-spin" : ""}`}
          />
        </div>

        <div className="text-center space-y-3">
          <h1 className="text-2xl font-semibold text-black tracking-tight">{current.title}</h1>
          <p className="text-sm font-medium text-zinc-500 max-w-md leading-relaxed">
            {current.description}
          </p>
        </div>

        {paymentInfo && status === "success" && (
          <div className="border border-zinc-200 bg-white p-6 w-full max-w-sm space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest">
                Mã giao dịch
              </span>
              <span className="text-xs font-semibold text-black uppercase tracking-tight">
                #{paymentInfo.order_code}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-zinc-200 pb-3">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest">
                Số tiền
              </span>
              <span className="text-xs font-semibold text-black tracking-tight">
                {Number(
                  paymentInfo.amount_paid || paymentInfo.amount || 0
                ).toLocaleString()}{" "}
                VNĐ
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest">
                Trạng thái
              </span>
              <span className="text-xs font-semibold text-black flex items-center gap-1.5 uppercase tracking-tight">
                <div className="w-1.5 h-1.5 bg-black rounded-none"></div>
                Hoàn tất
              </span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-4">
          <Link
            href="/vi-tien"
            className="h-11 px-8 bg-black text-white text-[11px] font-semibold uppercase tracking-widest flex items-center gap-2 rounded-none transition-transform active:scale-[0.98]"
          >
            <ArrowLeft className="w-4 h-4" /> Về ví tiền
          </Link>
          {(status === "failed" || status === "cancelled") && (
            <button
              onClick={verifyPayment}
              className="h-11 px-8 border border-zinc-200 bg-white text-black text-[11px] font-semibold uppercase tracking-widest flex items-center gap-2 rounded-none transition-transform active:scale-[0.98]"
            >
              Thử lại
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
