"use client";

import { useEffect, useState } from "react";
import { Clock, BookOpen, Trash2, Calendar, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function ReadingHistoryPage() {
  const [history, setHistory] = useState([
    { id: "1", title: "Kinh tế học cơ bản", author: "Thomas Sowell", date: "2024-04-23T10:30:00Z", progress: 45, slug: "kinh-te-hoc-co-ban" },
    { id: "2", title: "Thiết kế hệ thống", author: "Alex Xu", date: "2024-04-22T15:20:00Z", progress: 100, slug: "thiet-ke-he-thong" },
    { id: "3", title: "Blockchain & Web3", author: "Vitalik Buterin", date: "2024-04-20T08:45:00Z", progress: 12, slug: "blockchain-web3" }
  ]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Clock className="w-5 h-5 text-black" />
              <span className="text-[10px] font-bold tracking-widest text-zinc-400">Dấu chân tri thức</span>
           </div>
           <h1 className="text-4xl font-black text-black tracking-tighter">Lịch sử đọc</h1>
        </div>
        <div className="flex gap-4">
           <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input 
                 className="bg-zinc-50 border border-zinc-200 pl-10 pr-4 py-2 text-xs font-bold tracking-widest outline-none focus:border-black transition-all"
                 placeholder="Tìm trong lịch sử"
              />
           </div>
           <Button variant="outline" className="text-[10px] font-bold tracking-widest border-black h-10 px-6">
              <Trash2 className="w-4 h-4 mr-2" /> Xóa toàn bộ
           </Button>
        </div>
      </header>

      <div className="space-y-4">
        {history.map((item) => (
          <div key={item.id} className="group border border-black p-6 flex flex-col md:flex-row items-center gap-8 hover:bg-zinc-50 transition-all duration-300">
             <div className="w-16 h-20 bg-zinc-100 border border-zinc-200 shrink-0 flex items-center justify-center font-black text-zinc-200 text-xs text-center p-2">
                {item.title}
             </div>
             
             <div className="flex-1 space-y-2">
                <div className="flex items-center gap-3 text-[9px] font-bold tracking-widest text-zinc-400">
                   <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> {new Date(item.date).toLocaleDateString("vi-VN")}</span>
                   <span className="w-1 h-1 rounded-none bg-zinc-200" />
                   <span>{item.author}</span>
                </div>
                <h3 className="text-lg font-black tracking-tighter">{item.title}</h3>
                <div className="w-full bg-zinc-100 h-1.5 rounded-none overflow-hidden">
                   <div className="bg-black h-full transition-all duration-500" style={{ width: `${item.progress}%` }} />
                </div>
                <p className="text-[9px] font-bold tracking-widest text-zinc-400">Tiến độ: {item.progress}%</p>
             </div>

             <div className="flex items-center gap-4">
                <Link href={`/preview/${item.slug}`} className="bg-black text-white text-[10px] font-bold tracking-widest px-6 py-3 hover:bg-zinc-800 transition-all">
                   Đọc tiếp
                </Link>
                <button className="p-3 border border-zinc-100 hover:border-black transition-all group/btn">
                   <Trash2 className="w-4 h-4 text-zinc-300 group-hover/btn:text-black" />
                </button>
             </div>
          </div>
        ))}

        {history.length === 0 && (
           <div className="py-24 text-center border border-dashed border-zinc-200 bg-zinc-50/50">
              <p className="text-[10px] font-bold tracking-widest text-zinc-300">Bạn chưa đọc tài liệu nào gần đây.</p>
           </div>
        )}
      </div>
    </div>
  );
}
