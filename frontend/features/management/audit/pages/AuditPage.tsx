"use client";

import { useEffect, useState, useCallback } from "react";
import { getModeratorActivityAPI } from "@/features/management/services/audit.service";
import {
  Loader2,
  RefreshCcw,
  Activity,
  FileText,
  Database,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import PageHeader from "@/shared/components/common/PageHeader";

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
      showToast("Lỗi trích xuất bản ghi nhật ký hệ thống", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user) {
      if (user.role !== "admin") {
        router.push("/");
      } else {
        fetchData();
      }
    }
  }, [user, authLoading, fetchData, router]);

  if (authLoading || isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--ink-muted)]" />
      </div>
    );
  }

  if (user?.role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 font-sans text-center">
        <div className="w-24 h-24 bg-[var(--surface-quiet)] flex items-center justify-center rounded-[var(--radius-panel)]">
          <ShieldAlert className="w-10 h-10 text-[var(--danger)]" />
        </div>
        <div className="space-y-2 max-w-[300px]">
          <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
            Truy cập bị hạn chế
          </p>
          <p className="text-[15px] text-[var(--ink-muted)]">
            Bạn không có quyền quản trị để truy cập trang này.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-page gap-6">
      <PageHeader
        title="Nhật ký hệ thống"
        actions={
          <button
            onClick={fetchData}
            disabled={isRefreshing}
            className="icon-button"
            aria-label="Làm mới"
            title="Làm mới"
          >
            <RefreshCcw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </button>
        }
      />
      <div className="flex flex-col">
        <main className="flex-1 min-w-0 space-y-8 pt-6">
          <div className="w-full overflow-x-auto min-h-[400px] transition-colors">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-[13px] text-[var(--ink-muted)] border-b border-[var(--border)]">
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center w-[25%]">Thao tác</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center w-[35%]">Đối tượng</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center w-[25%]">Thời gian</th>
                  <th className="py-3 px-6 font-medium whitespace-nowrap text-center w-[15%]">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {activityLogs.length === 0 ? (
                  <tr>
                    <td colSpan={4}>
                      <div className="py-24 flex flex-col items-center justify-center bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] w-full text-center my-4">
                        <p className="text-[17px] text-[var(--ink-muted)]">Chưa có dữ liệu</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  activityLogs.map((log: any, idx: number) => (
                    <tr
                      key={idx}
                      className="hover:bg-[var(--border)]/60 transition-colors group cursor-default"
                    >
                      <td className="py-3 px-6 text-center">
                        <span className="font-medium text-[14px] text-[var(--ink)]">
                          {log.action || "Thao tác điều hành"}
                        </span>
                      </td>
                      <td className="py-3 px-6 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-[12px] bg-[var(--border)] text-[var(--ink-muted)] px-2 py-0.5 rounded-md w-fit font-medium">
                            {log.target_type}
                          </span>
                          <span className="text-[13px] text-[var(--ink-muted)] font-mono">
                            {log.target_id}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-6 text-[var(--ink-muted)] text-[13px] text-center">
                        {new Date(log.created_at).toLocaleString("vi-VN")}
                      </td>
                      <td className="py-3 px-6 text-center">
                        <div className="inline-flex items-center justify-center px-3 py-1 bg-[#E8F5E9] text-[var(--success)] rounded-full text-[12px] font-medium whitespace-nowrap gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Hoàn tất
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
