"use client";

import { useEffect, useState } from "react";
import { getMyQuotaAPI, QuotaUsage } from "@/services/quota.service";
import { Cpu, Zap, Activity } from "lucide-react";

export default function QuotaIndicator() {
  const [usage, setUsage] = useState<QuotaUsage | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchQuota = async () => {
    try {
      const data = await getMyQuotaAPI();
      setUsage(data);
    } catch (err) {
      console.error("Lỗi lấy thông tin hạn mức:", err);
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
    <div className="flex flex-col gap-3 p-4 bg-zinc-50 border border-zinc-200 rounded-none animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-black" />
          <span className="text-[10px] font-bold tracking-widest text-black">
            Hạn mức sử dụng ngày
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-medium text-zinc-500 tracking-tighter">
            <span>Yêu cầu</span>
            <span>{usage.used_requests} / {usage.limit_requests}</span>
          </div>
          <div className="h-1 w-full bg-zinc-200 rounded-none overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${reqPercent > 90 ? 'bg-black' : 'bg-zinc-800'}`}
              style={{ width: `${reqPercent}%` }}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-medium text-zinc-500 tracking-tighter">
            <span>Token</span>
            <span>{usage.used_tokens.toLocaleString()} / {usage.limit_tokens.toLocaleString()}</span>
          </div>
          <div className="h-1 w-full bg-zinc-200 rounded-none overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${tokenPercent > 90 ? 'bg-black' : 'bg-zinc-800'}`}
              style={{ width: `${tokenPercent}%` }}
            />
          </div>
        </div>
      </div>
      
      { (reqPercent >= 100 || tokenPercent >= 100) && (
        <p className="text-[10px] font-bold text-black mt-1">
          Đã đạt giới hạn hôm nay
        </p>
      )}
    </div>
  );
}
