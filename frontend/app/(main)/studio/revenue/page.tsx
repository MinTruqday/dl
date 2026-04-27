"use client";

import { useEffect, useState } from "react";
import { getAuthorRevenueAPI } from "@/app/lib/api";
import { CreditCard, TrendingUp, DollarSign, ArrowUpRight, ArrowDownRight, Package, Calendar, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AuthorRevenuePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRevenue();
  }, []);

  const loadRevenue = async () => {
    setLoading(true);
    try {
      const res = await getAuthorRevenueAPI();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-black" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400">Tài chính tác giả</span>
           </div>
           <h1 className="text-4xl font-bold text-black tracking-tighter">Thống kê doanh thu</h1>
        </div>
        <Button variant="outline" className="text-[12px] font-bold tracking-widest border-black h-12 px-8">
           <Download className="w-4 h-4 mr-2" /> Xuất báo cáo (CSV)
        </Button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
         <div className="border border-black p-8 bg-black text-white space-y-4">
            <div className="flex justify-between items-start">
               <span className="text-[12px] font-bold tracking-widest text-zinc-400">Tổng doanh thu</span>
               <DollarSign className="w-4 h-4" />
            </div>
            <h2 className="text-4xl font-bold tracking-tighter">{(data?.total_revenue || 0).toLocaleString()} dl</h2>
            <div className="flex items-center gap-2 text-[12px] font-bold text-zinc-400">
               <ArrowUpRight className="w-3 h-3" /> +12.5% so với tháng trước
            </div>
         </div>
         <div className="border border-black p-8 bg-white space-y-4">
            <div className="flex justify-between items-start">
               <span className="text-[12px] font-bold tracking-widest text-zinc-400">Tổng lượt bán</span>
               <Package className="w-4 h-4" />
            </div>
            <h2 className="text-4xl font-bold tracking-tighter">{(data?.total_sales || 0).toLocaleString()}</h2>
            <p className="text-[12px] font-bold text-zinc-400 tracking-widest">Giao dịch thành công</p>
         </div>
         <div className="border border-black p-8 bg-white space-y-4">
            <div className="flex justify-between items-start">
               <span className="text-[12px] font-bold tracking-widest text-zinc-400">Lượt xem tài liệu</span>
               <TrendingUp className="w-4 h-4" />
            </div>
            <h2 className="text-4xl font-bold tracking-tighter">{(data?.total_views || 0).toLocaleString()}</h2>
            <div className="flex items-center gap-2 text-[12px] font-bold text-zinc-400">
               <ArrowDownRight className="w-3 h-3" /> -2.1% tỷ lệ chuyển đổi
            </div>
         </div>
      </div>

      <div className="space-y-8">
         <div className="flex items-center justify-between border-b border-zinc-100 pb-4">
            <h3 className="text-sm font-bold tracking-tighter flex items-center gap-2">
               <Calendar className="w-5 h-5" />
               Lịch sử giao dịch gần đây
            </h3>
         </div>

         <div className="border border-black divide-y divide-zinc-100">
            {data?.recent_sales?.map((sale: any, idx: number) => (
               <div key={idx} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:bg-zinc-50 transition-colors">
                  <div className="space-y-1">
                     <p className="text-sm font-bold tracking-tight">{sale.document_title}</p>
                     <p className="text-[12px] font-bold text-zinc-400 tracking-widest">
                        {new Date(sale.date).toLocaleString("vi-VN")}
                     </p>
                  </div>
                  <div className="flex items-center gap-8">
                     <div className="text-right">
                        <p className="text-sm font-bold">+{sale.price.toLocaleString()} dl</p>
                        <p className="text-[13px] font-bold text-black tracking-widest">Thành công</p>
                     </div>
                     <ArrowUpRight className="w-5 h-5 text-zinc-200" />
                  </div>
               </div>
            ))}

            {(!data?.recent_sales || data.recent_sales.length === 0) && (
               <div className="py-24 text-center bg-zinc-50/50">
                  <p className="text-[12px] font-bold tracking-widest text-zinc-300">Chưa có giao dịch phát sinh.</p>
               </div>
            )}
         </div>
      </div>
    </div>
  );
}
