"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { getWalletBalanceAPI } from "@/features/payment/services/wallet.service";
import { Check, Sparkles, Loader2, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function UpgradePage() {
  const { user } = useAuth() as any;
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
      router.push("/dang-nhap");
      return;
    }
    if (balance < price) {
      showToast(`Lỗi thiếu hụt số dư khả dụng. Cần bổ sung ${price - balance} dl`, "error");
      setTimeout(() => router.push("/vi-tien"), 1500);
      return;
    }

    setLoading(tier);
    try {
      showToast(`Cập nhật cấp độ thành viên ${tier} hoàn tất`, "success");
      setTimeout(() => window.location.reload(), 1000);
    } catch (err: any) {
      showToast(err.message || "Không thể cập nhật cấp độ thành viên", "error");
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
    <div className="w-full h-full font-sans text-ink overflow-y-auto no-scrollbar">
      <div className="w-full space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-[28px] md:text-[32px] font-semibold tracking-tight flex items-center justify-center gap-3">
            Nâng cấp trải nghiệm DocLib
          </h1>
          <p className="text-[17px] text-ink-muted max-w-2xl mx-auto leading-relaxed">
            Mở khóa sức mạnh của các mô hình AI tiên tiến nhất để tăng tốc quá
            trình sáng tác và nghiên cứu của bạn.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 items-stretch">
          <div className="bg-white rounded-panel border border-border p-8 flex flex-col h-full hover:scale-[1.02] transition-transform">
            <div className="mb-10">
              <h3 className="text-[22px] font-semibold text-ink mb-4">
                Cơ bản
              </h3>
              <div className="flex items-baseline gap-2">
                <span className="text-[40px] font-bold text-ink tracking-tight">
                  Miễn phí
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              {[
                "Mô hình ngôn ngữ tiêu chuẩn",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-ink"
                >
                  <Check className="w-5 h-5 text-brand shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              disabled
              className="w-full py-3.5 rounded-full text-[15px] font-medium bg-surface-quiet text-ink-faint cursor-not-allowed"
            >
              {getTierState("BASIC") === "CURRENT"
                ? "Gói hiện tại"
                : "Mặc định"}
            </button>
          </div>

          <div className="bg-white rounded-panel border border-border p-8 flex flex-col h-full hover:scale-[1.02] transition-transform">
            <div className="mb-10">
              <h3 className="text-[22px] font-semibold text-ink mb-4">
                Chuyên sâu
              </h3>
              <div className="flex items-baseline gap-1">
                <span className="text-[40px] font-bold text-ink tracking-tight">
                  750
                </span>
                <span className="text-[16px] font-medium text-ink-muted">
                  dl / tháng
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-[14px] text-ink">
                <Check className="w-5 h-5 text-brand shrink-0" />{" "}
                <span className="font-semibold">
                  Mọi tính năng của gói Cơ bản
                </span>
              </li>
              {[
                "Mô hình ngôn ngữ thông minh",
                "Lượt trò chuyện dài hơn",
                "Bảo mật tài liệu đơn giản",
                "Cấp phát 10GB lưu trữ tài liệu",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-ink"
                >
                  <Check className="w-5 h-5 text-brand shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleUpgrade("PRO", 750)}
              disabled={!!loading || getTierState("PRO") !== "AVAILABLE"}
              className={`w-full py-3.5 rounded-full text-[15px] font-medium flex items-center justify-center gap-2 ${getTierState("PRO") === "CURRENT" || getTierState("PRO") === "DOWNGRADE" || getTierState("PRO") === "ADMIN" ? "bg-surface-quiet text-ink-faint cursor-not-allowed" : "bg-brand text-white hover:bg-brand transition-colors"}`}
            >
              {loading === "PRO" ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : getTierState("PRO") === "CURRENT" ? (
                "Gói hiện tại"
              ) : getTierState("PRO") === "ADMIN" ? (
                "Quản trị viên"
              ) : (
                "Nâng cấp ngay"
              )}
            </button>
          </div>

          <div className="bg-white rounded-panel border border-border p-8 flex flex-col h-full hover:scale-[1.02] transition-transform">
            <div className="mb-10">
              <h3 className="text-[22px] font-semibold text-ink mb-4">
                Toàn năng
              </h3>
              <div className="flex items-baseline gap-1">
                <span className="text-[40px] font-bold text-ink tracking-tight">
                  2.500
                </span>
                <span className="text-[16px] font-medium text-ink-muted">
                  dl / tháng
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-[14px] text-ink">
                <Check className="w-5 h-5 text-brand shrink-0" />{" "}
                <span className="font-semibold">
                  Mọi tính năng của gói Nâng cao
                </span>
              </li>
              {[
                "Kích hoạt chế độ suy nghĩ sâu",
                "Mở khóa AI trên soạn thảo",
                "Lượt trò chuyện tối đa",
                "Bảo mật tài liệu toàn diện",
                "Cấp phát 100GB lưu trữ tài liệu",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-ink"
                >
                  <Check className="w-5 h-5 text-brand shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleUpgrade("PREMIUM", 2500)}
              disabled={!!loading || getTierState("PREMIUM") !== "AVAILABLE"}
              className={`w-full py-3.5 rounded-full text-[15px] font-medium flex items-center justify-center gap-2 ${getTierState("PREMIUM") === "CURRENT" || getTierState("PREMIUM") === "ADMIN" ? "bg-surface-quiet text-ink-faint cursor-not-allowed" : "bg-ink text-white hover:bg-ink transition-colors"}`}
            >
              {loading === "PREMIUM" ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : getTierState("PREMIUM") === "CURRENT" ? (
                "Gói hiện tại"
              ) : getTierState("PREMIUM") === "ADMIN" ? (
                "Quản trị viên"
              ) : (
                "Nâng cấp ngay"
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-[13px] text-ink-muted">
          <AlertCircle className="w-4 h-4" /> Giao dịch sẽ trừ trực tiếp vào số
          dư (dl) trong ví của bạn. Tỷ giá quy đổi 1 dl = 1.000 VNĐ.
        </div>
      </div>
    </div>
  );
}
