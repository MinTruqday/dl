"use client";
import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";

export default function ReportModal({ isOpen, onClose, onSubmit }: any) {
  const [reason, setReason] = useState("");
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 animate-in fade-in">
      <div className="bg-white p-6 w-full max-w-md border border-black">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-bold tracking-widest text-black flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> Báo cáo vi phạm
          </h3>
          <button onClick={onClose}><X className="w-4 h-4 text-zinc-400" /></button>
        </div>
        <textarea 
          className="w-full p-3 border border-border text-sm mb-4 focus:outline-none focus:border-black h-24 resize-none"
          placeholder="Lý do báo cáo"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <button onClick={() => onSubmit(reason)} className="w-full py-3 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800">
          Gửi báo cáo
        </button>
      </div>
    </div>
  );
}