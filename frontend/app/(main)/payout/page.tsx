"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getAuthorRevenueAPI } from "@/services/monetization.service";
import {
  getWalletHistoryAPI,
  getWalletBalanceAPI,
  requestPayoutAPI,
} from "@/services/wallet.service";
import {
  Wallet,
  TrendingUp,
  ArrowDownToLine,
  Clock,
  Loader2,
  Banknote,
  History,
  Info,
  ChevronRight,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/contexts/ToastContext";

export default function StudioPayoutsPage() {
  const { user, isLoading } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();
  const [revenue, setRevenue] = useState<any>(null);
  const [balance, setBalance] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [bankInfo, setBankInfo] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [revData, balData, histData] = await Promise.all([
        getAuthorRevenueAPI(),
        getWalletBalanceAPI(),
        (getWalletHistoryAPI as any)(0, 50),
      ]);
      setRevenue(revData?.data || revData || {});
      setBalance(balData?.data || balData || {});
      setHistory(histData?.data || histData || []);
    } catch (err: any) {
      showToast("Lỗi tải dữ liệu tài chính", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isLoading && !user) router.push("/dang-nhap");
    if (!isLoading && user) loadData();
  }, [isLoading, user, router, loadData]);

  const handlePayout = async () => {
    const amount = parseInt(payoutAmount);
    if (!amount || amount < 50000) {
      showToast("Số tiền tối thiểu để rút là 50.000 dl.", "error");
      return;
    }
    if (!bankInfo.trim()) {
      showToast("Vui lòng nhập thông tin ngân hàng.", "error");
      return;
    }
    setRequesting(true);
    try {
      await requestPayoutAPI(amount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi thành công.", "success");
      setPayoutAmount("");
      setBankInfo("");
      loadData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại.", "error");
    } finally {
      setRequesting(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Doanh thu</h1>
            <p className="text-sm text-zinc-500 mt-1">Quản trị tài chính & Thu nhập</p>
          </div>
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 border border-zinc-200 text-xs font-medium text-zinc-500 bg-white">
            Hệ thống thanh toán
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="p-6 border border-black bg-black text-white flex flex-col justify-between h-32">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold uppercase tracking-wider opacity-80">Số dư hiện tại</p>
              <Wallet className="w-4 h-4 opacity-50" />
            </div>
            <div className="flex items-baseline gap-1 mt-auto">
              <span className="text-3xl font-bold tracking-tight">{balance?.balance?.toLocaleString() || 0}</span>
              <span className="text-sm opacity-50">dl</span>
            </div>
          </div>
          <div className="p-6 border border-zinc-200 bg-white text-black flex flex-col justify-between h-32">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Tổng thu nhập</p>
              <TrendingUp className="w-4 h-4 text-zinc-300" />
            </div>
            <div className="flex items-baseline gap-1 mt-auto">
              <span className="text-3xl font-bold tracking-tight">{revenue?.total_revenue?.toLocaleString() || 0}</span>
              <span className="text-sm text-zinc-400">dl</span>
            </div>
          </div>
          <div className="p-6 border border-zinc-200 bg-white text-black flex flex-col justify-between h-32">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Đang chờ duyệt</p>
              <Clock className="w-4 h-4 text-zinc-300" />
            </div>
            <div className="flex items-baseline gap-1 mt-auto">
              <span className="text-3xl font-bold tracking-tight">{revenue?.pending_payout?.toLocaleString() || 0}</span>
              <span className="text-sm text-zinc-400">dl</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-2 space-y-8">
            <div>
              <h2 className="text-sm font-semibold text-black mb-6">
                Nhật ký giao dịch
              </h2>
              <div className="border border-zinc-200 bg-white">
                {history.length > 0 ? (
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-200 bg-zinc-50">
                        <th className="py-3 px-4 text-xs font-semibold text-zinc-600">Thời gian</th>
                        <th className="py-3 px-4 text-xs font-semibold text-zinc-600">Mô tả / Ngân hàng</th>
                        <th className="py-3 px-4 text-xs font-semibold text-zinc-600 text-right">Số lượng</th>
                        <th className="py-3 px-4 text-xs font-semibold text-zinc-600 text-right">Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((tx, idx) => {
                        const status = (tx.status || "COMPLETED").toUpperCase();
                        return (
                          <tr key={idx} className="border-b border-zinc-200 last:border-0">
                            <td className="py-4 px-4 align-top">
                              <span className="text-[11px] font-medium text-zinc-500 whitespace-nowrap">
                                {tx.created_at ? new Date(tx.created_at).toLocaleDateString("vi-VN") : "--"}
                              </span>
                            </td>
                            <td className="py-4 px-4 align-top">
                              <p className="text-sm font-medium text-black max-w-[200px] truncate">
                                {tx.note || tx.description || tx.type}
                              </p>
                              <span className="text-[10px] text-zinc-400 font-mono mt-1 block">
                                ID: {tx.id || tx._id || `TX-${idx}`}
                              </span>
                            </td>
                            <td className="py-4 px-4 align-top text-right whitespace-nowrap">
                              <span className={`text-sm font-semibold ${tx.amount >= 0 ? "text-black" : "text-zinc-500"}`}>
                                {tx.amount >= 0 ? "+" : ""}{tx.amount?.toLocaleString()} dl
                              </span>
                            </td>
                            <td className="py-4 px-4 align-top text-right">
                              <span className={`inline-block text-[10px] font-semibold border px-2 py-1 uppercase ${
                                status === "PENDING" ? "border-black text-black" : 
                                status === "REJECTED" ? "border-zinc-200 text-zinc-400" :
                                "border-zinc-200 text-zinc-500"
                              }`}>
                                {status}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                ) : (
                  <div className="py-24 flex flex-col items-center justify-center bg-white border-t border-zinc-200">
                    <p className="text-sm font-medium text-zinc-500">Chưa có dữ liệu</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <h2 className="text-sm font-semibold text-black">
              Rút tiền
            </h2>
            <div className="border border-zinc-200 bg-white p-6 space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">
                  Số tiền rút (dl)
                </label>
                <input
                  type="number"
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400"
                  placeholder="Tối thiểu 50.000"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">
                  Thông tin ngân hàng
                </label>
                <input
                  type="text"
                  value={bankInfo}
                  onChange={(e) => setBankInfo(e.target.value)}
                  className="w-full border border-zinc-200 p-3 text-sm font-medium text-black focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400"
                  placeholder="VD: VCB - 123456789 - NGUYEN VAN A"
                />
              </div>
              <button
                onClick={handlePayout}
                disabled={requesting || !payoutAmount || !bankInfo}
                className="w-full py-3 bg-black text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-2 disabled:opacity-50 rounded-none border border-black"
              >
                {requesting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowDownToLine className="w-4 h-4" />
                )}
                Yêu cầu rút tiền
              </button>
            </div>

            <div className="border border-zinc-200 bg-zinc-50 p-6 space-y-4">
              <h3 className="text-xs font-semibold text-black flex items-center gap-2">
                <Info className="w-3.5 h-3.5" /> Quy định thanh toán
              </h3>
              <div className="space-y-3">
                {[
                  "Tối thiểu 50.000 dl cho mỗi lần rút.",
                  "Phí hệ thống 2% sẽ được áp dụng.",
                  "Giao dịch được xử lý trong vòng 48h làm việc.",
                  "Vui lòng điền chính xác thông tin ngân hàng."
                ].map((rule, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <ChevronRight className="w-3.5 h-3.5 text-zinc-400 mt-0.5 shrink-0" />
                    <span className="text-[11px] font-medium text-zinc-500 leading-relaxed">
                      {rule}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
