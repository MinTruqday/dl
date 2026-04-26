"use client";

import { useEffect, useState } from "react";
import { Shield, Activity, Database, Server, Cpu, HardDrive, AlertCircle, CheckCircle, RefreshCcw } from "lucide-react";

export default function SupremeAdminDashboard() {
  const [health, setHealth] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const healthRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
      if (healthRes.ok) setHealth(await healthRes.json());
      
      const logsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/audit-logs`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('doclib_token')}` }
      });
      if (logsRes.ok) setLogs(await logsRes.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="border-b-2 border-black pb-8 mb-12 flex justify-between items-end">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Shield className="w-5 h-5 text-black" />
              <span className="text-[10px] font-bold tracking-widest text-zinc-400">Hệ thống tối cao</span>
           </div>
           <h1 className="text-4xl font-black text-black tracking-tighter">Bảng điều khiển Hệ thống</h1>
        </div>
        <button 
           onClick={fetchData}
           className="p-3 border border-black hover:bg-black hover:text-white transition-all"
        >
           <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
         <div className="border border-black p-8 space-y-6">
            <div className="flex items-center justify-between">
               <Activity className="w-6 h-6 text-black" />
               <span className={`text-[10px] font-black tracking-widest px-3 py-1 ${health?.status === 'ok' ? 'bg-black text-white' : 'bg-zinc-200 text-black border border-black'}`}>
                  {health?.status || 'Đang kiểm tra'}
               </span>
            </div>
            <div className="space-y-1">
               <h3 className="text-sm font-black tracking-tight">Dịch vụ hệ thống</h3>
               <p className="text-[10px] text-zinc-400 font-bold tracking-widest">v{health?.version || '1.0.0'}</p>
            </div>
            <div className="pt-4 border-t border-zinc-100 flex items-center gap-2">
               <CheckCircle className={`w-3.5 h-3.5 ${health?.status === 'ok' ? 'text-black' : 'text-zinc-300'}`} />
               <span className="text-xs font-bold tracking-tighter">Hoạt động bình thường</span>
            </div>
         </div>

         <div className="border border-black p-8 space-y-6">
            <div className="flex items-center justify-between">
               <Database className="w-6 h-6 text-black" />
               <span className={`text-[10px] font-black tracking-widest px-3 py-1 ${health?.services.mongodb === 'ok' ? 'bg-black text-white' : 'bg-zinc-200 text-black border border-black'}`}>
                  {health?.services.mongodb || 'Đang kiểm tra'}
               </span>
            </div>
            <div className="space-y-1">
               <h3 className="text-sm font-black tracking-tight">Lưu trữ dữ liệu</h3>
               <p className="text-[10px] text-zinc-400 font-bold tracking-widest">Cụm dữ liệu chính</p>
            </div>
            <div className="pt-4 border-t border-zinc-100 flex items-center gap-2">
               {health?.services.mongodb === 'ok' ? <CheckCircle className="w-3.5 h-3.5 text-black" /> : <AlertCircle className="w-3.5 h-3.5 text-zinc-400" />}
               <span className="text-xs font-bold tracking-tighter">
                  {health?.services.mongodb === 'ok' ? 'Kết nối ổn định' : 'Mất kết nối'}
               </span>
            </div>
         </div>

         <div className="border border-black p-8 space-y-6">
            <div className="flex items-center justify-between">
               <Server className="w-6 h-6 text-black" />
               <span className={`text-[10px] font-black tracking-widest px-3 py-1 ${health?.services.redis === 'ok' ? 'bg-black text-white' : 'bg-zinc-100 text-zinc-400'}`}>
                  {health?.services.redis || 'Không khả dụng'}
               </span>
            </div>
            <div className="space-y-1">
               <h3 className="text-sm font-black tracking-tight">Bộ đệm hệ thống</h3>
               <p className="text-[10px] text-zinc-400 font-bold tracking-widest">Bộ đệm phân tán</p>
            </div>
            <div className="pt-4 border-t border-zinc-100 flex items-center gap-2">
               {health?.services.redis === 'ok' ? <CheckCircle className="w-3.5 h-3.5 text-black" /> : <AlertCircle className="w-3.5 h-3.5 text-zinc-300" />}
               <span className="text-xs font-bold tracking-tighter">
                  {health?.services.redis === 'ok' ? 'Đã tối ưu hóa' : 'Không khả dụng'}
               </span>
            </div>
         </div>
      </div>

      <div className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-12">
         <div className="border border-black p-10 space-y-8">
            <h2 className="text-xl font-black tracking-tighter border-l-4 border-black pl-4">Tài nguyên máy chủ</h2>
            <div className="space-y-6">
               {[
                  { label: "Sử dụng CPU", val: health?.resources?.cpu_usage || "Không khả dụng", icon: <Cpu className="w-4 h-4" /> },
                  { label: "Bộ nhớ RAM", val: health?.resources?.memory_usage || "Không khả dụng", icon: <HardDrive className="w-4 h-4" /> },
                  { label: "Lưu trữ đĩa", val: health?.resources?.disk_usage || "Không khả dụng", icon: <Server className="w-4 h-4" /> }
               ].map((stat, i) => (
                  <div key={i} className="space-y-2">
                     <div className="flex justify-between items-end">
                        <div className="flex items-center gap-2">
                           {stat.icon}
                           <span className="text-[10px] font-bold tracking-widest text-zinc-500">{stat.label}</span>
                        </div>
                        <span className="text-sm font-black">{stat.val}</span>
                     </div>
                     <div className="w-full h-1.5 bg-zinc-100 overflow-hidden">
                        <div className="bg-black h-full" style={{ width: stat.val === "Không khả dụng" ? "0%" : stat.val }} />
                     </div>
                  </div>
               ))}
            </div>
         </div>

         <div className="border border-black p-10 space-y-8">
            <h2 className="text-xl font-black tracking-tighter border-l-4 border-black pl-4">Bảo trì & Sao lưu</h2>
            <div className="space-y-6">
               <div className="p-6 bg-zinc-50 border border-zinc-100 space-y-4">
                  <div className="flex justify-between items-center">
                     <p className="text-xs font-black tracking-tight">Sao lưu dữ liệu</p>
                     <span className="text-[9px] font-bold text-zinc-400">Hàng ngày @ 03:00</span>
                  </div>
                  <button className="w-full py-3 border border-black text-[10px] font-bold tracking-widest hover:bg-black hover:text-white transition-all">
                     Thực hiện sao lưu
                  </button>
               </div>
               <div className="p-6 bg-zinc-50 border border-zinc-100 space-y-4">
                  <div className="flex justify-between items-center">
                     <p className="text-xs font-black tracking-tight">Dọn dẹp bộ đệm</p>
                     <span className="text-[9px] font-bold text-zinc-400">Sử dụng: 42.5 MB</span>
                  </div>
                  <button className="w-full py-3 border border-black text-[10px] font-bold tracking-widest hover:bg-black hover:text-white transition-all">
                     Làm trống bộ đệm
                  </button>
               </div>
            </div>
         </div>

         <div className="border border-black p-10 space-y-8 lg:col-span-2">
            <div className="flex items-center justify-between">
               <h2 className="text-xl font-black tracking-tighter border-l-4 border-black pl-4">Nhật ký Hệ thống Toàn cầu</h2>
               <button className="text-[10px] font-bold tracking-widest text-zinc-400 hover:text-black underline">Tải xuống CSV</button>
            </div>
            <div className="space-y-1">
               <div className="grid grid-cols-12 px-4 py-3 bg-zinc-100 text-[10px] font-black tracking-widest text-zinc-500">
                  <div className="col-span-2">Thời gian</div>
                  <div className="col-span-3">Quản trị viên</div>
                  <div className="col-span-4">Hành động</div>
                  <div className="col-span-3 text-right">Trạng thái</div>
               </div>
               <div className="divide-y divide-zinc-100 border border-zinc-100">
                  {logs.length > 0 ? logs.map((log: any, i: number) => (
                     <div key={i} className="grid grid-cols-12 px-4 py-4 text-[11px] font-bold tracking-tight hover:bg-zinc-50 transition-colors items-center">
                        <div className="col-span-2 tabular-nums text-zinc-400">{log.time}</div>
                        <div className="col-span-3 truncate pr-4">{log.admin}</div>
                        <div className="col-span-4 truncate pr-4">{log.action}</div>
                        <div className="col-span-3 text-right">
                           <span className={`px-2 py-1 ${log.status === 'SUCCESS' ? 'bg-black text-white' : 'bg-zinc-100 text-zinc-500'}`}>
                              {log.status}
                           </span>
                        </div>
                     </div>
                  )) : (
                     <div className="py-8 text-center text-zinc-500 text-xs">Không có dữ liệu nhật ký</div>
                  )}
               </div>
            </div>
         </div>
      </div>
    </div>
  );
}
