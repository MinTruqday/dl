"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  getAuthorRevenueAPI,
  getWalletHistoryAPI,
  getWalletBalanceAPI,
  requestPayoutAPI,
} from "@/app/lib/api";
import { 
  Wallet, 
  TrendingUp, 
  ArrowDownToLine, 
  Clock, 
  Loader2,
  Banknote,
  ArrowUpRight,
  History,
  Info,
  Sparkles,
  ChevronRight
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Notification } from "@/app/components/NotificationToast";

export default function StudioPayoutsPage() {
  const { user, isLoading } = useAuth() as any;
  const router = useRouter();
  const [revenue, setRevenue] = useState<any>(null);
  const [balance, setBalance] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [revData, balData, histData] = await Promise.all([
        getAuthorRevenueAPI(),
        getWalletBalanceAPI(),
        getWalletHistoryAPI(0, 50),
      ]);
      setRevenue(revData.data || revData);
      setBalance(balData.data || balData);
      setHistory(histData.data || histData || []);
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu tài chính:", err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!isLoading && !user) router.push("/login");
    if (!isLoading && user) loadData();
  }, [isLoading, user, router, loadData]);

  const handlePayout = async () => {
    const amount = parseInt(payoutAmount);
    if (!amount || amount < 50000) {
      setNotification({ type: "error", text: "Số tiền tối thiểu để rút là 50.000 dl." });
      return;
    }
    setRequesting(true);
    try {
      await requestPayoutAPI(amount);
      setNotification({ type: "success", text: "Yêu cầu rút tiền đã được gửi thành công." });
      setPayoutAmount("");
      loadData();
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Yêu cầu rút tiền thất bại." });
    } finally {
      setRequesting(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div 
        className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">
              Doanh thu
            </h1>
            <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              Quản trị tài chính & Thu nhập <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
             <Banknote className="w-4 h-4" /> Hệ thống thanh toán DocLib
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        <div 
          className="lg:col-span-9 space-y-12 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { label: "Số dư hiện tại", val: balance?.balance || 0, icon: Wallet, color: "bg-black text-white" },
              { label: "Tổng thu nhập", val: revenue?.total_revenue || 0, icon: TrendingUp, color: "bg-white text-black border-zinc-100" },
              { label: "Đang chờ duyệt", val: revenue?.pending_payout || 0, icon: Clock, color: "bg-white text-black border-zinc-100" },
            ].map((item, i) => (
              <div
                key={i}
                className={`p-10 border transition-all duration-300 group rounded-sm ${item.color}`}
              >
                <item.icon className="w-5 h-5 mb-8 opacity-50" />
                <h3 className="text-4xl font-bold tracking-tighter mb-2 group-hover:translate-x-1 transition-transform duration-300">
                  {item.val.toLocaleString()} <span className="text-sm opacity-30">dl</span>
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest opacity-50">{item.label}</p>
              </div>
            ))}
          </div>

          <div className="space-y-8">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-widest px-1">
              <History className="w-4 h-4 text-zinc-300" /> Nhật ký giao dịch
            </div>
            <div className="grid gap-4">
              {history.length > 0 ? (
                history.map((tx, idx) => (
                  <div
                    key={idx}
                    className="group flex items-center justify-between p-8 border border-zinc-100 bg-white hover:border-black transition-all duration-300 rounded-sm"
                  >
                    <div className="flex items-center gap-8">
                      <div className="w-12 h-12 border border-zinc-100 flex items-center justify-center font-bold text-[13px] text-zinc-300 group-hover:bg-black group-hover:text-white group-hover:border-black transition-all duration-300 rounded-sm">
                        {idx + 1}
                      </div>
                      <div className="space-y-1">
                        <p className="text-base font-bold text-black group-hover:translate-x-1 transition-transform duration-300 tracking-tight">
                          {tx.note || tx.description || tx.type}
                        </p>
                        <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                          {tx.created_at ? new Date(tx.created_at).toLocaleDateString("vi-VN") : "Thời gian không xác định"}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xl font-bold tracking-tighter mb-1 ${tx.amount >= 0 ? "text-black" : "text-zinc-400"}`}>
                        {tx.amount >= 0 ? "+" : ""}{tx.amount?.toLocaleString()} <span className="text-[10px] text-zinc-200 uppercase">dl</span>
                      </div>
                      <div className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Giao dịch hệ thống</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-48 flex flex-col items-center justify-center border border-dashed border-zinc-200 bg-zinc-50/20 rounded-sm">
                  <History className="w-16 h-16 text-zinc-100 mb-8 stroke-[1]" />
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Không có dữ liệu giao dịch</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <aside 
          className="lg:col-span-3 space-y-10 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="flex items-center gap-3 text-[11px] font-bold text-black uppercase tracking-widest px-1">
              <ArrowDownToLine className="w-4 h-4 text-zinc-300" /> Rút tiền
            </div>
            <div className="p-10 border border-zinc-100 bg-white space-y-8 rounded-sm">
              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Số tiền (dl)</label>
                <input
                  type="number"
                  value={payoutAmount}
                  onChange={(e) => setPayoutAmount(e.target.value)}
                  className="w-full h-16 border border-zinc-100 px-6 font-bold text-lg focus:outline-none focus:border-black transition-all rounded-sm placeholder:text-zinc-100"
                  placeholder="0"
                />
              </div>
              <button
                onClick={handlePayout}
                disabled={requesting || !payoutAmount}
                className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all flex items-center justify-center gap-4 active:scale-[0.98] rounded-sm disabled:opacity-50"
              >
                {requesting ? <Loader2 className="w-5 h-5 animate-spin" /> : <ArrowDownToLine className="w-5 h-5" />}
                Gửi yêu cầu
              </button>
            </div>
          </div>

          <div className="p-10 border border-zinc-100 bg-zinc-50/20 space-y-8 rounded-sm">
             <div className="flex items-center gap-3 text-[10px] font-bold text-black uppercase tracking-widest">
                <Info className="w-3.5 h-3.5 text-zinc-300" /> Quy định thanh toán
             </div>
             <div className="space-y-6">
                {[
                  "Tối thiểu 50.000 dl",
                  "Phí hệ thống 2%",
                  "Xử lý trong 48h làm việc"
                ].map((rule, i) => (
                  <div key={i} className="flex items-start gap-4">
                    <ChevronRight className="w-3.5 h-3.5 text-zinc-200 mt-0.5" />
                    <span className="text-[11px] font-bold text-zinc-400 leading-relaxed uppercase tracking-tight">{rule}</span>
                  </div>
                ))}
             </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
