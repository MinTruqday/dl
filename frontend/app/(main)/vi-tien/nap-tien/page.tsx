"use client";

import { useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { createDepositLinkAPI } from "@/features/payment/services/deposit.service";
import { useToast } from "@/shared/contexts/ToastContext";
import PageLoader from "@/shared/components/common/PageLoader";
import { Loader2, AlertCircle } from "lucide-react";

export default function TopupPage() {
  const { isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [topupAmount, setTopupAmount] = useState(50000);
  const [topupLoading, setTopupLoading] = useState(false);

  const handleTopup = async () => {
    if (topupAmount < 10000)
      return showToast("Mức nạp tối thiểu là 10.000 VNĐ", "error");
    setTopupLoading(true);
    try {
      const res = await createDepositLinkAPI(topupAmount);
      const url = res?.data?.checkout_url ?? res?.checkout_url ?? null;
      if (url) {
        window.location.href = url;
      } else {
        showToast("Lỗi kết nối đến cổng thanh toán", "error");
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi khởi tạo giao dịch nạp tiền", "error");
    } finally {
      setTopupLoading(false);
    }
  };

  if (authLoading) return <PageLoader />;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
          Nạp tiền
        </h2>
      </div>
      <div className="bg-white rounded-[18px] p-6">
        <div className="space-y-6">
          <div className="space-y-3">
            <label className="text-[14px] font-medium text-[#6E6E73]">
              Chọn hạn mức
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[50000, 100000, 200000, 500000, 1000000].map((amt) => (
                <button
                  key={amt}
                  onClick={() => setTopupAmount(amt)}
                  className={`py-3 rounded-[12px] text-[15px] font-medium transition-all duration-200 border ${
                    topupAmount === amt
                      ? "bg-[#E6F0FA] border-[#0071E3] text-[#0071E3] shadow-sm"
                      : "bg-white border-[#E8E8ED] text-[#1D1D1F] hover:bg-[#F5F5F7]"
                  }`}
                >
                  {amt.toLocaleString()} ₫
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-3">
            <label className="text-[14px] font-medium text-[#6E6E73]">
              Hoặc nhập số tiền khác
            </label>
            <div className="relative">
              <input
                type="number"
                value={topupAmount}
                onChange={(e) => setTopupAmount(Number(e.target.value))}
                className="w-full h-12 pl-4 pr-12 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] rounded-[12px] outline-none text-[#1D1D1F] text-[17px] font-medium transition-all duration-200"
                placeholder="Nhập số tiền..."
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#86868B] font-medium">
                VNĐ
              </span>
            </div>
          </div>
          
          <div className="bg-[#F5F5F7] p-4 rounded-[12px] flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#86868B] shrink-0 mt-0.5" />
            <div className="text-[13px] text-[#6E6E73] leading-relaxed">
              <p>Thanh toán bảo mật qua cổng PayOS.</p>
              <p>Mã QR tự động xác nhận trong vòng 1-3 phút.</p>
              <p>1 VNĐ tương ứng với 1 dl.</p>
            </div>
          </div>

          <button
            onClick={handleTopup}
            disabled={topupLoading || topupAmount < 10000}
            className="w-full py-3.5 bg-[#0071E3] hover:bg-[#0055C6] text-white rounded-[12px] font-medium text-[15px] transition-all duration-200 flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {topupLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Đang xử lý...
              </>
            ) : (
              "Thanh toán ngay"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
