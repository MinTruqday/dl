import React from "react";

export default function EmptyState({ 
  text = "Chưa có dữ liệu", 
  compact = false 
}: { 
  text?: string;
  compact?: boolean;
}) {
  return (
    <div className={`${compact ? "py-12" : "py-24"} flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full animate-in fade-in duration-500`}>
      <p className="text-[17px] text-[#6E6E73]">{text}</p>
    </div>
  );
}
