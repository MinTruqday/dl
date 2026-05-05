"use client";

import { useEffect, useState, useCallback } from "react";
import { getModeratorActivityAPI } from "@/services/log.service";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import { useRouter } from "next/navigation";

export default function LogsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();
  
  const [activityLogs, setActivityLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

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
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white font-sans text-black">
      <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12">
        <header className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-black">Nhật ký hệ thống</h1>
            <p className="text-sm text-zinc-500 mt-1">Lưu trữ hoạt động quản trị và kiểm duyệt</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="text-sm font-medium text-zinc-500 hover:text-black transition-colors disabled:opacity-50"
            >
              {isRefreshing ? "Đang đồng bộ" : "Đồng bộ dữ liệu"}
            </button>
          </div>
        </header>

        <div className="space-y-6">
          <h2 className="text-sm font-semibold text-black">Bản ghi nhật ký ({activityLogs.length})</h2>
          
          <div className="border border-zinc-200 bg-white overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50">
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Thao tác</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Đối tượng</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Thời gian</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {activityLogs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-24 text-center">
                      <p className="text-sm font-medium text-zinc-500">Nhật ký hiện đang trống</p>
                    </td>
                  </tr>
                ) : (
                  activityLogs.map((log: any, idx: number) => (
                    <tr key={idx} className="border-b border-zinc-200 last:border-0 hover:bg-zinc-50 transition-colors">
                      <td className="py-4 px-6 align-top">
                        <span className="text-sm font-semibold text-black uppercase">{log.action || "Thao tác điều hành"}</span>
                      </td>
                      <td className="py-4 px-6 align-top">
                        <div className="flex flex-col gap-1">
                          <span className="text-[10px] font-bold text-black uppercase tracking-widest">{log.target_type}</span>
                          <span className="text-xs text-zinc-500 font-mono">{log.target_id}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6 align-top whitespace-nowrap">
                        <span className="text-xs font-medium text-zinc-500">
                          {new Date(log.created_at).toLocaleString("vi-VN")}
                        </span>
                      </td>
                      <td className="py-4 px-6 align-top text-right">
                        <span className="text-xs font-medium text-zinc-500">Hoàn tất</span>
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
