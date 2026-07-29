"use client";

import { useCallback, useEffect, useState } from "react";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  getDocumentAnalyticsAPI,
  getAcademicMetricsAPI,
} from "@/features/content/services/document.service";
import { requestWithdrawalAPI } from "@/features/payment/services/withdrawal.service";
import {
  Eye,
  Database,
  Wallet,
  Banknote,
  Loader2,
  BarChart3,
  ArrowUpRight,
  Clock,
  Bookmark,
  MessageSquare,
  FileText,
  Percent,
  BookOpen,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";
import {
  getAuthorRevenueAPI,
  setDocumentPricingAPI,
} from "@/features/payment/services/monetization.service";
import PageLoader from "@/shared/components/common/PageLoader";
import PageHeader from "@/shared/components/common/PageHeader";

export default function StatsPage() {
  const { showToast } = useToast();
  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [selectedAnalytics, setSelectedAnalytics] = useState<any>(null);
  const [selectedAcademic, setSelectedAcademic] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState(0);
  const [bankInfo, setBankInfo] = useState({
    bank_name: "",
    account_number: "",
    account_name: "",
  });
  const [requestingWithdrawal, setRequestingWithdrawal] = useState(false);

  const [showPricingModal, setShowPricingModal] = useState(false);
  const [pricingDocId, setPricingDocId] = useState("");
  const [pricingDocTitle, setPricingDocTitle] = useState("");
  const [newPrice, setNewPrice] = useState(0);
  const [settingPrice, setSettingPrice] = useState(false);

  const fetchStatsData = useCallback(async () => {
    setLoading(true);
    try {
      const revData = await getAuthorRevenueAPI();
      setRevenue(revData.data || revData);
      setStats(revData.data || revData);
    } catch {
      showToast("Lỗi trích xuất số liệu phân tích", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    fetchStatsData();
  }, [fetchStatsData]);

  const handleViewDeepAnalytics = async (
    docId: string,
    e: React.MouseEvent,
  ) => {
    e.stopPropagation();
    setLoadingAnalytics(true);
    setShowAnalyticsModal(true);
    try {
      const [analyticsData, academicData] = await Promise.all([
        getDocumentAnalyticsAPI(docId).catch(() => null),
        getAcademicMetricsAPI(docId).catch(() => null),
      ]);
      setSelectedAnalytics(analyticsData?.data || analyticsData);
      setSelectedAcademic(academicData?.data || academicData);
    } catch {
      showToast("Lỗi trích xuất báo cáo chi tiết", "error");
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const handleSetPricing = async () => {
    if (newPrice < 0) {
      showToast("Lỗi sai lệch định dạng chuẩn giá trị", "error");
      return;
    }
    setSettingPrice(true);
    try {
      await setDocumentPricingAPI(pricingDocId, newPrice);
      showToast("Cập nhật cấu hình định giá hoàn tất", "success");
      setShowPricingModal(false);
    } catch (e: any) {
      showToast(e.message || "Lỗi cập nhật cấu hình định giá", "error");
    } finally {
      setSettingPrice(false);
    }
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) {
      showToast("Lỗi giá trị giao dịch không hợp lệ", "error");
      return;
    }
    if (
      !bankInfo.bank_name ||
      !bankInfo.account_number ||
      !bankInfo.account_name
    ) {
      showToast("Lỗi thiếu hụt trường thông tin thanh toán", "error");
      return;
    }
    setRequestingWithdrawal(true);
    try {
      await requestWithdrawalAPI(withdrawalAmount, bankInfo);
      showToast("Khởi tạo tiến trình giao dịch tài chính hoàn tất", "success");
      setShowWithdrawalModal(false);
      fetchStatsData();
    } catch (e: any) {
      showToast(e.message || "Lỗi khởi tạo tiến trình giao dịch tài chính", "error");
    } finally {
      setRequestingWithdrawal(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="app-page gap-6">
      <PageHeader title="Số liệu" />
      <div
        className={`bg-[var(--surface-quiet)] md:bg-transparent rounded-[var(--radius-panel)] md:rounded-none p-6 md:px-0 md:pt-6 flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
          {[
            {
              label: "Tổng lượt xem",
              val: stats?.total_views || 0,
              icon: Eye,
              color: "text-[var(--brand)]",
              bg: "bg-[var(--brand)]/10",
            },
            {
              label: "Kinh nghiệm",
              val: stats?.total_points || 0,
              icon: Database,
              color: "text-[var(--warning)]",
              bg: "bg-[var(--warning)]/10",
            },
            {
              label: "Doanh thu (dl)",
              val: revenue?.available_balance || 0,
              icon: Wallet,
              color: "text-[var(--success)]",
              bg: "bg-[var(--success)]/10",
            },
          ].map((s, i) => (
            <div
              key={i}
              className="bg-white border border-[var(--border)] p-6 flex flex-col justify-between h-[140px] rounded-[var(--radius-panel)] relative overflow-hidden"
            >
              <div className="flex justify-between items-start relative z-10">
                <span className="text-[13px] font-medium text-[var(--ink-muted)]">
                  {s.label}
                </span>
                <div
                  className={`w-10 h-10 rounded-[var(--radius-control)] ${s.bg} flex items-center justify-center`}
                >
                  <s.icon className={`w-5 h-5 ${s.color}`} />
                </div>
              </div>
              <div className="flex items-end gap-3 relative z-10">
                <h4 className="text-[32px] font-semibold text-[var(--ink)]">
                  {s.val.toLocaleString()}
                </h4>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white border border-[var(--border)] rounded-[var(--radius-panel)] flex flex-col flex-1 min-h-0 overflow-hidden pb-6">
          <div className="p-6 flex items-center gap-3 bg-white border-b border-[var(--border)] shrink-0">
            <BarChart3 className="w-5 h-5 text-[var(--ink)]" />
            <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
              Hiệu suất tác phẩm
            </p>
          </div>
          <div className="flex-1 overflow-auto custom-scrollbar">
            {(stats?.documents || []).length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <div className="w-16 h-16 bg-[var(--surface-quiet)] flex items-center justify-center rounded-[var(--radius-panel)] mb-4">
                  <BookOpen className="w-8 h-8 text-[var(--border-strong)]" />
                </div>
                <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4 mb-2">
                  Chưa có dữ liệu
                </p>
                <p className="text-[15px] text-[var(--ink-muted)] max-w-sm">
                  Bạn chưa có tác phẩm nào phát sinh số liệu. Hãy xuất bản thêm
                  nội dung.
                </p>
              </div>
            ) : (
              <table className="w-full text-left text-[15px] border-collapse min-w-[600px]">
                <thead className="sticky top-0 bg-white z-10">
                  <tr className="text-[13px] font-medium text-[var(--ink-muted)]">
                    <th className="px-6 py-4 w-1/2">Tiêu đề tác phẩm</th>
                    <th className="px-6 py-4 text-center">Lượt xem</th>
                    <th className="px-6 py-4 text-center">Xếp hạng</th>
                    <th className="px-6 py-4 text-right">Chi tiết</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats?.documents || []).map((doc: any, idx: number) => (
                    <tr
                      key={doc.id || idx}
                      onClick={(e) => handleViewDeepAnalytics(doc.id, e)}
                      className="cursor-pointer hover:bg-[var(--surface-quiet)] transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="font-semibold text-[var(--ink)] line-clamp-1">
                          {doc.title}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center px-3 py-1 bg-[var(--brand)]/10 text-[var(--brand)] text-[13px] font-medium rounded-full">
                          {doc.views.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center px-3 py-1 bg-[var(--warning)]/10 text-[var(--warning)] text-[13px] font-medium rounded-full">
                          {doc.rating?.toFixed(1) || "0.0"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end items-center gap-2">
                          <div
                            onClick={(e) => {
                              e.stopPropagation();
                              setPricingDocId(doc.id);
                              setPricingDocTitle(doc.title);
                              setNewPrice(doc.price_dl || 0);
                              setShowPricingModal(true);
                            }}
                            className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-[var(--border)] text-[var(--ink-muted)] transition-colors"
                            title="Thiết lập giá"
                          >
                            <Banknote className="w-5 h-5" />
                          </div>
                          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[var(--surface-quiet)] group-hover:bg-[var(--brand)] group-hover:text-white text-[var(--ink)] transition-colors">
                            <ArrowUpRight className="w-5 h-5" />
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      <Modal
        isOpen={showAnalyticsModal}
        onClose={() => setShowAnalyticsModal(false)}
        className="max-w-3xl"
      >
        <ModalHeader>
          <ModalTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" /> Phân tích & Chỉ số học thuật
          </ModalTitle>
          <ModalDescription className="ml-7">
            Báo cáo chi tiết hiệu suất tác phẩm
          </ModalDescription>
        </ModalHeader>
        <ModalContent>
          <div className="max-h-[70vh] overflow-y-auto custom-scrollbar">
            {loadingAnalytics ? (
              <div className="flex flex-col items-center justify-center py-24">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--brand)] mb-4" />
                <p className="text-[13px] font-medium text-[var(--ink-muted)]">
                  Đang phân tích dữ liệu
                </p>
              </div>
            ) : (
              <div className="p-6 space-y-8 bg-white">
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-3">
                    <Eye className="w-5 h-5 text-[var(--ink)]" />
                    <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                      Tương tác độc giả
                    </p>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-5 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex flex-col justify-between h-[120px]">
                      <Eye className="w-5 h-5 text-[var(--brand)] mb-2" />
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Lượt xem
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)]">
                          {(selectedAnalytics?.views || 0).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="p-5 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex flex-col justify-between h-[120px]">
                      <Clock className="w-5 h-5 text-[#AF52DE] mb-2" />
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Đọc TB
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)]">
                          {selectedAnalytics?.avg_read_time || "0 phút"}
                        </p>
                      </div>
                    </div>
                    <div className="p-5 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex flex-col justify-between h-[120px]">
                      <Bookmark className="w-5 h-5 text-[var(--success)] mb-2" />
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Lượt lưu
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)]">
                          {selectedAnalytics?.saves || 0}
                        </p>
                      </div>
                    </div>
                    <div className="p-5 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex flex-col justify-between h-[120px]">
                      <MessageSquare className="w-5 h-5 text-[var(--warning)] mb-2" />
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Bình luận
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)]">
                          {selectedAnalytics?.comments || 0}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-2 pb-3">
                    <BookOpen className="w-5 h-5 text-[var(--ink)]" />
                    <p className="text-[13px] font-medium text-[var(--ink-muted)] mb-4">
                      Chỉ số học thuật
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-6 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex items-center justify-between">
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Tổng số từ
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)]">
                          {(selectedAcademic?.word_count || 0).toLocaleString()}
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                        <FileText className="w-5 h-5 text-[var(--ink)]" />
                      </div>
                    </div>
                    <div className="p-6 bg-[var(--surface-quiet)] rounded-[var(--radius-panel)] flex items-center justify-between">
                      <div>
                        <p className="text-[12px] font-medium text-[var(--ink-muted)] mb-1">
                          Độ đọc hiểu
                        </p>
                        <p className="text-[24px] font-semibold text-[var(--ink)] flex items-baseline gap-1">
                          {selectedAcademic?.readability_score || 0}
                          <span className="text-[15px] text-[var(--ink-muted)]">
                            /100
                          </span>
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
                        <Percent className="w-5 h-5 text-[var(--ink)]" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowAnalyticsModal(false)}
            className="h-[44px] px-8 bg-[var(--brand)] text-white text-[15px] font-medium rounded-full hover:bg-[var(--brand-hover)] transition-colors"
          >
            Đóng báo cáo
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showWithdrawalModal}
        onClose={() => !requestingWithdrawal && setShowWithdrawalModal(false)}
      >
        <ModalHeader className="bg-[var(--success)]/10">
          <ModalTitle className="flex items-center gap-2">
            <Banknote className="w-5 h-5 text-[var(--success)]" /> Yêu cầu rút tiền
          </ModalTitle>
          <ModalDescription className="ml-7">
            Chuyển doanh thu về tài khoản ngân hàng
          </ModalDescription>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-6">
            <div className="bg-[var(--success)]/10 p-4 rounded-[var(--radius-control)] flex items-center justify-between border-[var(--success)]/20">
              <span className="text-[13px] font-medium text-[var(--ink)]">
                Số dư khả dụng:
              </span>
              <span className="text-[17px] font-semibold text-[var(--success)]">
                {revenue?.available_balance || 0} dl
              </span>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink)]">
                  Số tiền cần rút (dl)
                </label>
                <div className="relative">
                  <Banknote className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--ink-muted)]" />
                  <input
                    type="number"
                    value={withdrawalAmount || ""}
                    onChange={(e) =>
                      setWithdrawalAmount(parseInt(e.target.value) || 0)
                    }
                    placeholder=""
                    className="w-full h-[48px] pl-12 pr-4 text-[15px] text-[var(--ink)] rounded-[var(--radius-control)] outline-none focus:border-[var(--brand)] bg-[var(--surface-quiet)] focus:bg-white transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink)]">
                  Tên ngân hàng
                </label>
                <input
                  value={bankInfo.bank_name}
                  onChange={(e) =>
                    setBankInfo({ ...bankInfo, bank_name: e.target.value })
                  }
                  placeholder=""
                  className="w-full h-[48px] px-4 text-[15px] text-[var(--ink)] rounded-[var(--radius-control)] outline-none focus:border-[var(--brand)] bg-[var(--surface-quiet)] focus:bg-white transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink)]">
                  Số tài khoản
                </label>
                <input
                  value={bankInfo.account_number}
                  onChange={(e) =>
                    setBankInfo({ ...bankInfo, account_number: e.target.value })
                  }
                  placeholder=""
                  className="w-full h-[48px] px-4 text-[15px] text-[var(--ink)] rounded-[var(--radius-control)] outline-none focus:border-[var(--brand)] bg-[var(--surface-quiet)] focus:bg-white transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[var(--ink)]">
                  Tên chủ tài khoản
                </label>
                <input
                  value={bankInfo.account_name}
                  onChange={(e) =>
                    setBankInfo({ ...bankInfo, account_name: e.target.value })
                  }
                  placeholder=""
                  className="w-full h-[48px] px-4 text-[15px] text-[var(--ink)] rounded-[var(--radius-control)] outline-none focus:border-[var(--brand)] bg-[var(--surface-quiet)] focus:bg-white transition-colors uppercase"
                />
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowWithdrawalModal(false)}
            disabled={requestingWithdrawal}
            className="flex-1 h-[44px] bg-white text-[15px] font-medium text-[var(--ink)] rounded-full hover:bg-[var(--surface-quiet)] transition-colors disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={requestingWithdrawal || withdrawalAmount <= 0}
            className="flex-1 h-[44px] bg-[var(--success)] text-white text-[15px] font-medium rounded-full flex items-center justify-center hover:bg-[#2EB150] transition-colors disabled:opacity-50 gap-2"
          >
            {requestingWithdrawal ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Gửi yêu cầu"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showPricingModal}
        onClose={() => setShowPricingModal(false)}
      >
        <ModalHeader>
          <ModalTitle>
            Thiết lập giá bán
          </ModalTitle>
          <ModalDescription>
            Thay đổi giá bán (dl) cho tác phẩm{" "}
            <span className="font-semibold text-[var(--ink)]">
              {pricingDocTitle}
            </span>
          </ModalDescription>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[var(--ink)]">
              Giá bán mới (dl)
            </label>
            <div className="relative">
              <input
                type="number"
                min="0"
                value={newPrice}
                onChange={(e) => setNewPrice(Number(e.target.value))}
                className="w-full h-[52px] pl-4 pr-12 rounded-[var(--radius-control)] text-[15px] font-medium bg-[var(--surface-quiet)] focus:bg-white focus:border-[var(--brand)] outline-none transition-all"
                placeholder=""
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[15px] font-medium text-[var(--ink-muted)]">
                dl
              </span>
            </div>
            <p className="text-[13px] text-[var(--ink-muted)] mt-2">
              Lưu ý: Nhập 0 để phát hành miễn phí.
            </p>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowPricingModal(false)}
            className="px-6 py-3 rounded-full text-[15px] font-medium text-[var(--ink)] hover:bg-[var(--surface-quiet)] transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSetPricing}
            disabled={settingPrice}
            className="px-6 py-3 rounded-full bg-[var(--brand)] text-white text-[15px] font-medium disabled:opacity-50 flex items-center gap-2 hover:bg-[var(--brand-hover)] transition-colors"
          >
            {settingPrice ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Banknote className="w-5 h-5" />
            )}{" "}
            Xác nhận
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
