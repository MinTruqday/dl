"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  Wallet,
  History,
  CreditCard,
  Gift,
  ArrowUpRight,
  ArrowDownLeft,
  Zap,
  X,
  Plus,
  Loader2,
  AlertCircle,
  Info,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { API_URL, getToken, depositDLAPI } from "@/app/lib/api";
import { Notification } from "@/app/components/NotificationToast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

export default function WalletPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [voucherCode, setVoucherCode] = useState("");
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [notification, setNotification] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [visible, setVisible] = useState(false);

  const [showTopupModal, setShowTopupModal] = useState(false);
  const [topupAmount, setTopupAmount] = useState(50000);
  const [topupLoading, setTopupLoading] = useState(false);

  const fetchWalletData = useCallback(async () => {
    setIsLoading(true);
    const token = getToken();
    if (!token) return;

    try {
      const [balanceRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/wallet/balance`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/wallet/history`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      const [balanceData, historyData] = await Promise.all([balanceRes.json(), historyRes.json()]);

      if (balanceRes.ok) setBalance(balanceData.data?.balance || balanceData.balance || 0);
      if (historyRes.ok) setHistory(historyData.data || historyData || []);
    } catch (error) {
      console.error("Lỗi tải dữ liệu ví:", error);
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (user) fetchWalletData();
  }, [user, fetchWalletData]);

  const handleRedeemVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!voucherCode.trim() || isRedeeming) return;

    setIsRedeeming(true);
    const token = getToken();

    try {
      const res = await fetch(`${API_URL}/wallet/redeem-voucher`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code: voucherCode }),
      });
      const data = await res.json();
      if (res.ok) {
        setNotification({ type: "success", text: "Kích hoạt voucher thành công. Số dư đã được cập nhật." });
        setVoucherCode("");
        fetchWalletData();
      } else {
        setNotification({ type: "error", text: data.message || data.detail || "Voucher không hợp lệ hoặc đã hết hạn" });
      }
    } catch (error) {
      setNotification({ type: "error", text: "Lỗi kết nối hệ thống, vui lòng thử lại sau." });
    } finally {
      setIsRedeeming(false);
    }
  };

  const handleTopup = async () => {
    if (topupAmount < 10000) {
      setNotification({ type: "error", text: "Số tiền nạp tối thiểu là 10.000 VND." });
      return;
    }
    setTopupLoading(true);
    try {
      const res = await depositDLAPI(topupAmount);
      if (res.payUrl) {
        window.location.href = res.payUrl;
      } else {
        setNotification({ type: "error", text: "Không thể khởi tạo thanh toán MoMo lúc này." });
      }
    } catch (e: any) {
      setNotification({ type: "error", text: e.message || "Lỗi hệ thống khi nạp tiền." });
    } finally {
      setTopupLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-10 font-sans px-6 text-center">
        <div className="w-24 h-24 bg-zinc-50 flex items-center justify-center border border-zinc-100">
          <AlertCircle className="w-12 h-12 text-zinc-200 stroke-[1]" />
        </div>
        <div className="space-y-4">
          <h2 className="text-3xl font-bold text-black tracking-tighter">Truy cập bị hạn chế</h2>
          <p className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Vui lòng đăng nhập để quản lý tài chính cá nhân</p>
        </div>
        <Button
          onClick={() => (window.location.href = "/login")}
          className="bg-black text-white h-16 px-12 text-[11px] font-bold uppercase tracking-widest transition-all active:scale-95 rounded-none"
        >
          Đăng nhập ngay
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Premium Topup Modal */}
      {showTopupModal && (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center p-6 animate-in fade-in duration-500 backdrop-blur-md">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowTopupModal(false)} />
          <div className="bg-white w-full max-w-xl relative border border-zinc-200 shadow-2xl animate-in zoom-in-95 duration-300 rounded-none">
            <div className="p-10 border-b border-zinc-100 flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="text-2xl font-bold text-black tracking-tighter flex items-center gap-4">
                  <CreditCard className="w-6 h-6" /> Nạp tài nguyên
                </h3>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Thanh toán an toàn qua cổng MoMo</p>
              </div>
              <button onClick={() => setShowTopupModal(false)} className="p-3 hover:bg-zinc-50 transition-colors">
                <X className="w-6 h-6 text-zinc-300" />
              </button>
            </div>
            <div className="p-10 space-y-10">
              <div className="space-y-6">
                <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5" /> Chọn mệnh giá phổ biến (VND)
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {[50000, 100000, 200000, 500000].map((amt) => (
                    <button
                      key={amt}
                      onClick={() => setTopupAmount(amt)}
                      className={`h-20 border text-[13px] font-bold tracking-tighter transition-all active:scale-[0.98] rounded-none ${
                        topupAmount === amt 
                          ? "bg-black text-white border-black shadow-lg shadow-black/10" 
                          : "bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black"
                      }`}
                    >
                      {amt.toLocaleString()} <span className="text-[10px] ml-1">VNĐ</span>
                    </button>
                  ))}
                </div>
                <div className="relative group">
                  <input
                    type="number"
                    value={topupAmount}
                    onChange={(e) => setTopupAmount(parseInt(e.target.value) || 0)}
                    className="w-full h-16 bg-zinc-50 border border-zinc-100 px-8 text-center text-lg font-bold tracking-tighter focus:outline-none focus:border-black focus:bg-white transition-all rounded-none"
                  />
                  <div className="absolute right-8 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">VND</div>
                </div>
              </div>
              
              <div className="bg-zinc-50/50 p-8 flex items-center justify-between border border-zinc-100">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tỷ lệ quy đổi nền tảng</span>
                <span className="text-sm font-bold text-black tracking-tight">1.000 VNĐ = <span className="text-lg">1 dl</span></span>
              </div>

              <Button
                onClick={handleTopup}
                disabled={topupLoading || topupAmount < 10000}
                className="w-full h-20 bg-black text-white hover:bg-zinc-800 text-[11px] font-bold uppercase tracking-[0.2em] transition-all active:scale-[0.98] flex items-center justify-center gap-4 disabled:opacity-50 rounded-none"
              >
                {topupLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : "Bắt đầu thanh toán ngay"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main Page Layout */}
      <header 
        className="mb-12 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div>
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
            Ví điện tử
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Energy & Value Ecosystem <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
        <Button
          onClick={() => setShowTopupModal(true)}
          className="bg-black text-white hover:bg-zinc-800 h-16 px-12 text-[11px] font-bold uppercase tracking-[0.2em] transition-all active:scale-95 flex items-center gap-4 rounded-none shadow-xl shadow-black/5"
        >
          <Plus className="w-5 h-5" /> Nạp thêm tài nguyên
        </Button>
      </header>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Left Column: Balance & Voucher */}
        <aside 
          className="lg:col-span-4 space-y-12 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {/* Main Balance Card - Simplified and Clean */}
          <div className="bg-white border border-zinc-100 p-12 transition-all duration-700 shadow-sm">
            <div className="space-y-10">
               <div className="flex flex-col gap-2">
                  <p className="text-zinc-300 text-[10px] font-bold uppercase tracking-[0.2em]">Năng lượng tri thức</p>
                  <div className="flex items-baseline gap-3">
                    <span className="text-7xl font-bold tracking-tighter text-black">
                      {balance.toLocaleString()}
                    </span>
                    <span className="text-xl font-bold text-zinc-200 italic">dl</span>
                  </div>
               </div>

               <div className="pt-10 border-t border-zinc-50 flex flex-col gap-6">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col gap-1">
                      <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Trạng thái định danh</span>
                      <div className="flex items-center gap-2 text-[10px] font-bold text-black uppercase">
                        <div className="w-2 h-2 bg-black animate-pulse" /> Global Verified
                      </div>
                    </div>
                    <div className="flex -space-x-2">
                      <div className="w-8 h-8 rounded-full border-2 border-white bg-zinc-50" />
                      <div className="w-8 h-8 rounded-full border-2 border-white bg-zinc-100" />
                    </div>
                  </div>
                  
                  <div className="p-4 bg-zinc-50/50 border border-zinc-100 text-[10px] font-medium text-zinc-400 italic">
                    Tài khoản được bảo vệ bởi lớp mã hóa đa tầng.
                  </div>
               </div>
            </div>
          </div>

          {/* Voucher Activation Card */}
          <div className="bg-zinc-50/50 border border-zinc-100 p-8 space-y-6">
            <div className="space-y-1">
              <h3 className="text-[11px] font-bold text-black uppercase tracking-widest flex items-center gap-3">
                <Gift className="w-4 h-4 text-zinc-300" /> Kích hoạt Voucher
              </h3>
              <p className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Sử dụng mã quà tặng từ đối tác</p>
            </div>
            <form onSubmit={handleRedeemVoucher} className="space-y-4">
              <input
                type="text"
                value={voucherCode}
                onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                className="w-full h-16 bg-white border border-zinc-100 px-6 text-center text-sm font-bold tracking-widest focus:outline-none focus:border-black transition-all rounded-none"
              />
              <Button
                type="submit"
                disabled={isRedeeming || !voucherCode.trim()}
                className="w-full h-16 bg-white text-black border border-zinc-100 hover:bg-black hover:text-white transition-all text-[11px] font-bold uppercase tracking-widest active:scale-[0.98] disabled:opacity-50 rounded-none"
              >
                {isRedeeming ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận mã"}
              </Button>
            </form>
          </div>
        </aside>

        {/* Right Column: Transaction History */}
        <main 
          className="lg:col-span-8 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="bg-white border border-zinc-100 flex flex-col h-full min-h-[700px]">
            <div className="px-10 py-10 border-b border-zinc-100 flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="text-2xl font-bold text-black tracking-tighter flex items-center gap-4">
                  <History className="w-6 h-6 text-zinc-200" /> Nhật ký giao dịch
                </h3>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Theo dõi dòng chảy tài nguyên của bạn</p>
              </div>
              <div className="px-5 py-2 bg-zinc-50 border border-zinc-100 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                {history.length} Giao dịch
              </div>
            </div>

            <div className="flex-1">
              {isLoading ? (
                <div className="py-48 text-center flex flex-col items-center gap-6">
                  <Loader2 className="animate-spin w-12 h-12 text-zinc-100 stroke-[1]" />
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">Đang đồng bộ dữ liệu ví</p>
                </div>
              ) : history.length === 0 ? (
                <div className="py-48 text-center flex flex-col items-center gap-8">
                  <div className="w-24 h-24 bg-zinc-50 flex items-center justify-center border border-zinc-100">
                    <Info className="w-10 h-10 text-zinc-200 stroke-[1]" />
                  </div>
                  <div className="space-y-2">
                    <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-[0.4em]">Nhật ký đang trống</p>
                    <p className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest italic">Hãy bắt đầu nạp năng lượng tri thức ngay hôm nay</p>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-zinc-50">
                  {history.map((tx) => (
                    <div
                      key={tx._id}
                      className="px-10 py-10 flex items-center justify-between hover:bg-zinc-50/50 transition-all duration-500 group"
                    >
                      <div className="flex items-center gap-10">
                        <div
                          className={`w-16 h-16 flex items-center justify-center border transition-all duration-700 ${
                            tx.type === "TOPUP"
                              ? "bg-black text-white border-black"
                              : "bg-white border-zinc-100 text-zinc-200 group-hover:border-black group-hover:text-black"
                          }`}
                        >
                          {tx.type === "TOPUP" ? <ArrowDownLeft className="w-7 h-7" /> : <ArrowUpRight className="w-7 h-7" />}
                        </div>
                        <div className="space-y-2">
                          <p className="text-[17px] font-bold text-black tracking-tight group-hover:translate-x-1 transition-transform duration-500">
                            {tx.note || (tx.type === "TOPUP" ? "Nạp năng lượng tri thức" : "Trao đổi tri thức")}
                          </p>
                          <div className="flex items-center gap-4">
                            <p className="text-[10px] text-zinc-300 font-bold uppercase tracking-widest flex items-center gap-2">
                              <History className="w-3 h-3" /> {new Date(tx.created_at).toLocaleString("vi-VN")}
                            </p>
                            <div className="h-[1px] w-4 bg-zinc-100" />
                            <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">ID: {tx._id.slice(-8)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right space-y-3">
                        <p
                          className={`text-3xl font-bold tracking-tighter transition-colors duration-500 ${
                            tx.type === "TOPUP" ? "text-black" : "text-zinc-200 group-hover:text-black"
                          }`}
                        >
                          {tx.type === "TOPUP" ? "+" : "-"}
                          {tx.amount.toLocaleString()} <span className="text-[10px] italic ml-1">dl</span>
                        </p>
                        <div className="flex justify-end">
                          <div
                            className={`inline-flex items-center gap-2 px-3 py-1 border transition-all duration-500 ${
                              tx.status === "COMPLETED"
                                ? "bg-zinc-50 border-zinc-100 text-black"
                                : "bg-white border-zinc-50 text-zinc-200"
                            }`}
                          >
                            <div className={`w-1.5 h-1.5 rounded-full ${tx.status === "COMPLETED" ? "bg-black" : "bg-zinc-200"}`} />
                            <span className="text-[9px] font-bold uppercase tracking-widest">{tx.status}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
