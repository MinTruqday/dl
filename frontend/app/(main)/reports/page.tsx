"use client";

import { useEffect, useState, useCallback } from "react";
import { getReportsAPI as getAdminReportsAPI, resolveReportAPI } from "@/services/moderation.service";
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
  Filter,
  Zap,
  MoreVertical,
  ShieldAlert,
  Search,
  ArrowRight,
  UserX
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

export default function ReportsManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await getAdminReportsAPI();
      setReports(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể kết nối máy chủ báo cáo.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, []);

  useEffect(() => {
    if (!authLoading && (user?.role === "admin" || user?.role === "moderator")) {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const handleResolve = async (reportId: string, action: string) => {
    try {
      await resolveReportAPI(reportId, action);
      showToast(action === "RESOLVED" ? "Đã xử lý vi phạm thành công." : "Đã bỏ qua báo cáo.", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý báo cáo.", "error");
    }
  };

  const filteredReports = reports.filter(r => 
    (r.reason || "").toLowerCase().includes(searchQuery.toLowerCase()) || 
    (r.target_id || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.reporter_name || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
        

        <div 
          className="mb-12 border-b border-zinc-100 pb-10 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4">
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Vi phạm & Báo cáo</h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                Quản trị an toàn & Compliance DocLib <ShieldAlert className="w-3.5 h-3.5 text-zinc-100" />
              </p>
            </div>
            
            <div className="flex items-center gap-4">
               <button 
                onClick={fetchData}
                disabled={isRefreshing}
                className="h-14 px-8 border border-zinc-100 text-black text-[11px] font-bold uppercase hover:bg-zinc-50 transition-all active:scale-[0.98] flex items-center gap-4 rounded-sm"
              >
                {isRefreshing ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCcw className="w-5 h-5" />}
                Đồng bộ
              </button>
              <div className="hidden md:flex items-center gap-3 px-6 py-3 bg-zinc-50 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-400 rounded-sm">
                Trung tâm an toàn DocLib
              </div>
            </div>
          </div>
        </div>

        <div 
          className="transition-all duration-300 delay-75 space-y-10"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
            <div className="relative group">
                <div className="absolute left-6 top-1/2 -translate-y-1/2">
                    <Search className="w-5 h-5 text-zinc-200 group-focus-within:text-black transition-colors" />
                </div>
                <input 
                  type="text"
                  placeholder="Tìm kiếm theo lý do, ID đối tượng hoặc người báo cáo"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-16 pl-16 pr-8 bg-white border border-zinc-100 focus:border-black outline-none font-bold text-lg tracking-tight transition-all placeholder:text-zinc-100 rounded-sm"
                />
            </div>

            <div className="bg-white border border-zinc-100 rounded-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-zinc-50/50 border-b border-zinc-100 text-zinc-300 text-[9px] font-bold uppercase tracking-[0.2em]">
                      <th className="px-10 py-6">Đối tượng vi phạm</th>
                      <th className="px-10 py-6">Nội dung & Lý do</th>
                      <th className="px-10 py-6">Người gửi báo cáo</th>
                      <th className="px-10 py-6 text-right">Xử lý</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {filteredReports.map((report: any) => (
                      <tr key={report.id} className="hover:bg-zinc-50/20 transition-all duration-300 group">
                        <td className="px-10 py-10">
                            <div className="flex items-center gap-8">
                                <div className="w-14 h-14 bg-zinc-50 flex items-center justify-center border border-zinc-100 group-hover:bg-black transition-all duration-300 rounded-sm">
                                    <UserX className="w-6 h-6 text-zinc-100 group-hover:text-white" />
                                </div>
                                <div className="flex flex-col gap-2 min-w-0">
                                    <span className="font-bold text-black uppercase tracking-widest text-[10px] flex items-center gap-2">
                                        {report.target_type || "Nội dung"} <ChevronRight className="w-3 h-3 text-zinc-100" />
                                    </span>
                                    <span className="text-[10px] font-bold text-zinc-200 truncate max-w-[150px] tracking-tight italic">ID: {report.target_id}</span>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-10">
                            <div className="space-y-3 max-w-lg">
                                <span className="inline-block px-3 py-1 bg-black text-white text-[9px] font-black uppercase tracking-widest rounded-sm border border-black">
                                    {report.reason}
                                </span>
                                <p className="text-[12px] text-zinc-500 font-medium italic line-clamp-2 leading-relaxed">
                                    "{report.description || "Không có mô tả chi tiết kèm theo."}"
                                </p>
                            </div>
                        </td>
                        <td className="px-10 py-10">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 border border-zinc-100 flex items-center justify-center text-[11px] font-bold text-zinc-300 rounded-sm group-hover:text-black group-hover:border-black transition-all">
                                    {report.reporter_name?.[0] || "R"}
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[11px] font-bold text-black tracking-tight">{report.reporter_name || "Ẩn danh"}</span>
                                    <div className="flex items-center gap-2 text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                                        <Clock className="w-3 h-3" /> {new Date(report.created_at).toLocaleDateString("vi-VN")}
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-10 text-right">
                            <div className="flex justify-end gap-3">
                                <button 
                                    onClick={() => handleResolve(report.id, "DISMISSED")}
                                    className="h-11 px-8 border border-zinc-100 text-[9px] font-bold uppercase tracking-widest text-zinc-300 hover:text-black hover:border-black transition-all rounded-sm"
                                >
                                    Bỏ qua
                                </button>
                                <button 
                                    onClick={() => handleResolve(report.id, "RESOLVED")}
                                    className="h-11 px-10 bg-black text-white text-[9px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
                                >
                                    Xử lý vi phạm
                                </button>
                                <button className="h-11 w-11 border border-zinc-100 flex items-center justify-center text-zinc-100 hover:text-black hover:border-black transition-all rounded-sm">
                                    <MoreVertical className="w-4 h-4" />
                                </button>
                            </div>
                        </td>
                      </tr>
                    ))}
                    {filteredReports.length === 0 && (
                        <tr>
                            <td colSpan={4} className="py-48 text-center border-dashed border-2 border-zinc-50 rounded-sm">
                                <div className="flex flex-col items-center gap-6">
                                    <ShieldCheck className="w-16 h-16 text-zinc-50 stroke-[1]" />
                                    <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.2em]">Hệ thống hiện tại không có báo cáo vi phạm</p>
                                </div>
                            </td>
                        </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
        </div>
      </div>
  );
}
