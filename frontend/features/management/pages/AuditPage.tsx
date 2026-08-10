"use client";

import { useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import EmptyState from "@/shared/components/common/EmptyState";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { Modal } from "@/shared/components/ui/Modal";
import InlineState from "@/shared/components/common/InlineState";
import MetricStrip from "@/shared/components/data-display/MetricStrip";
import PageHeader from "@/shared/components/layout/PageHeader";
import { AuditLog, useAuditLogs } from "../hooks/useAuditLogs";

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

function getSeverityBadgeClass(severity?: string) {
  const s = String(severity || "INFO").toUpperCase();
  if (s === "SECURITY" || s === "CRITICAL") {
    return "border border-danger/20 bg-danger-soft text-danger";
  }
  if (s === "ERROR") {
    return "border border-danger/20 bg-danger-soft text-danger";
  }
  if (s === "WARNING") {
    return "border border-warning/20 bg-warning-soft text-warning";
  }
  return "border border-brand/20 bg-brand-soft text-brand";
}

function getStatusBadgeClass(status?: string) {
  const s = String(status || "SUCCESS").toUpperCase();
  if (s === "SUCCESS") {
    return "border border-brand/20 bg-brand-soft text-brand";
  }
  if (s === "DENIED") {
    return "border border-warning/20 bg-warning-soft text-warning";
  }
  return "border border-danger/20 bg-danger-soft text-danger";
}

function getSeverityLabel(severity?: string) {
  const value = String(severity || "INFO").toUpperCase();
  if (value === "WARNING") return "Cảnh báo";
  if (value === "ERROR") return "Lỗi";
  if (value === "CRITICAL") return "Nghiêm trọng";
  if (value === "SECURITY") return "Bảo mật";
  return "Thông tin";
}

function getStatusLabel(status?: string) {
  const value = String(status || "SUCCESS").toUpperCase();
  if (value === "DENIED") return "Bị từ chối";
  if (value === "FAILED" || value === "FAILURE" || value === "ERROR")
    return "Thất bại";
  return "Thành công";
}

function getModuleName(module?: string) {
  const m = String(module || "").toLowerCase();
  if (m === "authentication") return "Xác thực";
  if (m === "content") return "Tài liệu";
  if (m === "drm") return "Bản quyền";
  if (m === "finance") return "Tài chính";
  if (m === "agentic_ai") return "Trí tuệ nhân tạo";
  return "Hệ thống";
}

export default function AuditPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const {
    logs,
    stats,
    total,
    totalPages,
    page,
    pageSize,
    moduleFilter,
    severityFilter,
    statusFilter,
    searchQuery,
    dateRange,
    fromDate,
    toDate,
    loading,
    refreshing,
    error,
    selectedLog,
    autoRefreshInterval,
    integrityStatus,
    verifyingIntegrity,
    exporting,
    setPage,
    setPageSize,
    setModuleFilter,
    setSeverityFilter,
    setStatusFilter,
    setSearchQuery,
    setDateRange,
    setFromDate,
    setToDate,
    setSelectedLog,
    setAutoRefreshInterval,
    reload,
    verifyIntegrity,
    exportData,
    resetFilters,
  } = useAuditLogs(allowed);

  const [copiedId, setCopiedId] = useState(false);
  const [copiedPayload, setCopiedPayload] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);

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

  const metricItems = [
    {
      label: "Tổng sự kiện",
      value: stats?.total_events ?? total,
    },
    {
      label: "Sự kiện hôm nay",
      value: stats?.today_events ?? 0,
    },
    {
      label: "Cảnh báo bảo mật",
      value: stats?.security_alerts ?? 0,
    },
    {
      label: "Thao tác quản trị",
      value: stats?.admin_actions ?? 0,
    },
  ];

  const handleCopy = (text: string, isId: boolean) => {
    navigator.clipboard.writeText(text);
    if (isId) {
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } else {
      setCopiedPayload(true);
      setTimeout(() => setCopiedPayload(false), 2000);
    }
  };

  return (
    <div className="w-full space-y-6">
      <PageHeader
        title="Kiểm toán hệ thống"
        meta={`${total} bản ghi`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Button
                variant="secondary"
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={exporting}
              >
                {exporting ? "Đang kết xuất" : "Kết xuất"}
              </Button>
              {showExportMenu && (
                <div className="absolute right-0 top-full z-20 mt-1 w-44 rounded-panel border border-border bg-surface p-1 shadow-lg">
                  <button
                    type="button"
                    onClick={() => {
                      setShowExportMenu(false);
                      exportData("csv");
                    }}
                    className="w-full rounded px-3 py-2 text-left text-[13px] text-ink hover:bg-surface-raised"
                  >
                    Kết xuất tệp CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowExportMenu(false);
                      exportData("json");
                    }}
                    className="w-full rounded px-3 py-2 text-left text-[13px] text-ink hover:bg-surface-raised"
                  >
                    Kết xuất tệp JSON
                  </button>
                </div>
              )}
            </div>

            <Button
              variant="secondary"
              onClick={() => verifyIntegrity()}
              disabled={verifyingIntegrity}
            >
              {verifyingIntegrity ? "Đang kiểm tra" : "Xác thực toàn vẹn"}
            </Button>

            <div className="flex items-center rounded-panel border border-border bg-surface px-2">
              <span className="text-[12px] text-ink-muted">Tự động:</span>
              <select
                aria-label="Khoảng thời gian tự động làm mới"
                value={autoRefreshInterval}
                onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
                className="bg-transparent px-2 py-1 text-[12px] text-ink focus:outline-none"
              >
                <option value={0}>Tắt</option>
                <option value={5}>5 giây</option>
                <option value={10}>10 giây</option>
                <option value={30}>30 giây</option>
              </select>
            </div>

            <Button variant="secondary" onClick={reload} disabled={refreshing}>
              {refreshing ? "Đang tải" : "Làm mới"}
            </Button>
          </div>
        }
      />

      <MetricStrip items={metricItems} />

      {integrityStatus && (
        <div
          className={`rounded-panel border p-4 ${
            integrityStatus.verified
              ? "border-brand/30 bg-brand-soft text-brand"
              : "border-danger/30 bg-danger-soft text-danger"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-[13px] font-medium">
              {integrityStatus.verified
                ? `Chuỗi nhật ký toàn vẹn: Đã kiểm tra ${integrityStatus.checked_records} bản ghi không có dấu hiệu can thiệp`
                : `Cảnh báo can thiệp: Phát hiện ${integrityStatus.tampered_records} bản ghi có mã băm không khớp`}
            </div>
            <button
              type="button"
              onClick={() => verifyIntegrity()}
              className="text-[12px] underline"
            >
              Kiểm tra lại
            </button>
          </div>
        </div>
      )}

      <div className="rounded-panel border border-border bg-surface p-4">
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
          <div className="sm:col-span-2">
            <label className="mb-1 block text-[12px] font-medium text-ink-muted">
              Tìm kiếm tức thời
            </label>
            <input
              type="text"
              placeholder="Mã người dùng, email, hành động, IP"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-panel border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-[12px] font-medium text-ink-muted">
              Phân hệ
            </label>
            <select
              aria-label="Lọc theo phân hệ"
              value={moduleFilter}
              onChange={(e) => {
                setModuleFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-panel border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink focus:border-brand focus:outline-none"
            >
              <option value="">Tất cả phân hệ</option>
              <option value="authentication">Xác thực</option>
              <option value="content">Tài liệu</option>
              <option value="drm">Bản quyền DRM</option>
              <option value="finance">Tài chính</option>
              <option value="management">Quản trị hệ thống</option>
              <option value="agentic_ai">Trí tuệ nhân tạo</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-[12px] font-medium text-ink-muted">
              Mức độ
            </label>
            <select
              aria-label="Lọc theo mức độ nghiêm trọng"
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-panel border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink focus:border-brand focus:outline-none"
            >
              <option value="">Tất cả mức độ</option>
              <option value="INFO">Thông tin</option>
              <option value="WARNING">Cảnh báo</option>
              <option value="ERROR">Lỗi</option>
              <option value="CRITICAL">Nghiêm trọng</option>
              <option value="SECURITY">Cảnh báo bảo mật</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-[12px] font-medium text-ink-muted">
              Trạng thái
            </label>
            <select
              aria-label="Lọc theo trạng thái"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-panel border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink focus:border-brand focus:outline-none"
            >
              <option value="">Tất cả trạng thái</option>
              <option value="SUCCESS">Thành công</option>
              <option value="FAILED">Thất bại</option>
              <option value="DENIED">Bị từ chối</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-[12px] font-medium text-ink-muted">
              Thời gian
            </label>
            <select
              aria-label="Lọc theo khoảng thời gian"
              value={dateRange}
              onChange={(e) => {
                setDateRange(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-panel border border-border bg-surface-quiet px-3 py-2 text-[13px] text-ink focus:border-brand focus:outline-none"
            >
              <option value="all">Toàn bộ thời gian</option>
              <option value="today">Hôm nay</option>
              <option value="7days">7 ngày qua</option>
              <option value="30days">30 ngày qua</option>
              <option value="custom">Tùy chọn mốc ngày</option>
            </select>
          </div>
        </div>

        {dateRange === "custom" && (
          <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-border pt-3">
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-ink-muted">Từ ngày:</span>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => {
                  setFromDate(e.target.value);
                  setPage(1);
                }}
                className="rounded border border-border bg-surface-quiet px-2 py-1 text-[12px] text-ink focus:outline-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-ink-muted">Đến ngày:</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => {
                  setToDate(e.target.value);
                  setPage(1);
                }}
                className="rounded border border-border bg-surface-quiet px-2 py-1 text-[12px] text-ink focus:outline-none"
              />
            </div>
          </div>
        )}

        {(moduleFilter ||
          severityFilter ||
          statusFilter ||
          searchQuery ||
          dateRange !== "all") && (
          <div className="mt-3 flex justify-end border-t border-border pt-2">
            <button
              type="button"
              onClick={resetFilters}
              className="text-[12px] font-medium text-brand hover:underline"
            >
              Đặt lại toàn bộ bộ lọc
            </button>
          </div>
        )}
      </div>

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
          text="Không tìm thấy bản ghi kiểm toán"
        />
      ) : (
        <div className="overflow-x-auto rounded-panel border border-border bg-surface">
          <table className="w-full min-w-[840px] border-collapse text-left">
            <thead className="bg-surface-quiet text-[12px] font-semibold text-ink-muted">
              <tr>
                <th className="px-4 py-3">Thời gian</th>
                <th className="px-4 py-3">Phân hệ</th>
                <th className="px-4 py-3">Hành động</th>
                <th className="px-4 py-3">Người thực hiện</th>
                <th className="px-4 py-3">Đối tượng</th>
                <th className="px-4 py-3">Mức độ</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3 text-right">Chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log, index) => {
                const logKey = log.id || log._id || `${log.timestamp}-${index}`;
                return (
                  <tr
                    key={logKey}
                    onClick={() => setSelectedLog(log)}
                    className="cursor-pointer text-[13px] hover:bg-surface-raised"
                  >
                    <td className="whitespace-nowrap px-4 py-3.5 text-ink-muted">
                      {formatDate(log.timestamp || log.created_at)}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-ink">
                      {getModuleName(log.module)}
                    </td>
                    <td className="max-w-[12rem] truncate px-4 py-3.5 font-semibold text-ink">
                      {log.action || "Thao tác hệ thống"}
                    </td>
                    <td className="max-w-[12rem] truncate px-4 py-3.5 text-ink-muted">
                      {log.actor_email || log.actor_id || "Hệ thống"}
                    </td>
                    <td className="max-w-[10rem] truncate px-4 py-3.5 font-mono text-[12px] text-ink-muted">
                      {log.target_id || log.target_type || "Không có"}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${getSeverityBadgeClass(
                          log.severity
                        )}`}
                      >
                        {getSeverityLabel(log.severity)}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${getStatusBadgeClass(
                          log.status
                        )}`}
                      >
                        {getStatusLabel(log.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLog(log);
                        }}
                      >
                        Xem
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-panel border border-border bg-surface px-4 py-3">
          <div className="flex items-center gap-2 text-[12px] text-ink-muted">
            <span>Hiển thị mỗi trang:</span>
            <select
              aria-label="Số lượng bản ghi mỗi trang"
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="rounded border border-border bg-surface-quiet px-2 py-1 text-ink focus:outline-none"
            >
              <option value={10}>10 dòng</option>
              <option value={20}>20 dòng</option>
              <option value={50}>50 dòng</option>
              <option value={100}>100 dòng</option>
            </select>
            <span>Tổng cộng {total} bản ghi</span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
            >
              Trang trước
            </Button>
            <span className="text-[12px] font-medium text-ink">
              Trang {page} / {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
            >
              Trang sau
            </Button>
          </div>
        </div>
      )}

      {selectedLog && (
        <Modal
          isOpen={Boolean(selectedLog)}
          onClose={() => setSelectedLog(null)}
          className="max-h-[90vh] max-w-3xl overflow-y-auto"
        >
          <div className="p-6">
            <div className="mb-4 flex items-center justify-between border-b border-border pb-4">
              <div>
                <h3 className="text-[18px] font-semibold text-ink">
                  Chi tiết bản ghi kiểm toán
                </h3>
                <p className="font-mono text-[12px] text-ink-muted">
                  ID: {selectedLog._id || selectedLog.id}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 rounded-panel bg-surface-quiet p-4 text-[13px] sm:grid-cols-3">
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Thời gian
                  </span>
                  <span className="font-medium text-ink">
                    {formatDate(selectedLog.timestamp || selectedLog.created_at)}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Phân hệ
                  </span>
                  <span className="font-medium text-ink">
                    {getModuleName(selectedLog.module)}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Hành động
                  </span>
                  <span className="font-semibold text-ink">
                    {selectedLog.action}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Mức độ
                  </span>
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${getSeverityBadgeClass(
                      selectedLog.severity
                    )}`}
                  >
                    {getSeverityLabel(selectedLog.severity)}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Trạng thái
                  </span>
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-[11px] font-semibold ${getStatusBadgeClass(
                      selectedLog.status
                    )}`}
                  >
                    {getStatusLabel(selectedLog.status)}
                  </span>
                </div>
                <div>
                  <span className="block text-[11px] font-medium text-ink-muted">
                    Địa chỉ IP
                  </span>
                  <span className="font-mono text-ink">
                    {selectedLog.ip_address || "Không ghi nhận"}
                  </span>
                </div>
              </div>

              <div className="space-y-2 rounded-panel border border-border p-4 text-[13px]">
                <div className="flex justify-between">
                  <span className="text-ink-muted">Người thực hiện:</span>
                  <span className="font-mono text-ink">
                    {selectedLog.actor_email || selectedLog.actor_id || "Hệ thống"}
                  </span>
                </div>
                {selectedLog.target_id && (
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Mã đối tượng tác động:</span>
                    <span className="font-mono text-ink">
                      {selectedLog.target_id}
                    </span>
                  </div>
                )}
                {selectedLog.user_agent && (
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Trình duyệt / Thiết bị:</span>
                    <span className="max-w-[20rem] truncate text-ink-muted">
                      {selectedLog.user_agent}
                    </span>
                  </div>
                )}
                {selectedLog.hash && (
                  <div className="flex items-center justify-between border-t border-border pt-2">
                    <span className="text-ink-muted">Mã băm toàn vẹn:</span>
                    <div className="flex items-center gap-2">
                      <span className="max-w-[14rem] truncate font-mono text-[11px] text-ink-faint sm:max-w-[20rem]">
                        {selectedLog.hash}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(selectedLog.hash || "", true)}
                        className="text-[11px] font-medium text-brand hover:underline"
                      >
                        {copiedId ? "Đã chép" : "Sao chép"}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-ink">
                    Gói tin dữ liệu chi tiết
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      handleCopy(
                        JSON.stringify(selectedLog.details || selectedLog, null, 2),
                        false
                      )
                    }
                    className="text-[11px] font-medium text-brand hover:underline"
                  >
                    {copiedPayload ? "Đã sao chép" : "Sao chép cấu trúc dữ liệu"}
                  </button>
                </div>
                <pre className="max-h-60 overflow-x-auto rounded-panel border border-border bg-surface-quiet p-3 font-mono text-[12px] text-ink">
                  {JSON.stringify(selectedLog.details || selectedLog, null, 2)}
                </pre>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
              <Button
                variant="secondary"
                onClick={() => verifyIntegrity(selectedLog._id || selectedLog.id)}
              >
                Xác thực bản ghi này
              </Button>
              <Button variant="primary" onClick={() => setSelectedLog(null)}>
                Hoàn tất
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
