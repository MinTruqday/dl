"use client";

import { useState, useEffect } from "react";
import { Activity } from "lucide-react";
import { getMyQuotaAPI, QuotaUsage } from "@/features/provision/services/usage_quota.service";

export default function QuotaIndicator() {
  const [usage, setUsage] = useState<QuotaUsage | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchQuota = async () => {
    try {
      const data = await getMyQuotaAPI();
      setUsage(data);
    } catch (err) {
      console.error("Error loading quota info:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuota();
    const interval = setInterval(fetchQuota, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !usage) return null;

  const reqPercent = Math.min(100, (usage.used_requests / usage.limit_requests) * 100);
  const tokenPercent = Math.min(100, (usage.used_tokens / usage.limit_tokens) * 100);

  return (
    <div className="flex flex-col gap-3 p-4 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px]">
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-[#0071E3]" />
        <span className="text-[12px] font-semibold text-[#1D1D1F]">
          Hạn mức sử dụng ngày
        </span>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[#6E6E73]">
            <span>Yêu cầu</span>
            <span>{usage.used_requests} / {usage.limit_requests}</span>
          </div>
          <div className="h-1.5 w-full bg-[#E8E8ED] rounded-full overflow-hidden">
            <div className={`h-full ${reqPercent > 90 ? "bg-[#FF3B30]" : "bg-[#0071E3]"}`} style={{ width: `${reqPercent}%` }} />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium text-[#6E6E73]">
            <span>Token</span>
            <span>{usage.used_tokens.toLocaleString()} / {usage.limit_tokens.toLocaleString()}</span>
          </div>
          <div className="h-1.5 w-full bg-[#E8E8ED] rounded-full overflow-hidden">
            <div className={`h-full ${tokenPercent > 90 ? "bg-[#FF3B30]" : "bg-[#0071E3]"}`} style={{ width: `${tokenPercent}%` }} />
          </div>
        </div>
      </div>

      {(reqPercent >= 100 || tokenPercent >= 100) && (
        <p className="text-[12px] font-semibold text-[#FF3B30] mt-1">Đã đạt giới hạn hôm nay</p>
      )}
    </div>
  );
}
