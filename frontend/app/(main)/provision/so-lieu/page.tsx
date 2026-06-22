"use client";

import { useEffect, useState, useCallback } from "react";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  getDocumentAnalyticsAPI,
  getAcademicMetricsAPI,
} from "@/features/content/services/document_metadata.service";
import { requestWithdrawalAPI } from "@/features/finance/services/fiat_withdrawal.service";
import {
  Eye,
  Database,
  Wallet,
  Banknote,
  ChevronRight,
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
import { useRouter } from "next/navigation";

export default function StatsPage() {
  const { showToast } = useToast();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  // Deep Analytics Modal
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [selectedAnalytics, setSelectedAnalytics] = useState<any>(null);
  const [selectedAcademic, setSelectedAcademic] = useState<any>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  // Withdrawal
  const [showWithdrawalModal, setShowWithdrawalModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState(0);
  const [bankInfo, setBankInfo] = useState({
    bank_name: "",
    account_number: "",
    account_name: "",
  });
  const [requestingWithdrawal, setRequestingWithdrawal] = useState(false);

  useEffect(() => {
    fetchStatsData();
  }, []);

  const fetchStatsData = async () => {
    setLoading(true);
    try {
      // API doanh thu đã bị gỡ bỏ ở Backend
      setStats(null);
      setRevenue(null);
    } catch (err: any) {
      showToast("Không thể tải số liệu thống kê", "error");
    } finally {
      setLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  };

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
    } catch (err: any) {
      showToast("Không thể tải chi tiết", "error");
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) {
      showToast("Số tiền không hợp lệ", "error");
      return;
    }
    if (
      !bankInfo.bank_name ||
      !bankInfo.account_number ||
      !bankInfo.account_name
    ) {
      showToast("Vui lòng nhập đủ thông tin ngân hàng", "error");
      return;
    }

    setRequestingWithdrawal(true);
    try {
      await requestWithdrawalAPI(withdrawalAmount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi", "success");
      setShowWithdrawalModal(false);
      fetchStatsData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại", "error");
    } finally {
      setRequestingWithdrawal(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang tải số liệu...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
              Báo cáo & Số liệu
            </h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
              Tổng quan về hiệu suất nội dung và doanh thu
            </p>
          </div>
          <button
            onClick={() => setShowWithdrawalModal(true)}
            className="h-10 px-4 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-xl flex items-center gap-2 transition-all hover:scale-[1.02] hover:-translate-y-0.5 shadow-md group"
          >
            <Banknote className="w-3.5 h-3.5" /> 
            <span className="hidden sm:inline">Rút tiền doanh thu</span>
            <span className="sm:hidden">Rút tiền</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
          {[
            { label: "Tổng lượt xem", val: stats?.total_views || 0, icon: Eye, color: "text-blue-600", bg: "bg-blue-50" },
            { label: "Kinh nghiệm", val: stats?.total_points || 0, icon: Database, color: "text-orange-600", bg: "bg-orange-50" },
            { label: "Doanh thu (dl)", val: revenue?.available_balance || 0, icon: Wallet, color: "text-green-600", bg: "bg-green-50" },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <div
                key={i}
                className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 flex flex-col justify-between h-32 rounded-3xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group"
              >
                <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full ${s.bg} opacity-50 group-hover:scale-150 transition-transform duration-700 ease-out`} />
                <div className="flex justify-between items-start relative z-10">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                    {s.label}
                  </span>
                  <div className={`w-8 h-8 rounded-xl ${s.bg} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${s.color}`} />
                  </div>
                </div>
                <div className="flex items-end gap-3 relative z-10">
                  <h4 className="text-3xl font-bold tracking-tight text-zinc-900">
                    {s.val.toLocaleString()}
                  </h4>
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm flex flex-col flex-1 min-h-0 overflow-hidden pb-6">
          <div className="p-6 border-b border-zinc-100 flex items-center gap-2 bg-zinc-50/50 shrink-0">
            <BarChart3 className="w-4 h-4 text-black" />
            <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest">Hiệu suất tác phẩm</h3>
          </div>
          
          <div className="flex-1 overflow-auto custom-scrollbar">
            {(stats?.documents || []).length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mb-4">
                  <BookOpen className="w-8 h-8 text-zinc-300 stroke-[1.5]" />
                </div>
                <h3 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-1">Chưa có dữ liệu</h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-sm">
                  Bạn chưa có tác phẩm nào phát sinh số liệu. Hãy xuất bản thêm nội dung.
                </p>
              </div>
            ) : (
              <table className="w-full text-left text-sm border-collapse min-w-[600px]">
                <thead className="sticky top-0 bg-white/95 backdrop-blur-sm z-10 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                  <tr className="border-b border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                    <th className="px-6 py-4 w-1/2">Tiêu đề tác phẩm</th>
                    <th className="px-6 py-4 text-center">Lượt xem</th>
                    <th className="px-6 py-4 text-center">Xếp hạng</th>
                    <th className="px-6 py-4 text-right">Chi tiết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-50">
                  {(stats?.documents || []).map((doc: any, idx: number) => (
                    <tr
                      key={doc.id || `stats-doc-${idx}`}
                      onClick={(e) => handleViewDeepAnalytics(doc.id, e)}
                      className="cursor-pointer hover:bg-zinc-50 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div className="font-bold text-zinc-900 line-clamp-1 group-hover:text-black transition-colors">{doc.title}</div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center min-w-[48px] px-2 py-1 bg-blue-50 text-blue-700 text-[10px] font-bold rounded-lg border border-blue-100">
                          {doc.views.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center min-w-[48px] px-2 py-1 bg-orange-50 text-orange-700 text-[10px] font-bold rounded-lg border border-orange-100">
                          {doc.rating?.toFixed(1) || "0.0"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="w-8 h-8 ml-auto rounded-xl flex items-center justify-center group-hover:bg-black group-hover:text-white text-zinc-300 transition-all shadow-sm group-hover:shadow-md bg-white border border-zinc-100">
                          <ArrowUpRight className="w-4 h-4" />
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

      {/* Analytics Modal */}
      <Modal
        isOpen={showAnalyticsModal}
        onClose={() => setShowAnalyticsModal(false)}
        className="max-w-3xl rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-2xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-zinc-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-zinc-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" /> Phân tích & Chỉ số học thuật
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-1 ml-7">
            Báo cáo chi tiết hiệu suất tác phẩm
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-0">
          <div className="max-h-[70vh] overflow-y-auto custom-scrollbar">
            {loadingAnalytics ? (
              <div className="flex flex-col items-center justify-center py-24">
                <Loader2 className="w-8 h-8 animate-spin text-zinc-300 mb-4" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">Đang phân tích dữ liệu...</p>
              </div>
            ) : (
              <div className="p-6 space-y-8 bg-white">
                {/* Tương tác độc giả */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-zinc-100 pb-3">
                    <Eye className="w-4 h-4 text-black" />
                    <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-900">
                      Tương tác độc giả
                    </h3>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-5 bg-zinc-50 border border-zinc-100 rounded-2xl flex flex-col justify-between h-28 relative overflow-hidden group hover:border-blue-200 transition-colors">
                      <div className="absolute right-0 top-0 w-16 h-16 bg-blue-100 rounded-bl-full opacity-50 -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
                      <Eye className="w-4 h-4 text-blue-500 mb-2 relative z-10" />
                      <div className="relative z-10">
                        <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Lượt xem</p>
                        <p className="text-xl font-bold tracking-tight text-zinc-900">{(selectedAnalytics?.views || 0).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="p-5 bg-zinc-50 border border-zinc-100 rounded-2xl flex flex-col justify-between h-28 relative overflow-hidden group hover:border-purple-200 transition-colors">
                      <div className="absolute right-0 top-0 w-16 h-16 bg-purple-100 rounded-bl-full opacity-50 -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
                      <Clock className="w-4 h-4 text-purple-500 mb-2 relative z-10" />
                      <div className="relative z-10">
                        <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Đọc TB</p>
                        <p className="text-xl font-bold tracking-tight text-zinc-900">{selectedAnalytics?.avg_read_time || "0 phút"}</p>
                      </div>
                    </div>
                    <div className="p-5 bg-zinc-50 border border-zinc-100 rounded-2xl flex flex-col justify-between h-28 relative overflow-hidden group hover:border-green-200 transition-colors">
                      <div className="absolute right-0 top-0 w-16 h-16 bg-green-100 rounded-bl-full opacity-50 -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
                      <Bookmark className="w-4 h-4 text-green-500 mb-2 relative z-10" />
                      <div className="relative z-10">
                        <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Lượt lưu</p>
                        <p className="text-xl font-bold tracking-tight text-zinc-900">{selectedAnalytics?.saves || 0}</p>
                      </div>
                    </div>
                    <div className="p-5 bg-zinc-50 border border-zinc-100 rounded-2xl flex flex-col justify-between h-28 relative overflow-hidden group hover:border-orange-200 transition-colors">
                      <div className="absolute right-0 top-0 w-16 h-16 bg-orange-100 rounded-bl-full opacity-50 -mr-8 -mt-8 group-hover:scale-150 transition-transform duration-500"></div>
                      <MessageSquare className="w-4 h-4 text-orange-500 mb-2 relative z-10" />
                      <div className="relative z-10">
                        <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Bình luận</p>
                        <p className="text-xl font-bold tracking-tight text-zinc-900">{selectedAnalytics?.comments || 0}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Chỉ số học thuật */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-zinc-100 pb-3">
                    <BookOpen className="w-4 h-4 text-black" />
                    <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-900">
                      Chỉ số học thuật
                    </h3>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-6 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-between group hover:shadow-sm transition-shadow">
                      <div>
                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Tổng số từ</p>
                        <p className="text-2xl font-bold tracking-tight text-zinc-900">{(selectedAcademic?.word_count || 0).toLocaleString()}</p>
                      </div>
                      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm border border-zinc-100">
                        <FileText className="w-5 h-5 text-zinc-400 group-hover:text-black transition-colors" />
                      </div>
                    </div>
                    <div className="p-6 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-between group hover:shadow-sm transition-shadow">
                      <div>
                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Độ đọc hiểu</p>
                        <p className="text-2xl font-bold tracking-tight text-zinc-900 flex items-baseline gap-1">
                          {selectedAcademic?.readability_score || 0}<span className="text-sm text-zinc-400">/100</span>
                        </p>
                      </div>
                      <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-sm border border-zinc-100">
                        <Percent className="w-5 h-5 text-zinc-400 group-hover:text-black transition-colors" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter className="border-t border-zinc-100 p-5 bg-zinc-50/50 flex justify-end">
          <button
            onClick={() => setShowAnalyticsModal(false)}
            className="h-11 px-6 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl transition-all hover:bg-zinc-800 shadow-sm"
          >
            Đóng báo cáo
          </button>
        </ModalFooter>
      </Modal>

      {/* Withdrawal Modal */}
      <Modal
        isOpen={showWithdrawalModal}
        onClose={() => !requestingWithdrawal && setShowWithdrawalModal(false)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-2xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6 bg-green-50/50">
          <ModalTitle className="text-sm font-bold tracking-tight text-green-700 flex items-center gap-2">
            <Banknote className="w-5 h-5" /> Yêu cầu rút tiền
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-green-600 mt-1 ml-7">
            Chuyển doanh thu về tài khoản ngân hàng
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="space-y-5">
            <div className="bg-green-50 p-4 rounded-2xl border border-green-100 flex items-center justify-between">
              <span className="text-[10px] font-bold text-green-700 uppercase tracking-widest">Số dư khả dụng:</span>
              <span className="text-base font-bold text-green-700">{revenue?.available_balance || 0} dl</span>
            </div>

            <div className="space-y-4 pt-2">
              <div className="space-y-2 relative">
                <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest ml-1">
                  Số tiền cần rút (dl)
                </label>
                <div className="relative">
                  <Banknote className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    type="number"
                    value={withdrawalAmount || ""}
                    onChange={(e) => setWithdrawalAmount(parseInt(e.target.value) || 0)}
                    placeholder="Nhập số tiền..."
                    className="w-full h-11 pl-10 pr-4 border border-zinc-200 text-sm font-bold text-zinc-900 rounded-2xl outline-none focus:border-green-500 bg-white shadow-sm transition-colors"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest ml-1">
                  Tên ngân hàng
                </label>
                <input
                  value={bankInfo.bank_name}
                  onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })}
                  placeholder="VD: Vietcombank, Techcombank..."
                  className="w-full h-11 px-4 border border-zinc-200 text-xs font-bold text-zinc-900 rounded-2xl outline-none focus:border-green-500 bg-white shadow-sm transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest ml-1">
                  Số tài khoản
                </label>
                <input
                  value={bankInfo.account_number}
                  onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })}
                  placeholder="Nhập số tài khoản..."
                  className="w-full h-11 px-4 border border-zinc-200 text-xs font-bold text-zinc-900 rounded-2xl outline-none focus:border-green-500 bg-white shadow-sm transition-colors"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest ml-1">
                  Tên chủ tài khoản
                </label>
                <input
                  value={bankInfo.account_name}
                  onChange={(e) => setBankInfo({ ...bankInfo, account_name: e.target.value })}
                  placeholder="VIET HOA KHONG DAU"
                  className="w-full h-11 px-4 border border-zinc-200 text-xs font-bold text-zinc-900 rounded-2xl outline-none focus:border-green-500 bg-white shadow-sm transition-colors uppercase"
                />
              </div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setShowWithdrawalModal(false)}
            disabled={requestingWithdrawal}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl transition-all hover:scale-[1.02] shadow-sm disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={requestingWithdrawal || withdrawalAmount <= 0}
            className="flex-1 h-11 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center transition-all hover:scale-[1.02] shadow-md gap-2 bg-green-600 hover:bg-green-700 disabled:opacity-50"
          >
            {requestingWithdrawal ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Gửi yêu cầu"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
