"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/contexts/Auth";
import { useToast } from "@/shared/contexts/Toast";

import { getWalletBalanceAPI } from "@/features/finance/services/account_ledger.service";
import { Check, Sparkles, Loader2, Zap, Brain, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function UpgradePage() {
  const { user, loginState } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();
  const [balance, setBalance] = useState<number>(0);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      getWalletBalanceAPI()
        .then((res: any) => setBalance(res.data?.balance || res.balance || 0))
        .catch(() => {});
    }
  }, [user]);

  const handleUpgrade = async (tier: "PRO" | "PREMIUM", price: number) => {
    if (!user) {
      router.push("/login");
      return;
    }
    if (balance < price) {
      showToast(`Số dư không đủ. Cần thêm ${price - balance} dl`, "error");
      setTimeout(() => router.push("/wallet"), 1500);
      return;
    }

    setLoading(tier);
    try {
      await // processDepositAPI(tier);
      showToast(`Nâng cấp gói ${tier} thành công!`, "success");
      // Trigger a re-fetch of user info or token refresh
      // Since ai_tier is likely stored in token or fetched via /me, reload window
      setTimeout(() => window.location.reload(), 1000);
    } catch (err: any) {
      showToast(err.message || "Lỗi nâng cấp gói AI", "error");
    } finally {
      setLoading(null);
    }
  };

  const getTierState = (tier: string) => {
    const userTier = user?.ai_tier || "BASIC";
    if (user?.role === "admin") return "ADMIN";
    if (userTier === tier) return "CURRENT";
    if (userTier === "PREMIUM" && tier === "PRO") return "DOWNGRADE";
    return "AVAILABLE";
  };

  return (
    <div className="w-full min-h-[calc(100vh-var(--navbar-height))] bg-zinc-50 py-12 px-6">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-black tracking-tight flex items-center justify-center gap-3">
            <Sparkles className="w-8 h-8 text-black" />
            Nâng cấp Trải nghiệm AI
          </h1>
          <p className="text-lg text-zinc-500 font-medium max-w-2xl mx-auto">
            Mở khóa sức mạnh của các mô hình AI tiên tiến nhất để tăng tốc quá trình sáng tác và nghiên cứu của bạn.
          </p>
          
          {user && (
            <div className="inline-flex items-center gap-2 bg-white px-4 py-2 rounded-full border border-zinc-200 shadow-sm mt-4">
              <span className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Số dư ví:</span>
              <span className="text-sm font-bold text-black">{balance.toLocaleString()} dl</span>
              <Link href="/wallet" className="text-xs text-blue-600 font-medium hover:underline ml-2">Nạp thêm</Link>
            </div>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {/* BASIC TIER */}
          <div className="bg-white rounded-3xl p-8 border border-zinc-200 shadow-sm relative overflow-hidden flex flex-col h-full">
            <div className="mb-8">
              <h3 className="text-xl font-bold text-black mb-2">Cơ bản</h3>
              <p className="text-sm text-zinc-500 font-medium min-h-[40px]">Trải nghiệm AI giới hạn dành cho người dùng mới.</p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-4xl font-bold text-black">Miễn phí</span>
              </div>
            </div>
            
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Mô hình Qwen tiêu chuẩn
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                10 lượt trò chuyện / ngày
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Tối đa 3.000 token / ngày
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Phân tích tối đa 1 tài liệu
              </li>
            </ul>

            <button
              disabled
              className="w-full py-4 rounded-xl text-sm font-bold bg-zinc-100 text-zinc-500 cursor-not-allowed"
            >
              {getTierState("BASIC") === "CURRENT" ? "Gói hiện tại" : "Mặc định"}
            </button>
          </div>

          {/* PRO TIER */}
          <div className="bg-white rounded-3xl p-8 border-2 border-black shadow-xl relative overflow-hidden flex flex-col h-full transform md:-translate-y-4">
            <div className="absolute top-0 right-0 bg-black text-white px-4 py-1 text-[10px] font-bold uppercase tracking-widest rounded-bl-xl">
              Phổ biến nhất
            </div>
            <div className="mb-8 mt-4">
              <h3 className="text-xl font-bold text-black mb-2 flex items-center gap-2">
                <Zap className="w-5 h-5 text-black" />
                Nâng cao
              </h3>
              <p className="text-sm text-zinc-500 font-medium min-h-[40px]">Phù hợp cho tác giả và nhà nghiên cứu bán chuyên.</p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-4xl font-bold text-black">750</span>
                <span className="text-sm font-bold text-zinc-500">dl / chu kỳ</span>
              </div>
            </div>
            
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-sm text-zinc-800 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                <span className="font-bold">Mọi tính năng của gói Cơ bản</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                25 lượt trò chuyện / ngày
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Tối đa 7.500 token / ngày
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Thời gian nạp lại quota: 5 tiếng
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-600 font-medium">
                <Check className="w-5 h-5 text-black shrink-0" />
                Phân tích tối đa 5 tài liệu cùng lúc
              </li>
            </ul>

            <button
              onClick={() => handleUpgrade("PRO", 750)}
              disabled={!!loading || getTierState("PRO") !== "AVAILABLE"}
              className={`w-full py-4 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                getTierState("PRO") === "CURRENT" ? "bg-zinc-100 text-zinc-500" :
                getTierState("PRO") === "DOWNGRADE" || getTierState("PRO") === "ADMIN" ? "bg-zinc-100 text-zinc-400 cursor-not-allowed" :
                "bg-black text-white hover:bg-zinc-800 hover:shadow-lg active:scale-[0.98]"
              }`}
            >
              {loading === "PRO" ? <Loader2 className="w-5 h-5 animate-spin" /> : 
                getTierState("PRO") === "CURRENT" ? "Gói hiện tại" : 
                getTierState("PRO") === "ADMIN" ? "Quản trị viên" :
                "Nâng cấp ngay"
              }
            </button>
          </div>

          {/* PREMIUM TIER */}
          <div className="bg-black rounded-3xl p-8 border border-black shadow-2xl relative overflow-hidden flex flex-col h-full text-white">
            <div className="absolute -right-12 -top-12 opacity-10">
              <Brain className="w-48 h-48" />
            </div>
            <div className="mb-8 relative z-10">
              <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Cao cấp
              </h3>
              <p className="text-sm text-zinc-400 font-medium min-h-[40px]">Dành cho chuyên gia cần sức mạnh xử lý tối đa.</p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-4xl font-bold">2.500</span>
                <span className="text-sm font-bold text-zinc-400">dl / chu kỳ</span>
              </div>
            </div>
            
            <ul className="space-y-4 mb-8 flex-1 relative z-10">
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                <span className="font-bold">Mọi tính năng của gói Nâng cao</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                <span className="text-white bg-white/20 px-1.5 py-0.5 rounded font-bold">Model Llama 4</span> thông minh nhất
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                Kích hoạt <span className="font-bold italic">Chế độ Suy nghĩ</span>
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                Mở khóa mọi tính năng AI trên Editor
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                100 lượt trò chuyện & 30.000 token / ngày
              </li>
              <li className="flex items-start gap-3 text-sm text-zinc-200 font-medium">
                <Check className="w-5 h-5 text-white shrink-0" />
                Không giới hạn số lượng tài liệu
              </li>
            </ul>

            <button
              onClick={() => handleUpgrade("PREMIUM", 2500)}
              disabled={!!loading || getTierState("PREMIUM") !== "AVAILABLE"}
              className={`w-full py-4 rounded-xl text-sm font-bold transition-all relative z-10 flex items-center justify-center gap-2 ${
                getTierState("PREMIUM") === "CURRENT" ? "bg-white/10 text-zinc-500 cursor-not-allowed" :
                getTierState("PREMIUM") === "ADMIN" ? "bg-white/10 text-zinc-500 cursor-not-allowed" :
                "bg-white text-black hover:bg-zinc-100 shadow-[0_0_20px_rgba(255,255,255,0.3)] active:scale-[0.98]"
              }`}
            >
              {loading === "PREMIUM" ? <Loader2 className="w-5 h-5 animate-spin" /> : 
                getTierState("PREMIUM") === "CURRENT" ? "Gói hiện tại" : 
                getTierState("PREMIUM") === "ADMIN" ? "Quản trị viên" :
                "Nâng cấp lên Cao cấp"
              }
            </button>
          </div>

        </div>

        <div className="flex items-center justify-center gap-2 text-xs font-medium text-zinc-400 mt-8">
          <AlertCircle className="w-4 h-4" />
          Giao dịch sẽ trừ trực tiếp vào số dư (dl) trong ví của bạn. Tỷ giá quy đổi 1 dl = 1.000 VNĐ.
        </div>
      </div>
    </div>
  );
}
