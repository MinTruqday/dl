"use client";
import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";

export default function ReportModal({ isOpen, onClose, onSubmit }: any) {
  const [reason, setReason] = useState("");
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in duration-300">
      <div className="bg-white p-6 w-full max-w-md border border-zinc-200 animate-in zoom-in-95 duration-300">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-bold text-black flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Báo cáo vi phạm
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-zinc-50 transition-colors duration-150">
            <X className="w-4 h-4 text-zinc-400" />
          </button>
        </div>
        <textarea
          className="w-full p-3 border border-zinc-200 text-sm mb-4 focus:outline-none focus:border-black focus:ring-1 focus:ring-black h-24 resize-none transition-all duration-150"
          placeholder=""
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <button
          onClick={() => onSubmit(reason)}
          className="w-full py-3 bg-black text-white text-[12px] font-bold hover:bg-zinc-800 transition-all duration-150 active:scale-[0.98]"
        >
          Gửi báo cáo
        </button>
      </div>
    </div>
  );
}