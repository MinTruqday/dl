"use client";

import { useEffect, useState, useCallback } from "react";
import { getModeratorActivityAPI } from "@/features/provision/services/audit_logs.service";
import { Loader2, RefreshCcw, Activity, FileText, Database, ShieldAlert } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";

export default function LogsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();

  const [activityLogs, setActivityLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [visible, setVisible] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const logsRes = await getModeratorActivityAPI();
      setActivityLogs(logsRes.data || logsRes || []);
    } catch (err: any) {
      showToast("Không thể tải nhật ký hệ thống.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user) {
      if (user.role !== "admin" && user.role !== "moderator") {
        router.push("/");
      } else {
        fetchData();
      }
    }
  }, [user, authLoading, fetchData, router]);

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  if (user?.role !== "admin" && user?.role !== "moderator") {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-6 font-sans bg-zinc-50 px-6 text-center">
        <div className="w-20 h-20 bg-white shadow-sm flex items-center justify-center border border-zinc-100 rounded-3xl">
          <ShieldAlert className="w-8 h-8 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-zinc-900">
            Truy cập bị hạn chế
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            Bạn không có quyền quản trị hệ thống
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <div className="flex flex-col gap-6 h-full min-h-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-4 md:p-6 flex flex-col md:flex-row gap-4 items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0 shadow-sm hidden md:flex">
              <Activity className="w-6 h-6 text-black" />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
                Nhật ký hệ thống
              </h1>
              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Lưu trữ hoạt động quản trị và kiểm duyệt
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-11 px-6 border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-900 text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm w-full md:w-auto"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Đồng bộ dữ liệu</span>
            </button>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
          <div className="flex items-center justify-between p-6 border-b border-zinc-100">
            <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2">
              <Database className="w-4 h-4 text-zinc-400" /> Bản ghi nhật ký
            </h2>
            <span className="px-3 py-1 bg-zinc-100 text-zinc-900 text-[10px] font-bold uppercase tracking-widest rounded-xl">
              {activityLogs.length} bản ghi
            </span>
          </div>
          
          <div className="overflow-y-auto custom-scrollbar flex-1">
            <table className="w-full text-left text-sm border-collapse min-w-[800px]">
              <thead className="sticky top-0 bg-white/95 backdrop-blur-sm z-10">
                <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                  <th className="w-[30%] px-6 py-4 whitespace-nowrap">
                    Thao tác
                  </th>
                  <th className="w-[30%] px-6 py-4 whitespace-nowrap">
                    Đối tượng
                  </th>
                  <th className="w-[20%] px-6 py-4 whitespace-nowrap">
                    Thời gian
                  </th>
                  <th className="w-[20%] px-6 py-4 text-right whitespace-nowrap">
                    Trạng thái
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {activityLogs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-32 text-center">
                      <div className="flex flex-col items-center justify-center bg-white border border-zinc-100 rounded-3xl p-12 max-w-sm mx-auto shadow-sm">
                        <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                          <FileText className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                        </div>
                        <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Nhật ký trống</h2>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                          Chưa có hoạt động quản trị nào được ghi nhận
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  activityLogs.map((log: any, idx: number) => (
                    <tr
                      key={idx}
                      className="group hover:bg-zinc-50/50 transition-colors"
                    >
                      <td className="px-6 py-4 align-top">
                        <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
                          {log.action || "Thao tác điều hành"}
                        </span>
                      </td>
                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[9px] font-bold text-black uppercase tracking-widest px-2 py-0.5 bg-zinc-100 rounded-md w-fit">
                            {log.target_type}
                          </span>
                          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono">
                            {log.target_id}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top whitespace-nowrap">
                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                          {new Date(log.created_at).toLocaleString("vi-VN")}
                        </span>
                      </td>
                      <td className="px-6 py-4 align-top text-right">
                        <div className="inline-flex items-center gap-2 px-2.5 py-1 bg-zinc-50 border border-zinc-100 rounded-lg shadow-sm">
                          <div className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                          <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-900">
                            Hoàn tất
                          </span>
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
