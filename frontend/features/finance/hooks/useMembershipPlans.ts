"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  buyMembershipAPI,
  getMembershipPricingAPI,
} from "@/features/finance/services/monetization.service";
import { getWalletBalanceAPI } from "@/features/finance/services/wallet.service";

export type MembershipTier = "BASIC" | "PRO" | "PREMIUM";

type Plan = {
  id: MembershipTier;
  name: string;
  price: number;
  monthlyPrice: number;
  features: string[];
};

const fallbackPlans: Plan[] = [
  {
    id: "BASIC",
    name: "Cơ bản",
    price: 0,
    monthlyPrice: 0,
    features: ["Trợ lý AI tiêu chuẩn", "Đọc và lưu tài liệu", "Công cụ thu thập cơ bản"],
  },
  {
    id: "PRO",
    name: "Chuyên sâu",
    price: 750,
    monthlyPrice: 99000,
    features: ["Gợi ý AI nâng cao", "Hỗ trợ quản trị ưu tiên"],
  },
  {
    id: "PREMIUM",
    name: "Toàn năng",
    price: 2500,
    monthlyPrice: 199000,
    features: ["Không giới hạn số tài liệu", "Kiểm tra mâu thuẫn trong tài liệu"],
  },
];

export function useMembershipPlans() {
  const router = useRouter();
  const { user, refreshUser } = useAuth() as any;
  const [plans, setPlans] = useState<Plan[]>(fallbackPlans);
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState<MembershipTier | "">("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [pricingResponse, walletResponse] = await Promise.all([
        getMembershipPricingAPI(),
        getWalletBalanceAPI(),
      ]);
      const tiers =
        pricingResponse?.data?.tiers || pricingResponse?.tiers || {};
      setPlans(
        fallbackPlans.map((fallback) => ({
          ...fallback,
          name: tiers[fallback.id]?.name || fallback.name,
          monthlyPrice: Number(
            tiers[fallback.id]?.monthly_price ?? fallback.monthlyPrice,
          ),
          price: Number(tiers[fallback.id]?.price_dl ?? fallback.price),
          features: Array.isArray(tiers[fallback.id]?.features)
            ? tiers[fallback.id].features
            : fallback.features,
        })),
      );
      setBalance(
        Number(walletResponse?.data?.balance ?? walletResponse?.balance ?? 0),
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể tải thông tin gói",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const currentTier = useMemo(
    () =>
      (String(user?.role || "").toLowerCase() === "admin"
        ? "PREMIUM"
        : String(user?.ai_tier || "BASIC").toUpperCase()) as MembershipTier,
    [user],
  );

  const buy = async (plan: Plan) => {
    if (plan.id === "BASIC" || buying) return;
    if (balance < plan.price) {
      setError(`Số dư còn thiếu ${plan.price - balance} dl`);
      return;
    }
    setBuying(plan.id);
    setError("");
    setNotice("");
    try {
      await buyMembershipAPI(plan.id);
      setBalance((value) => value - plan.price);
      await refreshUser();
      setNotice(`Đã kích hoạt gói ${plan.name}`);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể nâng cấp gói",
      );
    } finally {
      setBuying("");
    }
  };

  return {
    plans,
    balance,
    currentTier,
    loading,
    buying,
    error,
    notice,
    reload: load,
    buy,
    openWallet: () => router.push("/vi-tien"),
  };
}
