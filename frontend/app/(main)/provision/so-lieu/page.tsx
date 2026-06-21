"use client";

import { useEffect, useState, useCallback } from "react";
import { useToast } from "@/shared/contexts/Toast";
import { getAuthorStatsAPI } from "@/features/finance/services/account_ledger.service";
import { getAuthorRevenueAPI } from "@/features/finance/services/content_monetization.service";
import {
  getDocumentAnalyticsAPI,
  getAcademicMetricsAPI,
} from "@/features/content/services/document_metadata.service";
import { ingestDocumentAPI } from "@/features/ai/services/rag_pipeline.service";
import { requestWithdrawalAPI } from "@/features/finance/services/fiat_withdrawal.service";
import {
  Eye,
  Database,
  Wallet,
  Plus,
  Brain,
  Settings,
  RadioTower,
  Banknote,
  ChevronRight,
  Loader2,
} from "lucide-react";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import { useRouter } from "next/navigation";

export default function StatsPage() {
  const { showToast } = useToast();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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
      const sRes = await getAuthorStatsAPI();
      const data = sRes.data || sRes;
      setStats(data);
      setRevenue(data);
    } catch (err: any) {
      showToast("Không thể tải số liệu thống kê", "error");
    } finally {
      setLoading(false);
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
      <div className="flex justify-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div
        className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "150ms", animationFillMode: "both" }}
      >
        {[
          { label: "Tổng lượt xem", val: stats?.total_views || 0, icon: Eye },
          {
            label: "Kinh nghiệm",
            val: stats?.total_points || 0,
            icon: Database,
          },
          {
            label: "Doanh thu (dl)",
            val: revenue?.available_balance || 0,
            icon: Wallet,
          },
        ].map((s, i) => (
          <div
            key={i}
            className="bg-white p-6 border border-zinc-200 flex flex-col justify-between h-32 rounded-2xl shadow-sm"
          >
            <div className="flex justify-between items-start">
              <span className="text-sm font-medium text-zinc-500">
                {s.label}
              </span>
              <s.icon className="w-4 h-4 text-zinc-400" />
            </div>
            <h4 className="text-3xl font-medium text-black">
              {s.val.toLocaleString()}
            </h4>
          </div>
        ))}
      </div>

      <div
        className="bg-white border border-zinc-200 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-8 duration-300"
        style={{ animationDelay: "200ms", animationFillMode: "both" }}
      >
        <div className="p-6 border-b border-zinc-200 flex justify-between items-center">
          <h3 className="text-base font-medium text-black">Tác phẩm gần đây</h3>
          <button
            onClick={() => setShowWithdrawalModal(true)}
            className="h-9 px-4 bg-black text-white text-sm font-medium rounded-xl flex items-center gap-2"
          >
            <Banknote className="w-4 h-4" /> Rút tiền doanh thu
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-zinc-500 font-medium">
                <th className="px-6 py-4 font-medium">Tiêu đề</th>
                <th className="px-6 py-4 font-medium">Lượt tương tác</th>
                <th className="px-6 py-4 font-medium">Xếp hạng</th>
                <th className="px-6 py-4 font-medium text-right">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200">
              {(stats?.documents || []).map((doc: any, idx: number) => (
                <tr
                  key={doc.id || `stats-doc-${idx}`}
                  onClick={(e) => handleViewDeepAnalytics(doc.id, e)}
                  className="cursor-pointer hover:bg-zinc-50 transition-colors"
                >
                  <td className="px-6 py-4 font-medium text-black">
                    {doc.title}
                  </td>
                  <td className="px-6 py-4 text-zinc-600">
                    {doc.views.toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-zinc-600 font-medium">
                        {doc.rating?.toFixed(1) || "0.0"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <ChevronRight className="w-4 h-4 ml-auto text-zinc-400" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        isOpen={showAnalyticsModal}
        onClose={() => setShowAnalyticsModal(false)}
        className="max-w-2xl"
      >
        <ModalHeader>
          <ModalTitle>Phân tích & Chỉ số học thuật</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2 no-scrollbar">
            {loadingAnalytics ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
                    Tương tác độc giả
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Lượt xem
                      </p>
                      <p className="text-lg font-medium text-black">
                        {(selectedAnalytics?.views || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Thời gian đọc TB
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.avg_read_time || "0 phút"}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Lượt lưu
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.saves || 0}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Bình luận
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAnalytics?.comments || 0}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
                    Chỉ số học thuật
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Tổng số từ
                      </p>
                      <p className="text-lg font-medium text-black">
                        {(selectedAcademic?.word_count || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-xl space-y-1">
                      <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
                        Độ đọc hiểu
                      </p>
                      <p className="text-lg font-medium text-black">
                        {selectedAcademic?.readability_score || 0}/100
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </ModalContent>
      </Modal>

      <Modal
        isOpen={showWithdrawalModal}
        onClose={() => setShowWithdrawalModal(false)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Yêu cầu rút tiền</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Số tiền rút (dl)
              </label>
              <input
                type="number"
                value={withdrawalAmount}
                onChange={(e) =>
                  setWithdrawalAmount(parseInt(e.target.value) || 0)
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Tên ngân hàng
              </label>
              <input
                value={bankInfo.bank_name}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, bank_name: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Số tài khoản
              </label>
              <input
                value={bankInfo.account_number}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, account_number: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                Tên chủ tài khoản
              </label>
              <input
                value={bankInfo.account_name}
                onChange={(e) =>
                  setBankInfo({ ...bankInfo, account_name: e.target.value })
                }
                className="w-full h-10 border border-zinc-200 px-3 text-xs font-medium rounded-xl outline-none focus:border-black bg-white"
              />
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowWithdrawalModal(false)}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-xl flex items-center justify-center"
          >
            Hủy
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={requestingWithdrawal}
            className="flex-1 py-2 bg-black text-white text-xs font-medium border border-black rounded-xl flex items-center justify-center gap-2"
          >
            {requestingWithdrawal ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              "Gửi yêu cầu"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
