"use client";

import { useAuth } from "@/features/authentication/contexts/AuthContext";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/app/_components/InlineState";
import PageHeader from "@/app/_components/PageHeader";
import { useAuditLogs } from "./useAuditLogs";

function formatDate(value?: string) {
  if (!value) return "Chưa ghi nhận";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Chưa ghi nhận"
    : new Intl.DateTimeFormat("vi-VN", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

export default function AuditPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const { logs, loading, refreshing, error, reload } = useAuditLogs(allowed);

  if (authLoading || loading) return <PageLoader rows={6} />;

  if (!allowed) {
    return (
      <InlineState
        title="Không có quyền truy cập"
        detail="Trang này chỉ dành cho quản trị viên"
        tone="danger"
      />
    );
  }

  return (
    <div className="w-full">
      <PageHeader
        title="Kiểm toán"
        meta={`${logs.length} bản ghi`}
        actions={
          <Button variant="secondary" onClick={reload} disabled={refreshing}>
            {refreshing ? "Đang tải" : "Làm mới"}
          </Button>
        }
      />

      {error && (
        <div className="mb-6">
          <InlineState
            title="Không thể tải nhật ký"
            detail={error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}

      {logs.length === 0 ? (
        <EmptyState
          text="Chưa có hoạt động quản trị"
          description="Các thao tác quản trị mới sẽ được ghi nhận tại đây"
        />
      ) : (
        <div className="overflow-x-auto rounded-panel border border-border bg-surface">
          <table className="w-full min-w-[720px] border-collapse text-left">
            <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
              <tr>
                <th className="px-4 py-3">Thao tác</th>
                <th className="px-4 py-3">Loại đối tượng</th>
                <th className="px-4 py-3">Mã đối tượng</th>
                <th className="px-4 py-3">Thời gian</th>
                <th className="px-4 py-3">Trạng thái</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log, index) => (
                <tr
                  key={log.id || log._id || `${log.created_at}-${index}`}
                  className="text-[13px] hover:bg-surface-raised"
                >
                  <td className="px-4 py-3.5 font-semibold text-ink">
                    {log.action || "Thao tác quản trị"}
                  </td>
                  <td className="px-4 py-3.5 text-ink-muted">
                    {log.target_type || "Không xác định"}
                  </td>
                  <td className="max-w-[16rem] truncate px-4 py-3.5 font-mono text-[12px] text-ink-muted">
                    {log.target_id || "Không có"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3.5 text-ink-muted">
                    {formatDate(log.created_at)}
                  </td>
                  <td className="px-4 py-3.5 font-medium text-brand">
                    {log.status || "Hoàn tất"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
