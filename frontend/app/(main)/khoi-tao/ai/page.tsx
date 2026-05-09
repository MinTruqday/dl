"use client";

import { ShieldCheck } from "lucide-react";

export default function AICofigPage() {
  return (
    <div className="border border-zinc-200 bg-zinc-50 p-24 text-center flex flex-col items-center justify-center space-y-6 rounded-none">
      <ShieldCheck className="w-10 h-10 text-zinc-400" />
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-black uppercase tracking-widest">
          Cấu hình AI
        </h3>
        <p className="text-xs font-medium text-zinc-500">
          Tính năng đang được phát triển
        </p>
      </div>
    </div>
  );
}
