"use client";

import { useEffect, useState, useCallback } from "react";
import {
  getAuthorApplicationsAPI,
  reviewAuthorApplicationAPI,
} from "@/services/operation.service";
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

export default function AuthorApplicationsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const [applications, setApplications] = useState<any[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [searchQuery, setSearchQuery] = useState("");
  const [reviewModal, setReviewModal] = useState<{
    isOpen: boolean;
    appId: string;
    status: string;
  } | null>(null);
  const [reasonText, setReasonText] = useState("");

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
    }
  }, [statusFilter, showToast]);

  useEffect(() => {
    if (
      !authLoading &&
      (user?.role === "admin" || user?.role === "moderator")
    ) {
      fetchData();
    }
  }, [user, authLoading, fetchData]);

  const openReviewModal = (appId: string, status: string) => {
    setReviewModal({ isOpen: true, appId, status });
    setReasonText(
      status === "APPROVED" ? "Đã phê duyệt hồ sơ tác giả." : "",
    );
  };

  const confirmReview = async () => {
    if (!reviewModal) return;
    try {
      await reviewAuthorApplicationAPI(
        reviewModal.appId,
        reviewModal.status,
        reasonText ||
          (reviewModal.status === "APPROVED"
            ? "Đã phê duyệt hồ sơ tác giả."
            : "Hồ sơ chưa đạt tiêu chuẩn kiểm duyệt."),
      );
      showToast("Đã cập nhật trạng thái hồ sơ ứng tuyển.", "success");
      setReviewModal(null);
      fetchData();
    } catch (err: any) {
      showToast(err.message || "Lỗi xử lý hồ sơ.", "error");
    }
  };

  const filteredApplications = applications.filter(
    (app) =>
      (app.user_name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (app.user_email || "").toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const getStatusDisplay = (status: string) => {
    if (status === "PENDING") {
      return (
        <span className="text-[10px] font-bold tracking-widest text-black border border-black px-2 py-1 uppercase">
          Đang chờ
        </span>
      );
    }
    if (status === "APPROVED") {
      return (
        <span className="text-[10px] font-medium tracking-widest text-zinc-500 border border-zinc-200 px-2 py-1 uppercase">
          Đã duyệt
        </span>
      );
    }
    return (
      <span className="text-[10px] font-medium tracking-widest text-zinc-500 border border-zinc-200 px-2 py-1 uppercase">
        Từ chối
      </span>
    );
  };

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
            <h1 className="text-3xl font-semibold text-black">Hồ sơ ứng tuyển</h1>
            <p className="text-sm text-zinc-500 mt-1">Quản lý và xét duyệt tác giả</p>
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

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
          <div className="flex border-b border-zinc-200 w-full md:w-auto">
            {[
              { id: "PENDING", label: "Đang chờ" },
              { id: "APPROVED", label: "Đã duyệt" },
              { id: "REJECTED", label: "Đã từ chối" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setStatusFilter(f.id)}
                className={`pb-3 px-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  statusFilter === f.id
                    ? "border-black text-black"
                    : "border-transparent text-zinc-500 hover:text-black"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Tìm kiếm ứng viên"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full border border-zinc-200 pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-black transition-colors rounded-none bg-white placeholder:text-zinc-400"
            />
          </div>
        </div>

        <div className="border border-zinc-200 bg-white">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[800px]">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50">
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ứng viên</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Nội dung hồ sơ</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Trạng thái</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600">Ngày gửi</th>
                  <th className="py-3 px-6 text-xs font-semibold text-zinc-600 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {filteredApplications.map((app: any) => (
                  <tr key={app._id} className="border-b border-zinc-200 last:border-0 hover:bg-zinc-50 transition-colors">
                    <td className="py-5 px-6 align-top">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-semibold text-black truncate max-w-[200px]">
                          {app.user_name || "Ẩn danh"}
                        </span>
                        <span className="text-xs text-zinc-500 truncate max-w-[200px]">
                          {app.user_email}
                        </span>
                      </div>
                    </td>
                    <td className="py-5 px-6 align-top max-w-sm">
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[10px] font-bold text-black uppercase tracking-wider">
                          {app.type || "Hồ sơ tác giả"}
                        </span>
                        {app.portfolio_url && (
                          <a
                            href={app.portfolio_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-medium text-black hover:underline"
                          >
                            Tài liệu đính kèm
                          </a>
                        )}
                        <p className="text-sm text-zinc-600 line-clamp-3 leading-relaxed mt-1">
                          {app.motivation || "--"}
                        </p>
                      </div>
                    </td>
                    <td className="py-5 px-6 align-top">
                      {getStatusDisplay(statusFilter)}
                    </td>
                    <td className="py-5 px-6 align-top whitespace-nowrap">
                      <span className="text-xs font-medium text-zinc-500">
                        {app.created_at ? new Date(app.created_at).toLocaleDateString("vi-VN") : "--"}
                      </span>
                    </td>
                    <td className="py-5 px-6 align-top text-right">
                      {statusFilter === "PENDING" && (
                        <div className="flex justify-end gap-4">
                          <button
                            onClick={() => openReviewModal(app._id, "REJECTED")}
                            className="text-xs font-semibold text-zinc-500 hover:text-black transition-colors"
                          >
                            Từ chối
                          </button>
                          <button
                            onClick={() => openReviewModal(app._id, "APPROVED")}
                            className="text-xs font-semibold text-black hover:underline underline-offset-4"
                          >
                            Phê duyệt
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
                {filteredApplications.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-24 text-center">
                      <p className="text-sm font-medium text-zinc-500">Không tìm thấy hồ sơ phù hợp</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Modal isOpen={!!reviewModal} onClose={() => setReviewModal(null)} className="max-w-md">
        <ModalHeader>
          <ModalTitle>
            {reviewModal?.status === "APPROVED" ? "Phê duyệt hồ sơ" : "Từ chối hồ sơ"}
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <p className="text-xs font-medium text-zinc-500 leading-relaxed">
              Vui lòng nhập lý do (sẽ được lưu lại và thông báo tới người dùng).
            </p>
            <div className="space-y-2">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Nội dung chi tiết</label>
              <textarea
                className="w-full min-h-[120px] border border-zinc-200 p-3 text-xs font-medium text-black focus:outline-none focus:border-black resize-none bg-zinc-50 placeholder:text-zinc-400 transition-colors"
                value={reasonText}
                onChange={(e) => setReasonText(e.target.value)}
                placeholder="Nhập nội dung..."
              />
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setReviewModal(null)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black hover:bg-zinc-50 transition-colors flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={confirmReview}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black hover:bg-zinc-800 transition-colors flex items-center justify-center"
          >
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
