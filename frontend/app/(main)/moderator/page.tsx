"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/app/lib/api";
import { 
  ShieldAlert, 
  Users, 
  FileCheck, 
  CreditCard, 
  BarChart3, 
  CheckCircle2, 
  XCircle, 
  Clock,
  ChevronRight,
  AlertCircle
} from "lucide-react";

export default function ModeratorDashboard() {
  const [reports, setReports] = useState<any[]>([]);
  const [payouts, setPayouts] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"reports" | "payouts" | "metrics">("reports");

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    try {
      const [repRes, payRes, metRes] = await Promise.all([
        fetch(`${API_URL}/moderator/reports`, { headers }),
        fetch(`${API_URL}/moderator/payouts`, { headers }),
        fetch(`${API_URL}/moderator/metrics`, { headers })
      ]);
      
      if (repRes.ok) setReports(await repRes.json());
      if (payRes.ok) setPayouts(await payRes.json());
      if (metRes.ok) setMetrics(await metRes.json());
    } catch (e) {
      console.error("Moderator load error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handlePayout = async (id: string, action: "approve" | "reject") => {
    try {
      const res = await fetch(`${API_URL}/moderator/payouts/${id}/${action}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) fetchData();
    } catch (e) { console.error(e); }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-none animate-spin" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-12 bg-white min-h-screen animate-in fade-in duration-300">
      <header className="border-b border-black pb-8 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <ShieldAlert className="w-5 h-5 text-black" />
            <span className="text-[12px] font-bold tracking-widest text-zinc-400">Kiểm soát hệ thống</span>
          </div>
          <h1 className="text-4xl font-bold text-black tracking-tighter">Bảng điều khiển Kiểm duyệt</h1>
        </div>
        
        <div className="flex gap-1 bg-zinc-50 p-1 border border-zinc-200">
          {(["reports", "payouts", "metrics"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 text-[12px] font-bold tracking-widest transition-all ${activeTab === tab ? "bg-black text-white" : "text-zinc-400 hover:text-black"}`}
            >
              {tab === "reports" ? "Báo cáo" : tab === "payouts" ? "Rút tiền" : "Chỉ số"}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-12">
        {activeTab === "metrics" && metrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 animate-in slide-in-from-bottom-4 duration-500">
            <div className="border border-black p-8">
              <Users className="w-6 h-6 mb-4 text-zinc-400" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-1">Tổng người dùng</span>
              <p className="text-4xl font-bold text-black tracking-tighter">{metrics.total_users?.toLocaleString()}</p>
            </div>
            <div className="border border-black p-8">
              <FileCheck className="w-6 h-6 mb-4 text-zinc-400" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-1">Tài liệu hệ thống</span>
              <p className="text-4xl font-bold text-black tracking-tighter">{metrics.total_documents?.toLocaleString()}</p>
            </div>
            <div className="border border-black p-8">
              <BarChart3 className="w-6 h-6 mb-4 text-zinc-400" />
              <span className="text-[12px] font-bold tracking-widest text-zinc-400 block mb-1">Trạng thái</span>
              <p className="text-4xl font-bold text-black tracking-tighter">Ổn định</p>
            </div>
          </div>
        )}

        {activeTab === "reports" && (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xs font-bold tracking-widest text-black mb-8 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" /> Danh sách báo cáo vi phạm ({reports.length})
            </h2>
            
            {reports.length === 0 ? (
              <div className="py-24 text-center border border-dashed border-zinc-200">
                <p className="text-[12px] font-bold text-zinc-400 tracking-widest">Hàng đợi trống</p>
              </div>
            ) : (
              <div className="border border-black divide-y divide-zinc-100">
                {reports.map((r) => (
                  <div key={r.id} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 hover:bg-zinc-50 transition-colors">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[13px] font-bold bg-black text-white px-2 py-0.5">{r.item_type}</span>
                        <span className="text-[12px] font-bold text-zinc-400 tracking-tight">Bởi: {r.reporter_name}</span>
                      </div>
                      <h3 className="text-sm font-bold text-black mb-1">{r.reason}</h3>
                      <p className="text-xs text-zinc-500 line-clamp-1">{r.description || "Không có mô tả chi tiết"}</p>
                    </div>
                    <div className="flex gap-3">
                      <button className="px-4 py-2 border border-black text-[12px] font-bold tracking-widest hover:bg-black hover:text-white transition-all">Xem nội dung</button>
                      <button className="px-4 py-2 bg-black text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-all">Xử lý</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "payouts" && (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xs font-bold tracking-widest text-black mb-8 flex items-center gap-2">
              <CreditCard className="w-4 h-4" /> Yêu cầu rút tiền đang chờ ({payouts.length})
            </h2>

            {payouts.length === 0 ? (
              <div className="py-24 text-center border border-dashed border-zinc-200">
                <p className="text-[12px] font-bold text-zinc-400 tracking-widest">Không có yêu cầu nào</p>
              </div>
            ) : (
              <div className="border border-black divide-y divide-zinc-100">
                {payouts.map((p) => (
                  <div key={p.id} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 hover:bg-zinc-50 transition-colors">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-[12px] font-bold text-black tracking-widest">ID: {p.user_id?.slice(-6)}</span>
                        <span className="text-[12px] font-bold text-zinc-400 tracking-tight">Tên: {p.user_name}</span>
                      </div>
                      <p className="text-2xl font-bold text-black tracking-tighter">{p.amount?.toLocaleString()} dl</p>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => handlePayout(p.id, "reject")} className="p-3 border border-zinc-200 text-zinc-400 hover:text-black hover:border-black transition-all">
                        <XCircle className="w-5 h-5" />
                      </button>
                      <button onClick={() => handlePayout(p.id, "approve")} className="p-3 bg-black text-white hover:bg-zinc-800 transition-all">
                        <CheckCircle2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
