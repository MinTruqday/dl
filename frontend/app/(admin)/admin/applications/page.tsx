"use client";

import { useEffect, useState, useCallback } from "react";
import { getToken, API_URL, formatError } from "@/app/lib/api";
import {
  UserCheck,
  Loader2,
  RefreshCcw,
  ShieldCheck,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { Notification } from "@/app/components/NotificationToast";

export default function AuthorApplicationsPage() {
  const { user, isLoading } = useAuth() as any;
  const [applications, setApplications] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const headers = { Authorization: `Bearer ${getToken()}` };
      const res = await fetch(`${API_URL}/admin/applications/authors`, { headers });
      if (res.ok) {
        const data = await res.json();
        setApplications(data.data || data || []);
      }
    } catch (err: any) {
      console.error("Lỗi tải đơn ứng tuyển:", err);
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

  const reviewApplication = async (appId: string, status: string) => {
    try {
      const res = await fetch(`${API_URL}/admin/applications/authors/${appId}/review`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${getToken()}`, "Content-Type": "application/json" },
        body: JSON.stringify({ status, reason: status === "APPROVED" ? "Đã duyệt" : "Không đủ tiêu chuẩn" }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã xử lý hồ sơ ứng tuyển." });
        fetchData();
      } else {
        const err = await res.json();
        setNotification({ type: "error", text: formatError(err.detail) || "Lỗi xử lý hồ sơ." });
      }
    } catch (err: any) {
      console.error("Lỗi duyệt hồ sơ:", err);
      setNotification({ type: "error", text: "Lỗi kết nối hệ thống." });
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
            <h1 className="text-5xl font-bold tracking-tighter leading-none">Hồ sơ ứng tuyển</h1>
            <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
              Xét duyệt đăng ký tác giả & Nâng cấp quyền hạn <UserCheck className="w-3.5 h-3.5" />
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
                      <th className="px-10 py-6">Người ứng tuyển</th>
                      <th className="px-10 py-6">Lý do & Động lực</th>
                      <th className="px-10 py-6">Ngày gửi</th>
                      <th className="px-10 py-6 text-right">Xử lý</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-50">
                    {applications.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-10 py-32 text-center text-[10px] font-bold text-zinc-200 uppercase tracking-widest italic">
                          Hiện không có đơn ứng tuyển nào đang chờ xét duyệt
                        </td>
                      </tr>
                    ) : (
                      applications.map((app: any) => (
                        <tr key={app._id} className="hover:bg-zinc-50/20 transition-colors group">
                          <td className="px-10 py-8">
                              <div className="flex items-center gap-4">
                                  <div className="w-10 h-10 bg-black flex items-center justify-center text-white font-bold">
                                      {app.user_name?.[0]?.toUpperCase() || "U"}
                                  </div>
                                  <div className="flex flex-col gap-1">
                                      <span className="font-bold text-black uppercase tracking-widest text-[10px]">{app.user_name}</span>
                                      <span className="text-[9px] font-bold text-zinc-300">{app.user_email}</span>
                                  </div>
                              </div>
                          </td>
                          <td className="px-10 py-8">
                              <p className="text-[11px] text-zinc-500 font-medium italic line-clamp-2 max-w-md">"{app.motivation}"</p>
                          </td>
                          <td className="px-10 py-8">
                              <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                                  {new Date(app.created_at).toLocaleDateString("vi-VN")}
                              </span>
                          </td>
                          <td className="px-10 py-8 text-right">
                              <div className="flex justify-end gap-3">
                                  <button 
                                      onClick={() => reviewApplication(app._id, "REJECTED")}
                                      className="h-9 px-6 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest text-zinc-300 hover:text-red-600 hover:border-red-600 transition-all"
                                  >
                                      Từ chối
                                  </button>
                                  <button 
                                      onClick={() => reviewApplication(app._id, "APPROVED")}
                                      className="h-9 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all active:scale-[0.98]"
                                  >
                                      Phê duyệt
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
