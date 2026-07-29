"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Loader2,
  Search,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  RefreshCcw,
  FileWarning,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";
import PageHeader from "@/shared/components/common/PageHeader";

export default function ReportsManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();

  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [confirmModal, setConfirmModal] = useState<{
    reportId: string;
    action: string;
  } | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      setReports([]);
    } catch (err: any) {
      showToast("Lỗi gián đoạn kết nối máy chủ quản lý", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (!authLoading && user) {
      if (user.role !== "admin") router.push("/");
      else fetchData();
    }
  }, [user, authLoading, fetchData, router]);

  const confirmResolve = async () => {
    if (!confirmModal) return;
    setIsProcessing(true);
    try {
      setConfirmModal(null);
    } catch (err: any) {
      showToast(err.message || "Lỗi tiến trình xử lý báo cáo", "error");
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredReports = reports.filter(
    (r) =>
      (r.reason || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.target_id || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.reporter_name || "").toLowerCase().includes(searchQuery.toLowerCase()),
  );

  if (authLoading || isLoading) return <PageLoader />;
  if (user?.role !== "admin")
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

  const pendingCount = reports.filter(
    (r) => r.status !== "RESOLVED" && r.status !== "DISMISSED",
  ).length;

  return (
    <div className="app-page gap-6">
      <PageHeader title="Báo cáo" />
      <div className="flex flex-col md:flex-row gap-6 flex-1 min-h-0">
        <aside className="w-full md:w-[320px] shrink-0 flex flex-col space-y-6 overflow-y-auto no-scrollbar pb-6 pr-2">
          <div className="bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:p-0 md:pt-6 space-y-4">
            <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
              Giao diện
            </p>
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="w-full py-2 rounded-[var(--radius-control)] bg-white  text-[var(--ink)] font-medium text-[14px] hover:bg-[var(--surface-quiet)] transition-colors flex items-center justify-center gap-2"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : null}{" "}
              Làm mới
            </button>
          </div>
        </aside>

        <main className="flex-1 min-w-0 flex flex-col min-h-0 pt-6">
          <div className="bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex-1 overflow-hidden flex flex-col min-h-0">
            <div className="flex items-center justify-between p-6 bg-[var(--surface-quiet)]/30">
              <div className="flex items-center gap-3">
                <h2 className="text-[20px] font-medium text-[var(--ink)]">
                  Hàng đợi báo cáo
                </h2>
                {pendingCount > 0 && (
                  <span className="px-3 py-1 bg-[var(--danger)]/10 text-[var(--danger)] text-[13px] font-medium rounded-full flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[var(--danger)] animate-pulse"></div>
                    {pendingCount} chờ xử lý
                  </span>
                )}
              </div>
              <span className="text-[13px] text-[var(--ink-muted)] font-medium">
                Tổng: {reports.length}
              </span>
            </div>

            <div className="overflow-y-auto no-scrollbar flex-1 p-2">
              <table className="w-full text-left text-[14px] border-collapse">
                <thead>
                  <tr className="text-[13px] text-[var(--ink-muted)]">
                    <th className="py-3 px-6 font-medium w-[20%]">Đối tượng</th>
                    <th className="py-3 px-6 font-medium w-[30%]">
                      Nội dung báo cáo
                    </th>
                    <th className="py-3 px-6 font-medium w-[15%]">
                      Người báo cáo
                    </th>
                    <th className="py-3 px-6 font-medium w-[15%]">
                      Trạng thái
                    </th>
                    <th className="py-3 px-6 font-medium text-right w-[20%]">
                      Thao tác
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReports.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-24 text-center">
                        <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                          <div className="w-16 h-16 bg-[var(--surface-quiet)] rounded-[var(--radius-workspace)] flex items-center justify-center mb-4">
                            <FileWarning className="w-8 h-8 text-[var(--border-strong)]" />
                          </div>
                          <h2 className="text-[20px] font-medium text-[var(--ink)] mb-1">
                            {searchQuery ? "Không tìm thấy" : "Chưa có báo cáo"}
                          </h2>
                          <p className="text-[17px] text-[var(--ink-muted)]">
                            {searchQuery
                              ? "Vui lòng thử từ khóa khác."
                              : "Hệ thống hiện không có vi phạm nào."}
                          </p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredReports.map((r) => (
                      <tr
                        key={r.id}
                        className="hover:bg-[var(--surface-quiet)] transition-colors group"
                      >
                        <td className="py-3 px-6">
                          <div className="flex flex-col gap-1">
                            <span className="text-[12px] bg-[var(--border)] text-[var(--ink-muted)] px-2 py-0.5 rounded-md w-fit font-medium">
                              {r.target_type || "Nội dung"}
                            </span>
                            <span className="text-[13px] text-[var(--ink-muted)] font-mono truncate max-w-[150px]">
                              {r.target_id}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-6 max-w-sm">
                          <div className="flex flex-col gap-1">
                            <span className="font-medium text-[var(--ink)]">
                              {r.reason}
                            </span>
                            <p className="text-[13px] text-[var(--ink-muted)] line-clamp-2">
                              "{r.description || "Không có mô tả chi tiết."}"
                            </p>
                          </div>
                        </td>
                        <td className="py-3 px-6">
                          <span className="font-medium text-[var(--ink)]">
                            {r.reporter_name || "Ẩn danh"}
                          </span>
                          <p className="text-[12px] text-[var(--ink-muted)] mt-0.5">
                            {r.created_at
                              ? new Date(r.created_at).toLocaleDateString(
                                  "vi-VN",
                                )
                              : "--"}
                          </p>
                        </td>
                        <td className="py-3 px-6">
                          {r.status === "RESOLVED" ? (
                            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#E8F5E9] text-[var(--success)] rounded-full text-[12px] font-medium">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Đã xử lý
                            </div>
                          ) : r.status === "DISMISSED" ? (
                            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[var(--surface-quiet)] text-[var(--ink-muted)] rounded-full text-[12px] font-medium">
                              <XCircle className="w-3.5 h-3.5" /> Đã bỏ qua
                            </div>
                          ) : (
                            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#FFF4E5] text-[var(--warning)] rounded-full text-[12px] font-medium">
                              <div className="w-2 h-2 rounded-full bg-[var(--warning)] animate-pulse"></div>{" "}
                              Đang chờ
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-6 text-right">
                          {r.status !== "RESOLVED" &&
                          r.status !== "DISMISSED" ? (
                            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() =>
                                  setConfirmModal({
                                    reportId: r.id,
                                    action: "DISMISSED",
                                  })
                                }
                                className="px-3 py-1.5 text-[13px] font-medium text-[var(--ink-muted)] bg-white  hover:bg-[var(--surface-quiet)] rounded-[var(--radius-control)] transition-colors"
                              >
                                Bỏ qua
                              </button>
                              <button
                                onClick={() =>
                                  setConfirmModal({
                                    reportId: r.id,
                                    action: "RESOLVED",
                                  })
                                }
                                className="px-3 py-1.5 text-[13px] font-medium text-white bg-[var(--brand)] hover:bg-[var(--brand-hover)] rounded-[var(--radius-control)] transition-colors"
                              >
                                Xử lý
                              </button>
                            </div>
                          ) : (
                            <span className="text-[var(--ink-faint)]">--</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isProcessing && setConfirmModal(null)}
      >
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2">
            {confirmModal?.action === "RESOLVED" ? (
              <>
                <AlertOctagon className="w-5 h-5 text-[var(--danger)]" /> Xác nhận xử
                lý
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-[var(--ink-muted)]" /> Xác nhận bỏ qua
              </>
            )}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="bg-[var(--surface-quiet)] p-4 rounded-[var(--radius-workspace)] border-[var(--border)] mb-4 font-mono text-[13px] text-[var(--ink-muted)]">
            ID: {confirmModal?.reportId}
          </div>
          <p className="text-[14px] text-[var(--ink-muted)] leading-relaxed">
            {confirmModal?.action === "RESOLVED"
              ? "Bạn có chắc chắn muốn xử lý vi phạm này? Tác giả sẽ nhận được cảnh báo."
              : "Bạn muốn bỏ qua báo cáo này? Nội dung sẽ vẫn hiển thị bình thường."}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => !isProcessing && setConfirmModal(null)}
            disabled={isProcessing}
            className="px-5 py-2 text-[var(--brand)] font-medium hover:bg-[var(--surface-quiet)] rounded-full disabled:opacity-50"
          >
            Hủy
          </button>
          <button
            onClick={confirmResolve}
            disabled={isProcessing}
            className={`pill-button disabled:opacity-50 flex items-center gap-2 ${confirmModal?.action === "RESOLVED" ? "bg-[var(--danger)] hover:bg-[#D70015]" : ""}`}
          >
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />} Xác
            nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
