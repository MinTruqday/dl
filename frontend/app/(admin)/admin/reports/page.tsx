"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import {
  AlertTriangle,
  Loader2,
  RefreshCcw,
  ShieldCheck,
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  MessageSquare,
  Filter
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function ReportsManagementPage() {
  const { user, isLoading } = useAuth() as any;
  const [reports, setReports] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const res = await fetch(`${API_URL}/admin/reports`, { headers });
      if (res.ok) {
        const data = await res.json();
        setReports(data.data || data || []);
      }
    } catch (err: any) {
      console.error("Lỗi tải báo cáo:", err);
    } finally {
      setIsRefreshing(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!isLoading && (user?.role === "admin" || user?.role === "moderator")) {
      fetchData();
    }
  }, [user, isLoading, fetchData]);

  const resolveReport = async (reportId: string, action: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/reports/${reportId}/resolve`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã xử lý báo cáo vi phạm." });
        fetchData();
      }
    } catch (err: any) {
      console.error("Lỗi xử lý báo cáo:", err);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      <div 
        className="mb-10 border-b border-zinc-100 pb-10 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tighter leading-none">Vi phạm & Báo cáo</h1>
            <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
              Giám sát cộng đồng & Xử lý khiếu nại <AlertTriangle className="w-3.5 h-3.5" />
            </p>
          </div>
          
          <button 
            onClick={fetchData}
            disabled={isRefreshing}
            className="h-14 px-12 bg-black text-white text-[10px] font-bold tracking-[0.2em] uppercase hover:bg-zinc-800 transition-all flex items-center gap-4 shadow-xl shadow-black/5"
          >
            {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
            Đồng bộ dữ liệu
          </button>
        </div>
      </div>

      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="bg-white border border-zinc-100 overflow-hidden shadow-sm">
             <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Đối tượng bị báo cáo</th>
                      <th className="px-10 py-6">Nội dung vi phạm</th>
                      <th className="px-10 py-6">Người báo cáo</th>
                      <th className="px-10 py-6 text-right">Xử lý</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {reports.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-10 py-32 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest italic">
                          Hệ thống hiện tại sạch bóng vi phạm
                        </td>
                      </tr>
                    ) : (
                      reports.map((report: any) => (
                        <tr key={report._id} className="hover:bg-zinc-50/20 transition-colors group">
                          <td className="px-10 py-8">
                              <div className="flex flex-col gap-1">
                                  <span className="font-bold text-black uppercase tracking-widest text-[10px]">{report.target_type}</span>
                                  <span className="text-[9px] font-bold text-zinc-300">ID: {report.target_id}</span>
                              </div>
                          </td>
                          <td className="px-10 py-8">
                              <div className="space-y-1">
                                <span className="px-2 py-0.5 bg-red-50 text-red-500 text-[8px] font-black uppercase tracking-widest border border-red-100">{report.reason}</span>
                                <p className="text-[11px] text-zinc-500 font-medium italic line-clamp-1">"{report.description}"</p>
                              </div>
                          </td>
                          <td className="px-10 py-8">
                              <div className="flex items-center gap-2">
                                  <div className="w-6 h-6 bg-zinc-100 flex items-center justify-center text-[10px] font-bold">
                                      {report.reporter_name?.[0] || "R"}
                                  </div>
                                  <span className="text-[10px] font-bold text-zinc-300">{report.reporter_name}</span>
                              </div>
                          </td>
                          <td className="px-10 py-8 text-right">
                              <div className="flex justify-end gap-3">
                                  <button 
                                      onClick={() => resolveReport(report._id, "DISMISSED")}
                                      className="h-9 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all"
                                  >
                                      Bỏ qua
                                  </button>
                                  <button 
                                      onClick={() => resolveReport(report._id, "RESOLVED")}
                                      className="h-9 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98]"
                                  >
                                      Xử lý vi phạm
                                  </button>
                              </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
             </div>
          </div>
      </div>
    </div>
  );
}
