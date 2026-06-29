"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { verifyDepositAPI } from "@/features/finance/services/fiat_deposit.service";
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

    if (cancelParam === "true" || statusParam === "CANCELLED") {
      setStatus("cancelled");
      return;
    }

    if (!orderCode) {
      setStatus("failed");
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
      console.error(err.message || err);
      setStatus("failed");
    }
  }, [searchParams]);

  useEffect(() => {
    verifyPayment();
  }, [verifyPayment]);

  const statusConfig: Record<PaymentStatus, { icon: any; title: string; description: string; color: string; bgClass: string }> = {
    loading: { icon: Loader2, title: "Đang xử lý", description: "Hệ thống đang xác nhận giao dịch của bạn", color: "text-[#0071E3]", bgClass: "bg-[#F5F5F7]" },
    success: { icon: CheckCircle2, title: "Nạp tiền thành công", description: paymentInfo ? `${Number(paymentInfo.amount_paid || paymentInfo.amount || 0).toLocaleString()} VNĐ đã được cộng vào ví` : "Số dư đã được cập nhật", color: "text-[#34C759]", bgClass: "bg-[#EAF8ED]" },
    failed: { icon: XCircle, title: "Giao dịch thất bại", description: "Không thể xác nhận thanh toán. Vui lòng thử lại", color: "text-[#FF3B30]", bgClass: "bg-[#FFEBEB]" },
    cancelled: { icon: XCircle, title: "Giao dịch đã hủy", description: "Bạn đã hủy giao dịch này", color: "text-[#FF3B30]", bgClass: "bg-[#FFEBEB]" },
  };

  const current = statusConfig[status];
  const IconComponent = current.icon;

  return (
    <div className="w-full h-[calc(100vh-56px)] flex flex-col items-center justify-center font-sans text-[#1D1D1F] px-6">
      <div className="w-full max-w-[480px] bg-white border border-[#E8E8ED] rounded-[24px] shadow-sm p-10 flex flex-col items-center text-center">
        <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 ${current.bgClass}`}>
          <IconComponent className={`w-10 h-10 ${current.color} ${status === "loading" ? "animate-spin" : ""}`} />
        </div>

        <h1 className="text-[24px] font-semibold text-[#1D1D1F] mb-2">{current.title}</h1>
        <p className="text-[15px] text-[#6E6E73] mb-8">{current.description}</p>

        {paymentInfo && status === "success" && (
          <div className="w-full bg-[#F5F5F7] rounded-[18px] p-6 space-y-4 mb-8">
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-[#6E6E73] font-medium">Mã giao dịch</span>
              <span className="text-[15px] font-medium text-[#1D1D1F]">#{paymentInfo.order_code}</span>
            </div>
            <div className="w-full h-px bg-[#E8E8ED]"></div>
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-[#6E6E73] font-medium">Số tiền nạp</span>
              <span className="text-[15px] font-semibold text-[#1D1D1F]">{Number(paymentInfo.amount_paid || paymentInfo.amount || 0).toLocaleString()} VNĐ</span>
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 w-full">
          <Link href="/vi-tien" className="flex-1 h-12 bg-[#F5F5F7] text-[#1D1D1F] text-[15px] font-medium flex items-center justify-center gap-2 rounded-full hover:bg-[#E8E8ED] transition-colors">
            <ArrowLeft className="w-4 h-4" /> Về ví tiền
          </Link>
          {(status === "failed" || status === "cancelled") && (
            <button onClick={verifyPayment} className="flex-1 h-12 bg-[#0071E3] text-white text-[15px] font-medium flex items-center justify-center rounded-full hover:bg-[#0077ED] transition-colors">
              Thử lại
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
