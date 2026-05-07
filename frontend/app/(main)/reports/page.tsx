"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getReportsAPI as getAdminReportsAPI,
  resolveReportAPI,
} from "@/services/report.service";
import { Loader2, Search } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function ReportsManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
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
      const data = await getAdminReportsAPI();
      setReports(data.data || data || []);
    } catch (err: any) {
      showToast("Không thể kết nối máy chủ báo cáo.", "error");
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (
      !authLoading &&
      (user?.role === "admin" || user?.role === "moderator")
    ) {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const confirmResolve = async () => {
    if (!confirmModal) return;
    setIsProcessing(true);
    try {
      await resolveReportAPI(confirmModal.reportId, confirmModal.action);
      showToast(
        confirmModal.action === "RESOLVED"
          ? "Đã xử lý vi phạm thành công."
          : "Đã bỏ qua báo cáo.",
        "success",
      );
      setConfirmModal(null);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý báo cáo.", "error");
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
            <h1 className="text-3xl font-semibold text-black">Vi phạm & Báo cáo</h1>
            <p className="text-sm text-zinc-500 mt-1">Quản trị an toàn và tuân thủ DocLib</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="text-sm font-medium text-zinc-500 disabled:opacity-50"
            >
              {isRefreshing ? "Đang đồng bộ" : "Đồng bộ dữ liệu"}
            </button>
          </div>
        </header>

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
          <div className="flex border-b border-zinc-200 w-full md:w-auto">
            <div className="pb-3 px-4 text-sm font-medium border-b-2 border-black text-black whitespace-nowrap">
              Hàng đợi báo cáo
            </div>
          </div>

          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Tìm kiếm báo cáo"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full border border-zinc-200 pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-black rounded-none bg-white placeholder:text-zinc-400"
            />
          </div>
        </div>

        <div className="border border-zinc-200 bg-white overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[800px]">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Đối tượng</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Nội dung báo cáo</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Người báo cáo</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Trạng thái</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày gửi</th>
                <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredReports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-24 text-center">
                    <p className="text-sm font-medium text-zinc-500">Hệ thống hiện tại không có báo cáo vi phạm</p>
                  </td>
                </tr>
              ) : (
                filteredReports.map((report: any) => (
                  <tr key={report.id} className="border-b border-zinc-200 last:border-0">
                    <td className="py-4 px-6 align-top">
                      <div className="flex flex-col gap-1">
                        <span className="text-[10px] font-bold text-black uppercase tracking-widest">
                          {report.target_type || "Nội dung"}
                        </span>
                        <span className="text-xs text-zinc-500 font-mono truncate max-w-[150px]">
                          {report.target_id}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6 align-top max-w-sm">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-semibold text-black">{report.reason}</span>
                        <p className="text-xs text-zinc-600 line-clamp-2">
                          "{report.description || "Không có mô tả chi tiết kèm theo."}"
                        </p>
                      </div>
                    </td>
                    <td className="py-4 px-6 align-top">
                      <span className="text-sm font-medium text-black">
                        {report.reporter_name || "Ẩn danh"}
                      </span>
                    </td>
                    <td className="py-4 px-6 align-top whitespace-nowrap">
                      {report.status === "RESOLVED" || report.status === "DISMISSED" ? (
                        <span className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                          {report.status === "RESOLVED" ? "Đã xử lý" : "Đã bỏ qua"}
                        </span>
                      ) : (
                        <span className="text-xs font-bold text-black border border-black px-2 py-1 uppercase tracking-widest">
                          Đang chờ
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 align-top whitespace-nowrap">
                      <span className="text-xs font-medium text-zinc-500">
                        {report.created_at ? new Date(report.created_at).toLocaleDateString("vi-VN") : "--"}
                      </span>
                    </td>
                    <td className="py-4 px-6 align-top text-right">
                      {report.status !== "RESOLVED" && report.status !== "DISMISSED" && (
                        <div className="flex justify-end gap-4">
                          <button
                            onClick={() => setConfirmModal({ reportId: report.id, action: "DISMISSED" })}
                            className="text-xs font-bold text-zinc-500 uppercase tracking-wider"
                          >
                            Bỏ qua
                          </button>
                          <button
                            onClick={() => setConfirmModal({ reportId: report.id, action: "RESOLVED" })}
                            className="text-xs font-bold text-black uppercase tracking-wider border border-black px-2 py-1"
                          >
                            Xử lý
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <Modal isOpen={!!confirmModal} onClose={() => !isProcessing && setConfirmModal(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>
            {confirmModal?.action === "RESOLVED" ? "Xác nhận xử lý vi phạm" : "Xác nhận bỏ qua báo cáo"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            {confirmModal?.action === "RESOLVED"
              ? "Bạn có chắc chắn muốn xử lý vi phạm đối với nội dung này? Các hành động liên quan sẽ được thực thi ngay lập tức."
              : "Bạn quyết định bỏ qua báo cáo này và đánh dấu là không hợp lệ?"}
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => !isProcessing && setConfirmModal(null)}
            disabled={isProcessing}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50 flex items-center justify-center rounded-none"
          >
            Hủy
          </button>
          <button
            onClick={confirmResolve}
            disabled={isProcessing}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black disabled:opacity-50 flex items-center justify-center gap-2 rounded-none"
          >
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin" />} Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
