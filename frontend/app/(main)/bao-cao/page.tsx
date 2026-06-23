"use client";

import { useEffect, useState, useCallback } from "react";

import { Loader2, Search, AlertOctagon, CheckCircle2, XCircle, RefreshCcw, FileWarning, ShieldAlert } from "lucide-react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { useRouter } from "next/navigation";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";

export default function ReportsManagementPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const router = useRouter();
  const { showToast } = useToast();
  
  const [reports, setReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [visible, setVisible] = useState(false);
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
      showToast("Không thể kết nối máy chủ báo cáo.", "error");
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

  const confirmResolve = async () => {
    if (!confirmModal) return;
    setIsProcessing(true);
    try {
      setConfirmModal(null);
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

  const pendingCount = reports.filter(r => r.status !== "RESOLVED" && r.status !== "DISMISSED").length;

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col gap-6 font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <div className="flex flex-col gap-6 h-full min-h-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-4 md:p-6 flex flex-col md:flex-row gap-4 items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0 shadow-sm hidden md:flex">
              <AlertOctagon className="w-6 h-6 text-black" />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
                Vi phạm & Báo cáo
              </h1>
              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                Quản trị an toàn và tuân thủ DocLib
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="relative flex-1 md:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input
                type="text"
                placeholder="Tìm kiếm báo cáo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-11 pl-10 pr-4 bg-zinc-50 border border-zinc-100 text-sm font-medium text-zinc-900 focus:outline-none focus:border-zinc-300 focus:bg-white rounded-2xl transition-all shadow-sm"
              />
            </div>
            <button
              onClick={fetchData}
              disabled={isRefreshing}
              className="h-11 px-5 border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-900 text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm shrink-0"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCcw className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">Đồng bộ</span>
            </button>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm overflow-hidden flex flex-col flex-1 min-h-0">
          <div className="flex items-center justify-between p-6 border-b border-zinc-100">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">
                Hàng đợi báo cáo
              </h2>
              {pendingCount > 0 && (
                <span className="px-2 py-0.5 bg-red-100 text-red-600 text-[10px] font-bold uppercase tracking-widest rounded-lg flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                  {pendingCount} cần xử lý
                </span>
              )}
            </div>
            <span className="px-3 py-1 bg-zinc-100 text-zinc-900 text-[10px] font-bold uppercase tracking-widest rounded-xl">
              Tổng số: {reports.length}
            </span>
          </div>
          
          <div className="overflow-y-auto custom-scrollbar flex-1">
            <table className="w-full text-left text-sm border-collapse min-w-[800px]">
              <thead className="sticky top-0 bg-white/95 backdrop-blur-sm z-10">
                <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                  <th className="w-[15%] px-6 py-4 whitespace-nowrap">Đối tượng</th>
                  <th className="w-[30%] px-6 py-4">Nội dung báo cáo</th>
                  <th className="w-[15%] px-6 py-4 whitespace-nowrap">Người báo cáo</th>
                  <th className="w-[10%] px-6 py-4 whitespace-nowrap">Ngày gửi</th>
                  <th className="w-[15%] px-6 py-4 whitespace-nowrap">Trạng thái</th>
                  <th className="w-[15%] px-6 py-4 text-right whitespace-nowrap">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50">
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-32 text-center">
                      <div className="flex flex-col items-center justify-center bg-white border border-zinc-100 rounded-3xl p-12 max-w-sm mx-auto shadow-sm">
                        <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                          <FileWarning className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                        </div>
                        <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">
                          {searchQuery ? "Không tìm thấy kết quả" : "Chưa có báo cáo"}
                        </h2>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                          {searchQuery ? "Vui lòng thử từ khóa khác" : "Hệ thống hiện tại không có vi phạm nào"}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((report: any) => (
                    <tr
                      key={report.id}
                      className="group hover:bg-zinc-50/50 transition-colors"
                    >
                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-col gap-1.5">
                          <span className="text-[9px] font-bold text-zinc-900 uppercase tracking-widest px-2 py-0.5 bg-zinc-100 rounded-md w-fit">
                            {report.target_type || "Nội dung"}
                          </span>
                          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest font-mono truncate max-w-[150px]" title={report.target_id}>
                            {report.target_id}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top max-w-sm">
                        <div className="flex flex-col gap-1.5">
                          <span className="text-xs font-bold text-zinc-900">
                            {report.reason}
                          </span>
                          <p className="text-[10px] font-bold text-zinc-500 leading-relaxed line-clamp-2">
                            "{report.description || "Không có mô tả chi tiết kèm theo."}"
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 align-top whitespace-nowrap">
                        <span className="text-xs font-bold text-zinc-900">
                          {report.reporter_name || "Ẩn danh"}
                        </span>
                      </td>
                      <td className="px-6 py-4 align-top whitespace-nowrap">
                        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                          {report.created_at
                            ? new Date(report.created_at).toLocaleDateString("vi-VN")
                            : "--"}
                        </span>
                      </td>
                      <td className="px-6 py-4 align-top whitespace-nowrap">
                        {report.status === "RESOLVED" ? (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-50 border border-green-100 rounded-lg">
                            <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                            <span className="text-[9px] font-bold uppercase tracking-widest text-green-700">Đã xử lý</span>
                          </div>
                        ) : report.status === "DISMISSED" ? (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-50 border border-zinc-200 rounded-lg">
                            <XCircle className="w-3.5 h-3.5 text-zinc-500" />
                            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-600">Đã bỏ qua</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-orange-50 border border-orange-100 rounded-lg">
                            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-orange-700">Đang chờ</span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 align-top text-right">
                        {report.status !== "RESOLVED" && report.status !== "DISMISSED" ? (
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() =>
                                setConfirmModal({
                                  reportId: report.id,
                                  action: "DISMISSED",
                                })
                              }
                              className="px-3 h-8 flex items-center justify-center text-[9px] font-bold text-zinc-600 bg-white border border-zinc-200 hover:bg-zinc-50 rounded-xl uppercase tracking-widest transition-colors shadow-sm"
                            >
                              Bỏ qua
                            </button>
                            <button
                              onClick={() =>
                                setConfirmModal({
                                  reportId: report.id,
                                  action: "RESOLVED",
                                })
                              }
                              className="px-3 h-8 flex items-center justify-center text-[9px] font-bold text-white bg-black hover:bg-zinc-800 rounded-xl uppercase tracking-widest transition-colors shadow-sm"
                            >
                              Xử lý
                            </button>
                          </div>
                        ) : (
                          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                            --
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !isProcessing && setConfirmModal(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            {confirmModal?.action === "RESOLVED" ? (
              <><AlertOctagon className="w-5 h-5 text-red-500" /> Xác nhận xử lý vi phạm</>
            ) : (
              <><XCircle className="w-5 h-5 text-zinc-500" /> Xác nhận bỏ qua báo cáo</>
            )}
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mt-1 ml-7">
            ID: {confirmModal?.reportId}
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed bg-zinc-50 border border-zinc-100 p-4 rounded-2xl">
            {confirmModal?.action === "RESOLVED"
              ? "Bạn có chắc chắn muốn xử lý vi phạm đối với nội dung này? Các hành động liên quan sẽ được thực thi ngay lập tức và tác giả sẽ nhận được cảnh báo."
              : "Bạn quyết định bỏ qua báo cáo này và đánh dấu là không hợp lệ? Nội dung sẽ vẫn được hiển thị bình thường."}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => !isProcessing && setConfirmModal(null)}
            disabled={isProcessing}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={confirmResolve}
            disabled={isProcessing}
            className={`flex-1 h-11 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md gap-2 ${
              confirmModal?.action === "RESOLVED" ? "bg-red-600 hover:bg-red-700" : "bg-black hover:bg-zinc-800"
            }`}
          >
            {isProcessing && <Loader2 className="w-4 h-4 animate-spin" />}
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
