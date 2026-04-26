"use client";

import { useState } from "react";
import { Sparkles, X, Send, Brain, Command } from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";

export default function FloatingAI() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const { user } = useAuth() as any;

  if (!user) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-4 pointer-events-none">
      {isOpen && (
        <div className="w-[380px] bg-white border border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col animate-in slide-in-from-bottom-4 duration-300 pointer-events-auto">
          <header className="p-4 bg-black text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span className="text-[10px] font-bold tracking-widest">Trợ lý AI Phân tán</span>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:opacity-60 transition-opacity">
              <X className="w-4 h-4" />
            </button>
          </header>
          
          <div className="h-80 overflow-y-auto p-6 space-y-4 bg-zinc-50/50">
             <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-black text-white flex items-center justify-center shrink-0">
                   <Brain className="w-4 h-4" />
                </div>
                <div className="bg-white border border-zinc-100 p-3 text-xs font-medium leading-relaxed">
                   Xin chào {user.full_name}, tôi có thể giúp bạn tìm kiếm tài liệu hoặc tóm tắt kiến thức ngay lúc này.
                </div>
             </div>
          </div>

          <div className="p-4 border-t border-zinc-100 bg-white">
             <div className="relative">
                <input 
                   value={query}
                   onChange={e => setQuery(e.target.value)}
                   className="w-full bg-zinc-50 border border-zinc-200 pl-4 pr-12 py-3 text-xs font-bold outline-none focus:border-black transition-all"
                   placeholder="Nhập yêu cầu tại đây"
                />
                <button className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-black text-white flex items-center justify-center hover:bg-zinc-800 transition-colors">
                   <Send className="w-3.5 h-3.5" />
                </button>
             </div>
             <div className="mt-3 flex items-center gap-2 text-[9px] font-bold text-zinc-400 tracking-widest">
                <Command className="w-3 h-3" /> Nhấn Enter để gửi
             </div>
          </div>
        </div>
      )}

      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 bg-black text-white flex items-center justify-center shadow-[4px_4px_0px_0px_rgba(255,255,255,1),4px_4px_0px_2px_rgba(0,0,0,1)] hover:translate-y-[-2px] hover:translate-x-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] active:translate-y-[0px] active:translate-x-[0px] active:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all pointer-events-auto"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Sparkles className="w-6 h-6" />}
      </button>
    </div>
  );
}
