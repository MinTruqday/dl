"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  getAuthorApplicationsAPI, 
  reviewAuthorApplicationAPI 
} from "@/services/admin.service";
import {
  UserCheck,
  Loader2,
  RefreshCcw,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Zap,
  Mail,
  MoreVertical,
  ChevronRight,
  ClipboardCheck,
  Search
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";

export default function AuthorApplicationsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const [applications, setApplications] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await getAuthorApplicationsAPI(statusFilter);
      setApplications(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể tải danh sách đơn ứng tuyển.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [statusFilter]);

  useEffect(() => {
    if (!authLoading && (user?.role === "admin" || user?.role === "moderator")) {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const handleReview = async (appId: string, status: string) => {
    try {
      await reviewAuthorApplicationAPI(
        appId, 
        status, 
        status === "APPROVED" ? "Đã phê duyệt hồ sơ tác giả." : "Hồ sơ chưa đạt tiêu chuẩn kiểm duyệt."
      );
      showToast("Đã cập nhật trạng thái hồ sơ ứng tuyển.", "success");
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý hồ sơ.", "error");
    }
  };

  const filteredApplications = applications.filter(app => 
    (app.user_name || "").toLowerCase().includes(searchQuery.toLowerCase()) || 
    (app.user_email || "").toLowerCase().includes(searchQuery.toLowerCase())
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
              <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Hồ sơ ứng tuyển</h1>
              <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
                Quy trình xét duyệt tác giả tri thức <ClipboardCheck className="w-3.5 h-3.5 text-zinc-100" />
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex bg-zinc-50 p-1 rounded-sm border border-zinc-100">
                {[
                    { id: "PENDING", label: "Đang chờ" },
                    { id: "APPROVED", label: "Đã duyệt" },
                    { id: "REJECTED", label: "Đã từ chối" },
                ].map((f) => (
                    <button
                        key={f.id}
                        onClick={() => setStatusFilter(f.id)}
                        className={`px-6 py-2.5 text-[10px] font-bold uppercase tracking-widest transition-all rounded-sm ${
                            statusFilter === f.id ? "bg-white text-black " : "text-zinc-400 hover:text-black"
                        }`}
                    >
                        {f.label}
                    </button>
                ))}
              </div>
              <button 
                onClick={fetchData}
                disabled={isRefreshing}
                className="h-12 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-3 rounded-sm"
              >
                {isRefreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                Đồng bộ
              </button>
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
                  placeholder="Tìm kiếm theo tên hoặc email ứng viên"
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
                      <th className="px-10 py-6">Ứng viên tiềm năng</th>
                      <th className="px-10 py-6">Lý do & Động lực</th>
                      <th className="px-10 py-6">Thời gian gửi</th>
                      <th className="px-10 py-6 text-right">Thao tác duyệt</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {filteredApplications.map((app: any) => (
                      <tr key={app._id} className="hover:bg-zinc-50/20 transition-all duration-300 group">
                        <td className="px-10 py-10">
                            <div className="flex items-center gap-8">
                                <div className="w-14 h-14 bg-zinc-50 flex items-center justify-center border border-zinc-100 font-black text-zinc-200 group-hover:bg-black group-hover:text-white transition-all duration-300 rounded-sm">
                                    {app.user_name?.[0]?.toUpperCase() || "U"}
                                </div>
                                <div className="flex flex-col gap-2 min-w-0">
                                    <span className="font-bold text-black text-base tracking-tighter truncate max-w-xs">{app.user_name || "Ứng viên ẩn danh"}</span>
                                    <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2">
                                        <Mail className="w-3 h-3" /> {app.user_email}
                                    </span>
                                </div>
                            </div>
                        </td>
                        <td className="px-10 py-10">
                            <div className="bg-zinc-50/30 p-4 border-l-2 border-zinc-100 rounded-sm group-hover:border-black transition-colors">
                                <p className="text-[12px] text-zinc-500 font-medium italic line-clamp-2 max-w-md leading-relaxed">
                                    "{app.motivation || "Ứng viên chưa cung cấp mô tả chi tiết về động lực ứng tuyển."}"
                                </p>
                            </div>
                        </td>
                        <td className="px-10 py-10">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                <Clock className="w-3.5 h-3.5" />
                                {new Date(app.created_at).toLocaleDateString("vi-VN")}
                            </div>
                        </td>
                        <td className="px-10 py-10 text-right">
                            {statusFilter === "PENDING" ? (
                                <div className="flex justify-end gap-3">
                                    <button 
                                        onClick={() => handleReview(app._id, "REJECTED")}
                                        className="h-11 px-8 border border-zinc-100 text-[9px] font-bold uppercase tracking-widest text-zinc-300 hover:text-red-500 hover:border-red-500 transition-all rounded-sm"
                                    >
                                        Từ chối
                                    </button>
                                    <button 
                                        onClick={() => handleReview(app._id, "APPROVED")}
                                        className="h-11 px-10 bg-black text-white text-[9px] font-bold uppercase tracking-[0.2em] hover:bg-zinc-800 transition-all active:scale-[0.98] rounded-sm"
                                    >
                                        Phê duyệt
                                    </button>
                                </div>
                            ) : (
                                <span className={`inline-block px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest rounded-sm border ${
                                    statusFilter === "APPROVED" ? "bg-black text-white border-black" : "bg-white text-zinc-200 border-zinc-100"
                                }`}>
                                    {statusFilter === "APPROVED" ? "Đã phê duyệt" : "Đã từ chối"}
                                </span>
                            )}
                        </td>
                      </tr>
                    ))}
                    {filteredApplications.length === 0 && (
                        <tr>
                            <td colSpan={4} className="py-48 text-center border-dashed border-2 border-zinc-50 rounded-sm">
                                <div className="flex flex-col items-center gap-6">
                                    <Search className="w-16 h-16 text-zinc-50 stroke-[1]" />
                                    <p className="text-[11px] font-bold text-zinc-200 uppercase tracking-[0.2em]">Không tìm thấy hồ sơ phù hợp</p>
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
