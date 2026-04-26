"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { Wallet, ArrowUpRight, ArrowDownRight, Gift, Clock, CreditCard } from "lucide-react";

export default function WalletPage() {
  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<any[]>([]);
  const [voucherCode, setVoucherCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchWallet();
  }, []);

  const fetchWallet = async () => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    try {
      const [balRes, histRes] = await Promise.all([
        fetch(`${API_URL}/wallet/balance`, { headers }),
        fetch(`${API_URL}/wallet/history`, { headers }),
      ]);
      if (balRes.ok) {
        const data = await balRes.json();
        setBalance(data.balance || 0);
      }
      if (histRes.ok) setHistory(await histRes.json());
    } catch (e) {
      console.error("Wallet load error:", e);
    } finally {
      setLoading(false);
    }
  };

  const showMsg = (msg: string) => {
    setMessage(msg);
    setTimeout(() => setMessage(""), 4000);
  };

  const redeemVoucher = async () => {
    if (!voucherCode.trim()) return;
    try {
      const res = await fetch(`${API_URL}/wallet/redeem-voucher`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ code: voucherCode }),
      });
      const data = await res.json();
      if (res.ok) {
        showMsg(data.message || "Nạp thành công");
        setVoucherCode("");
        fetchWallet();
      } else {
        showMsg(data.detail || "Mã không hợp lệ");
      }
    } catch (e) {
      showMsg("Mất kết nối");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center animate-in fade-in duration-300">
        <div className="w-10 h-10 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[800px] mx-auto px-6 lg:px-8 py-12 md:py-16 bg-white min-h-screen animate-in fade-in duration-300">
      {message && (
        <div className="fixed top-6 right-6 z-50 px-5 py-3 bg-black text-white text-[10px] font-bold tracking-widest animate-in slide-in-from-right-4 duration-300">
          {message}
        </div>
      )}

      <header className="border-b border-black pb-8 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <Wallet className="w-5 h-5 text-zinc-400" />
          <span className="text-[10px] font-bold tracking-widest text-zinc-400">Tài chính</span>
        </div>
        <h1 className="text-4xl font-bold text-black tracking-tighter">Ví DocLib</h1>
      </header>

      <div className="border border-black p-8 mb-10">
        <span className="text-[10px] font-bold tracking-widest text-zinc-400 block mb-2">Số dư hiện tại</span>
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold text-black tracking-tighter">{balance.toLocaleString()}</span>
          <span className="text-lg font-bold text-zinc-400">Coin</span>
        </div>
      </div>

      <div className="border border-border p-6 mb-10">
        <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-4">
          <Gift className="w-4 h-4" /> Nạp mã voucher
        </h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Nhập mã voucher"
            value={voucherCode}
            onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
            onKeyDown={(e) => { if (e.key === "Enter") redeemVoucher(); }}
            className="flex-1 px-4 py-3 border border-border text-sm font-bold tracking-widest focus:outline-none focus:border-black transition-all"
          />
          <button
            onClick={redeemVoucher}
            className="px-6 py-3 bg-black text-white text-[10px] font-bold tracking-widest hover:bg-zinc-800 transition-all"
          >
            Nạp
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-xs font-bold tracking-widest text-black flex items-center gap-2 mb-6">
          <Clock className="w-4 h-4" /> Lịch sử giao dịch
        </h2>
        {history.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-border">
            <p className="text-xs text-zinc-400 font-bold tracking-widest">Chưa có giao dịch nào</p>
          </div>
        ) : (
          <div className="space-y-1">
            {history.map((tx: any) => (
              <div key={tx._id} className="flex items-center justify-between px-5 py-4 border-b border-zinc-50 hover:bg-zinc-50/50 transition-colors">
                <div className="flex items-center gap-3">
                  {tx.amount > 0 ? (
                    <ArrowDownRight className="w-4 h-4 text-black" />
                  ) : (
                    <ArrowUpRight className="w-4 h-4 text-zinc-400" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-black">{tx.note || "Giao dịch"}</p>
                    <span className="text-[10px] text-zinc-400 font-bold tracking-widest">
                      {tx.created_at ? new Date(tx.created_at).toLocaleDateString("vi-VN") : ""}
                    </span>
                  </div>
                </div>
                <span className={`font-bold text-sm ${tx.amount > 0 ? "text-black" : "text-zinc-400"}`}>
                  {tx.amount > 0 ? "+" : ""}{tx.amount} Coin
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
