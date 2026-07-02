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
      showToast(`Số dư không đủ. Cần thêm ${price - balance} dl`, "error");
      setTimeout(() => router.push("/vi-tien"), 1500);
      return;
    }

    setLoading(tier);
    try {
      showToast(`Nâng cấp gói ${tier} thành công!`, "success");
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
    <div className="w-full min-h-[calc(100vh-56px)] font-sans text-[#1D1D1F] py-12 px-6">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-[40px] md:text-[48px] font-semibold tracking-tight flex items-center justify-center gap-3">
            <Sparkles className="w-8 h-8 text-[#0071E3]" /> Nâng cấp Trải nghiệm
            AI
          </h1>
          <p className="text-[17px] text-[#6E6E73] max-w-2xl mx-auto leading-relaxed">
            Mở khóa sức mạnh của các mô hình AI tiên tiến nhất để tăng tốc quá
            trình sáng tác và nghiên cứu của bạn.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 items-start">
          <div className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-8 flex flex-col h-full hover: transition-">
            <div className="mb-8">
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-2">
                Cơ bản
              </p>
              <p className="text-[14px] text-[#6E6E73] min-h-[40px]">
                Trải nghiệm AI giới hạn dành cho người dùng mới.
              </p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-[32px] font-semibold text-[#1D1D1F]">
                  Miễn phí
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              {[
                "Mô hình ngôn ngữ tiêu chuẩn",
                "10 lượt trò chuyện / ngày",
                "Tối đa 3.000 token / ngày",
                "Phân tích tối đa 1 tài liệu",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-[#1D1D1F]"
                >
                  <Check className="w-5 h-5 text-[#34C759] shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              disabled
              className="w-full py-3.5 rounded-full text-[15px] font-medium bg-[#F5F5F7] text-[#86868B] cursor-not-allowed"
            >
              {getTierState("BASIC") === "CURRENT"
                ? "Gói hiện tại"
                : "Mặc định"}
            </button>
          </div>

          <div className="bg-[#1D1D1F] rounded-[18px] border border-[#333336] p-8 flex flex-col h-full relative transform md:-translate-y-4">
            <div className="absolute top-0 right-8 bg-[#0071E3] text-white px-4 py-1.5 text-[12px] font-medium rounded-b-lg">
              Phổ biến nhất
            </div>
            <div className="mb-8 mt-4">
              <h3 className="text-[17px] font-medium text-white mb-2">
                Nâng cao
              </h3>
              <p className="text-[14px] text-[#A1A1A6] min-h-[40px]">
                Phù hợp cho tác giả và nhà nghiên cứu bán chuyên.
              </p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-[32px] font-semibold text-white">
                  750
                </span>
                <span className="text-[14px] font-medium text-[#A1A1A6]">
                  dl / tháng
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-[14px] text-white">
                <Check className="w-5 h-5 text-[#34C759] shrink-0" />{" "}
                <span className="font-semibold">
                  Mọi tính năng của gói Cơ bản
                </span>
              </li>
              {[
                "Mô hình ngôn ngữ thông minh",
                "25 lượt trò chuyện / ngày",
                "Tối đa 7.500 token / ngày",
                "Phân tích tối đa 5 tài liệu",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-[#D1D1D6]"
                >
                  <Check className="w-5 h-5 text-[#34C759] shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleUpgrade("PRO", 750)}
              disabled={!!loading || getTierState("PRO") !== "AVAILABLE"}
              className={`w-full py-3.5 rounded-full text-[15px] font-medium flex items-center justify-center gap-2 ${getTierState("PRO") === "CURRENT" ? "bg-[#333336] text-[#A1A1A6]" : getTierState("PRO") === "DOWNGRADE" || getTierState("PRO") === "ADMIN" ? "bg-[#333336] text-[#6E6E73] cursor-not-allowed" : "bg-[#0071E3] text-white hover:bg-[#0077ED] transition-colors"}`}
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

          <div className="bg-[#F5F5F7] rounded-[18px] border-[#E8E8ED] p-8 flex flex-col h-full hover: transition-">
            <div className="mb-8">
              <p className="text-[13px] font-medium text-[#6E6E73] mb-4 mb-2">
                Cao cấp
              </p>
              <p className="text-[14px] text-[#6E6E73] min-h-[40px]">
                Dành cho chuyên gia cần sức mạnh xử lý tối đa.
              </p>
              <div className="mt-6 flex items-baseline gap-2">
                <span className="text-[32px] font-semibold text-[#1D1D1F]">
                  2.500
                </span>
                <span className="text-[14px] font-medium text-[#6E6E73]">
                  dl / tháng
                </span>
              </div>
            </div>
            <ul className="space-y-4 mb-8 flex-1">
              <li className="flex items-start gap-3 text-[14px] text-[#1D1D1F]">
                <Check className="w-5 h-5 text-[#34C759] shrink-0" />{" "}
                <span className="font-semibold">
                  Mọi tính năng của gói Nâng cao
                </span>
              </li>
              {[
                "Kích hoạt chế độ suy nghĩ sâu",
                "Mở khóa AI trên soạn thảo",
                "100 lượt trò chuyện / ngày",
                "Tối đa 30.000 token / ngày",
                "Không giới hạn số lượng tài liệu",
              ].map((f, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-[14px] text-[#1D1D1F]"
                >
                  <Check className="w-5 h-5 text-[#34C759] shrink-0" /> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleUpgrade("PREMIUM", 2500)}
              disabled={!!loading || getTierState("PREMIUM") !== "AVAILABLE"}
              className={`w-full py-3.5 rounded-full text-[15px] font-medium flex items-center justify-center gap-2 ${getTierState("PREMIUM") === "CURRENT" || getTierState("PREMIUM") === "ADMIN" ? "bg-[#F5F5F7] text-[#86868B] cursor-not-allowed" : "bg-[#1D1D1F] text-white hover:bg-[#333336] transition-colors"}`}
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

        <div className="flex items-center justify-center gap-2 text-[13px] text-[#6E6E73]">
          <AlertCircle className="w-4 h-4" /> Giao dịch sẽ trừ trực tiếp vào số
          dư (dl) trong ví của bạn. Tỷ giá quy đổi 1 dl = 1.000 VNĐ.
        </div>
      </div>
    </div>
  );
}
