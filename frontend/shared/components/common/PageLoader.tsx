import React from "react";
import { Loader2 } from "lucide-react";

export default function PageLoader({ text = "Đang tải dữ liệu" }: { text?: string }) {
  return (
    <div className="flex flex-col h-[80vh] items-center justify-center font-sans w-full animate-in fade-in duration-500">
      <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
      {text && <p className="text-[15px] font-medium text-[#6E6E73] animate-pulse">{text}</p>}
    </div>
  );
}
