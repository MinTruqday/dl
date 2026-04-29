"use client";

import React, { useEffect, useState } from "react";
import AppShell from "@/app/components/AppShell";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  getAuthorRevenueAPI,
  getWalletHistoryAPI,
  getWalletBalanceAPI,
  requestPayoutAPI,
} from "@/app/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Wallet, TrendingUp, ArrowDownToLine, Clock, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function StudioPayoutsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [revenue, setRevenue] = useState<any>(null);
  const [balance, setBalance] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [feedback, setFeedback] = useState({ type: "", text: "" });
  const [activeTab, setActiveTab] = useState<"overview" | "history">("overview");
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
    if (!isLoading && user) {
      loadData();
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isLoading, user, router]);

  const loadData = async () => {
    try {
      const [revData, balData, histData] = await Promise.all([
        getAuthorRevenueAPI(),
        getWalletBalanceAPI(),
        getWalletHistoryAPI(0, 30),
      ]);
      setRevenue(revData.data || revData);
      setBalance(balData.data || balData);
      setHistory(histData.data || histData || []);
    } catch (err: any) {
      console.error("Lỗi tải dữ liệu tài chính:", err);
    }
  };

  const handlePayout = async () => {
    const amount = parseInt(payoutAmount);
    if (!amount || amount <= 0) {
      setFeedback({ type: "error", text: "Số tiền không hợp lệ." });
      return;
    }
    setRequesting(true);
    setFeedback({ type: "", text: "" });
    try {
      await requestPayoutAPI(amount);
      setFeedback({ type: "success", text: "Yêu cầu rút tiền đã được gửi." });
      setPayoutAmount("");
      loadData();
    } catch (e: any) {
      setFeedback({ type: "error", text: e.message || "Không thể gửi yêu cầu." });
    } finally {
      setRequesting(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex h-[80vh] items-center justify-center">
          <Loader2 className="w-10 h-10 animate-spin text-zinc-300" />
        </div>
      </AppShell>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <AppShell>
      <div
        className="max-w-5xl mx-auto px-4 py-12 md:py-20 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className="mb-12 border-b border-zinc-200 pb-8">
          <h1 className="text-4xl font-bold tracking-tighter text-black">Thu nhập và rút tiền</h1>
          <p className="text-sm font-bold text-zinc-400 mt-2">Quản lý doanh thu từ tài liệu</p>
        </div>

        {feedback.text && (
          <div className="p-4 mb-8 text-sm font-bold border bg-zinc-50 text-black border-zinc-200 transition-opacity duration-300">
            {feedback.text}
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="border border-zinc-200 bg-white p-6 rounded-sm">
            <div className="flex items-center gap-3 mb-4">
              <Wallet className="w-5 h-5 text-zinc-400" />
              <span className="text-xs font-bold text-zinc-400">Số dư hiện tại</span>
            </div>
            <p className="text-3xl font-bold text-black">
              {balance?.balance?.toLocaleString() || 0} <span className="text-sm text-zinc-400">dl</span>
            </p>
          </div>
          <div className="border border-zinc-200 bg-white p-6 rounded-sm">
            <div className="flex items-center gap-3 mb-4">
              <TrendingUp className="w-5 h-5 text-zinc-400" />
              <span className="text-xs font-bold text-zinc-400">Tổng thu nhập</span>
            </div>
            <p className="text-3xl font-bold text-black">
              {revenue?.total_revenue?.toLocaleString() || 0} <span className="text-sm text-zinc-400">dl</span>
            </p>
          </div>
          <div className="border border-zinc-200 bg-white p-6 rounded-sm">
            <div className="flex items-center gap-3 mb-4">
              <ArrowDownToLine className="w-5 h-5 text-zinc-400" />
              <span className="text-xs font-bold text-zinc-400">Đã rút</span>
            </div>
            <p className="text-3xl font-bold text-black">
              {revenue?.total_withdrawn?.toLocaleString() || 0} <span className="text-sm text-zinc-400">dl</span>
            </p>
          </div>
        </div>

        <div className="border border-zinc-200 bg-white p-6 rounded-sm mb-8">
          <h2 className="text-sm font-bold text-zinc-400 mb-4">Thực hiện rút tiền</h2>
          <div className="flex gap-3 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-xs font-bold text-zinc-400">Số tiền cần rút (dl)</label>
              <Input
                value={payoutAmount}
                onChange={(e) => setPayoutAmount(e.target.value)}
                placeholder=""
                type="number"
                className="h-12 border-zinc-200 focus:border-black transition-all"
              />
            </div>
            <Button
              onClick={handlePayout}
              disabled={requesting}
              className="bg-black text-white hover:bg-zinc-800 h-12 px-8 flex items-center gap-2 transition-all active:scale-[0.98]"
            >
              {requesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowDownToLine className="w-4 h-4" />}
              <span className="text-sm font-bold">Xác nhận</span>
            </Button>
          </div>
        </div>

        <div className="border-b border-zinc-200 mb-8">
          <nav className="-mb-px flex gap-8">
            {[
              { id: "overview", label: "Tổng quan" },
              { id: "history", label: "Lịch sử giao dịch" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-bold text-sm transition-all duration-150 ${
                  activeTab === tab.id
                    ? "border-black text-black"
                    : "border-transparent text-zinc-400 hover:text-black hover:border-zinc-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="min-h-[300px]">
          {activeTab === "overview" && (
            <div className="space-y-4 animate-in slide-in-from-bottom-2 fade-in duration-300">
              <div className="border border-zinc-200 bg-white p-6 rounded-sm">
                <h3 className="text-sm font-bold text-zinc-400 mb-4">Chi tiết thống kê</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-sm hover:border-black transition-all">
                    <p className="text-xs font-bold text-zinc-400 mb-1">Lượt mua tài liệu</p>
                    <p className="text-xl font-bold text-black">{revenue?.total_purchases || 0}</p>
                  </div>
                  <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-sm hover:border-black transition-all">
                    <p className="text-xs font-bold text-zinc-400 mb-1">Lượt ủng hộ</p>
                    <p className="text-xl font-bold text-black">{revenue?.total_tips || 0}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "history" && (
            <div className="animate-in slide-in-from-bottom-2 fade-in duration-300">
              {history.length > 0 ? (
                <div className="space-y-2">
                  {history.map((tx, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-4 border border-zinc-200 rounded-sm hover:bg-zinc-50 hover:border-black transition-all duration-150"
                    >
                      <div className="flex items-center gap-3">
                        <Clock className="w-4 h-4 text-zinc-400" />
                        <div>
                          <p className="font-bold text-black text-sm">{tx.description || tx.type}</p>
                          <p className="text-xs text-zinc-400">
                            {tx.created_at ? new Date(tx.created_at).toLocaleDateString("vi-VN") : ""}
                          </p>
                        </div>
                      </div>
                      <span className={`font-bold text-sm ${tx.amount >= 0 ? "text-black" : "text-zinc-500"}`}>
                        {tx.amount >= 0 ? "+" : ""}
                        {tx.amount?.toLocaleString()} dl
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20 text-zinc-400 bg-zinc-50 border border-zinc-200 rounded-sm">
                  <Clock className="w-12 h-12 mx-auto mb-4 opacity-20" />
                  <p className="font-bold text-sm">Chưa phát sinh giao dịch</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
