"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { Wallet, ArrowRight, Loader2, Clock, CheckCircle, XCircle } from "lucide-react";

export default function PayoutsPage() {
  const [balance, setBalance] = useState(0);
  const [revenue, setRevenue] = useState<any>(null);
  const [requesting, setRequesting] = useState(false);
  const [bankInfo, setBankInfo] = useState({ bank_name: "", account_number: "", account_holder: "" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    try {
      const [balRes, revRes] = await Promise.all([
        fetch(`${API_URL}/wallet/balance`, { headers }),
        fetch(`${API_URL}/author/revenue`, { headers }),
      ]);
      if (balRes.ok) {
        const d = await balRes.json();
        setBalance(d.balance || 0);
      }
      if (revRes.ok) setRevenue(await revRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(""), 3000);
  };

  const requestPayout = async () => {
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_holder) {
      showMsg("Vui lòng điền đầy đủ thông tin ngân hàng");
      return;
    }
    setRequesting(true);
    try {
      const res = await fetch(`${API_URL}/wallet/payout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ amount: balance, ...bankInfo }),
      });
      if (res.ok) {
        showMsg("Yêu cầu rút tiền đã được ghi nhận");
        fetchData();
      } else {
        const data = await res.json();
        showMsg(data.detail || "Yêu cầu rút tiền thất bại");
      }
    } catch (e) {
      showMsg("Lỗi kết nối");
    }
    setRequesting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[900px] mx-auto px-6 py-12 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[12px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <Wallet className="w-5 h-5 text-zinc-400" />
          <span className="text-[12px] font-bold tracking-widest text-zinc-400">Tài chính</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Rút tiền</h1>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <div className="border border-border p-6">
          <span className="text-3xl font-bold text-black">{balance}</span>
          <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Số dư hiện tại (Coin)</p>
        </div>
        <div className="border border-border p-6">
          <span className="text-3xl font-bold text-black">{revenue?.total_revenue || 0}</span>
          <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tổng doanh thu (Coin)</p>
        </div>
        <div className="border border-border p-6">
          <span className="text-3xl font-bold text-black">{revenue?.total_sales || 0}</span>
          <p className="text-[12px] text-zinc-400 font-bold tracking-widest mt-1">Tổng lượt bán</p>
        </div>
      </div>

      <div className="border border-border p-6">
        <h2 className="text-xs font-bold tracking-widest text-black mb-6">Thông tin ngân hàng</h2>
        <div className="space-y-4 mb-6">
          <input
            type="text"
            placeholder="Tên ngân hàng"
            value={bankInfo.bank_name}
            onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })}
            className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all"
          />
          <input
            type="text"
            placeholder="Số tài khoản"
            value={bankInfo.account_number}
            onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })}
            className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all"
          />
          <input
            type="text"
            placeholder="Chủ tài khoản"
            value={bankInfo.account_holder}
            onChange={(e) => setBankInfo({ ...bankInfo, account_holder: e.target.value })}
            className="w-full px-4 py-3 border border-border text-sm focus:outline-none focus:border-black transition-all"
          />
        </div>
        <button
          onClick={requestPayout}
          disabled={requesting || balance <= 0}
          className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all disabled:bg-zinc-300 flex items-center justify-center gap-2"
        >
          {requesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
          Yêu cầu rút {balance} Coin
        </button>
      </div>
    </div>
  );
}