"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { ArrowUpRight, ArrowDownLeft, Loader2 } from "lucide-react";
import {
  getWalletBalanceAPI,
  getWalletHistoryAPI,
} from "@/features/payment/services/wallet.service";
import { useToast } from "@/shared/contexts/ToastContext";
import PageLoader from "@/shared/components/common/PageLoader";
import Link from "next/link";

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

export default function WalletOverviewPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchWalletData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [balanceRes, historyRes] = await Promise.all([
        getWalletBalanceAPI(),
        getWalletHistoryAPI(),
      ]);
      setBalance(balanceRes.data?.balance ?? balanceRes.balance ?? 0);
      const txList = historyRes.data ?? historyRes ?? [];
      setHistory(Array.isArray(txList) ? txList : []);
    } catch (error) {
      showToast("Lỗi trích xuất dữ liệu ví điện tử", "error");
    } finally {
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (user) fetchWalletData();
  }, [user, fetchWalletData]);

  if (authLoading) return <PageLoader />;

  return (
    <div className="space-y-8">
      {/* Balance Card */}
      <div className="bg-[#1D1D1F] rounded-[24px] p-8 md:p-10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#0071E3] rounded-full filter blur-[100px] opacity-20 translate-x-1/3 -translate-y-1/3"></div>
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <p className="text-[#86868B] text-[15px] font-medium uppercase tracking-wider">
              Số dư khả dụng
            </p>
            <div className="flex items-baseline gap-2">
              <h1 className="text-white text-[48px] md:text-[56px] font-bold tracking-tight">
                {balance.toLocaleString()}
              </h1>
              <span className="text-[#86868B] text-[20px] font-medium">
                dl
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 w-full md:w-auto">
            <Link
              href="/vi-tien/nap-tien"
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-[#0071E3] text-white px-6 py-3.5 rounded-full text-[15px] font-medium hover:bg-[#0055C6] transition-colors"
            >
              <ArrowDownLeft className="w-5 h-5" />
              Nạp tiền
            </Link>
            <Link
              href="/vi-tien/rut-tien"
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-white/10 text-white px-6 py-3.5 rounded-full text-[15px] font-medium hover:bg-white/20 transition-colors backdrop-blur-sm"
            >
              <ArrowUpRight className="w-5 h-5" />
              Rút tiền
            </Link>
          </div>
        </div>
      </div>

      {/* History */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Lịch sử giao dịch</h2>
          <span className="px-3 py-1 bg-[#E8E8ED] text-[#1D1D1F] text-[13px] font-medium rounded-full">
            {history.length} mục
          </span>
        </div>

        {isLoading ? (
          <div className="py-24 flex justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
          </div>
        ) : history.length === 0 ? (
          <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
            <p className="text-[17px] text-[#6E6E73]">Chưa có giao dịch nào</p>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((tx) => {
              const isIn = tx.type === "TOPUP" || tx.amount > 0;
              const displayAmount = Math.abs(tx.amount);
              return (
                <div
                  key={tx._id}
                  className="flex items-center justify-between p-4 bg-white rounded-[16px] hover:bg-[#FAFAFA] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                        isIn ? "bg-[#E3F2E1] text-[#34C759]" : "bg-[#F5F5F7] text-[#6E6E73]"
                      }`}
                    >
                      {isIn ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="text-[15px] font-medium text-[#1D1D1F]">
                        {tx.note || (tx.type === "TOPUP" ? "Nạp tiền" : tx.type === "WITHDRAW" ? "Rút tiền" : "Giao dịch")}
                      </p>
                      <p className="text-[13px] text-[#6E6E73]">
                        {new Date(tx.created_at).toLocaleString("vi-VN")}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-[17px] font-semibold ${isIn ? "text-[#34C759]" : "text-[#1D1D1F]"}`}>
                      {isIn ? "+" : "-"}{displayAmount.toLocaleString()} dl
                    </p>
                    <p className="text-[12px] text-[#6E6E73] flex items-center justify-end gap-1.5 mt-0.5">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          tx.status === "COMPLETED" ? "bg-[#34C759]" : "bg-[#FF9500]"
                        }`}
                      />
                      {tx.status === "COMPLETED" ? "Hoàn tất" : "Đang xử lý"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
