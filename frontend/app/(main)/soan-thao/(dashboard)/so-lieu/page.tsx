"use client";

import { useEffect, useState } from "react";
import { useToast } from "@/shared/contexts/ToastContext";
import { getDocumentAnalyticsAPI, getAcademicMetricsAPI } from "@/features/content/services/document_metadata.service";
import { requestWithdrawalAPI } from "@/features/finance/services/fiat_withdrawal.service";
import { Eye, Database, Wallet, Banknote, Loader2, BarChart3, ArrowUpRight, Clock, Bookmark, MessageSquare, FileText, Percent, BookOpen } from "lucide-react";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter, ModalDescription } from "@/shared/components/ui/Modal";
import { getAuthorRevenueAPI, setDocumentPricingAPI } from "@/features/finance/services/content_monetization.service";
import PageLoader from "@/shared/components/common/PageLoader";

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
  const [bankInfo, setBankInfo] = useState({ bank_name: "", account_number: "", account_name: "" });
  const [requestingWithdrawal, setRequestingWithdrawal] = useState(false);

  const [showPricingModal, setShowPricingModal] = useState(false);
  const [pricingDocId, setPricingDocId] = useState("");
  const [pricingDocTitle, setPricingDocTitle] = useState("");
  const [newPrice, setNewPrice] = useState(0);
  const [settingPrice, setSettingPrice] = useState(false);
  
  useEffect(() => { fetchStatsData(); }, []);

  const fetchStatsData = async () => {
    setLoading(true);
    try {
      const revData = await getAuthorRevenueAPI();
      setRevenue(revData.data || revData);
      setStats(revData.data || revData);
    } catch { showToast("Không thể tải số liệu thống kê", "error"); } finally { setLoading(false); requestAnimationFrame(() => setVisible(true)); }
  };

  const handleViewDeepAnalytics = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoadingAnalytics(true); setShowAnalyticsModal(true);
    try {
      const [analyticsData, academicData] = await Promise.all([getDocumentAnalyticsAPI(docId).catch(() => null), getAcademicMetricsAPI(docId).catch(() => null)]);
      setSelectedAnalytics(analyticsData?.data || analyticsData); setSelectedAcademic(academicData?.data || academicData);
    } catch { showToast("Không thể tải chi tiết", "error"); } finally { setLoadingAnalytics(false); }
  };

  const handleSetPricing = async () => {
    if (newPrice < 0) { showToast("Giá không hợp lệ", "error"); return; }
    setSettingPrice(true);
    try {
      await setDocumentPricingAPI(pricingDocId, newPrice);
      showToast("Thiết lập giá thành công", "success"); setShowPricingModal(false);
    } catch (e: any) { showToast(e.message || "Thiết lập giá thất bại", "error"); } finally { setSettingPrice(false); }
  };

  const handleWithdrawal = async () => {
    if (withdrawalAmount <= 0) { showToast("Số tiền không hợp lệ", "error"); return; }
    if (!bankInfo.bank_name || !bankInfo.account_number || !bankInfo.account_name) { showToast("Vui lòng nhập đủ thông tin ngân hàng", "error"); return; }
    setRequestingWithdrawal(true);
    try {
      await requestWithdrawalAPI(withdrawalAmount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi", "success"); setShowWithdrawalModal(false); fetchStatsData();
    } catch (e: any) { showToast(e.message || "Yêu cầu rút tiền thất bại", "error"); } finally { setRequestingWithdrawal(false); }
  };

  if (loading) return (
    <PageLoader />
  );

  return (
    <div className="flex flex-col h-full font-sans">
      <div className={`flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
          {[
            { label: "Tổng lượt xem", val: stats?.total_views || 0, icon: Eye, color: "text-[#0071E3]", bg: "bg-[#0071E3]/10" },
            { label: "Kinh nghiệm", val: stats?.total_points || 0, icon: Database, color: "text-[#FF9F0A]", bg: "bg-[#FF9F0A]/10" },
            { label: "Doanh thu (dl)", val: revenue?.available_balance || 0, icon: Wallet, color: "text-[#34C759]", bg: "bg-[#34C759]/10" },
          ].map((s, i) => (
            <div key={i} className="bg-[#F5F5F7] border-[#E8E8ED] p-6 flex flex-col justify-between h-[140px] rounded-[24px] relative overflow-hidden">
              <div className="flex justify-between items-start relative z-10">
                <span className="text-[13px] font-medium text-[#6E6E73]">{s.label}</span>
                <div className={`w-10 h-10 rounded-[14px] ${s.bg} flex items-center justify-center`}><s.icon className={`w-5 h-5 ${s.color}`} /></div>
              </div>
              <div className="flex items-end gap-3 relative z-10"><h4 className="text-[32px] font-semibold text-[#1D1D1F]">{s.val.toLocaleString()}</h4></div>
            </div>
          ))}
        </div>

        <div className="bg-[#F5F5F7] border-[#E8E8ED] rounded-[24px] flex flex-col flex-1 min-h-0 overflow-hidden pb-6">
          <div className="p-6 border-b border-[#E8E8ED] flex items-center gap-3 bg-[#F5F5F7] shrink-0">
            <BarChart3 className="w-5 h-5 text-[#1D1D1F]" />
            <h3 className="text-[17px] font-medium text-[#1D1D1F]">Hiệu suất tác phẩm</h3>
          </div>
          <div className="flex-1 overflow-auto custom-scrollbar">
            {(stats?.documents || []).length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center p-12 text-center">
                <div className="w-16 h-16 bg-[#F5F5F7] border border-[#E8E8ED] shadow-sm flex items-center justify-center rounded-[18px] mb-4"><BookOpen className="w-8 h-8 text-[#C7C7CC]" /></div>
                <h3 className="text-[17px] font-medium text-[#1D1D1F] mb-2">Chưa có dữ liệu</h3>
                <p className="text-[15px] text-[#6E6E73] max-w-sm">Bạn chưa có tác phẩm nào phát sinh số liệu. Hãy xuất bản thêm nội dung.</p>
              </div>
            ) : (
              <table className="w-full text-left text-[15px] border-collapse min-w-[600px]">
                <thead className="sticky top-0 bg-white z-10 shadow-[0_1px_2px_rgba(0,0,0,0.05)]">
                  <tr className="border-b border-[#E8E8ED] text-[13px] font-medium text-[#6E6E73]">
                    <th className="px-6 py-4 w-1/2">Tiêu đề tác phẩm</th>
                    <th className="px-6 py-4 text-center">Lượt xem</th>
                    <th className="px-6 py-4 text-center">Xếp hạng</th>
                    <th className="px-6 py-4 text-right">Chi tiết</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E8E8ED]">
                  {(stats?.documents || []).map((doc: any, idx: number) => (
                    <tr key={doc.id || idx} onClick={(e) => handleViewDeepAnalytics(doc.id, e)} className="cursor-pointer hover:bg-[#F5F5F7] transition-colors group">
                      <td className="px-6 py-4"><div className="font-semibold text-[#1D1D1F] line-clamp-1">{doc.title}</div></td>
                      <td className="px-6 py-4 text-center"><span className="inline-flex items-center justify-center px-3 py-1 bg-[#0071E3]/10 text-[#0071E3] text-[13px] font-medium rounded-full">{doc.views.toLocaleString()}</span></td>
                      <td className="px-6 py-4 text-center"><span className="inline-flex items-center justify-center px-3 py-1 bg-[#FF9F0A]/10 text-[#FF9F0A] text-[13px] font-medium rounded-full">{doc.rating?.toFixed(1) || "0.0"}</span></td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end items-center gap-2">
                          <div onClick={(e) => { e.stopPropagation(); setPricingDocId(doc.id); setPricingDocTitle(doc.title); setNewPrice(doc.price_dl || 0); setShowPricingModal(true); }} className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-[#E8E8ED] text-[#6E6E73] transition-colors border border-[#E8E8ED]" title="Thiết lập giá"><Banknote className="w-5 h-5" /></div>
                          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#F5F5F7] group-hover:bg-[#0071E3] group-hover:text-white text-[#1D1D1F] transition-colors"><ArrowUpRight className="w-5 h-5" /></div>
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

      <Modal isOpen={showAnalyticsModal} onClose={() => setShowAnalyticsModal(false)} className="max-w-3xl rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-0 shadow-lg overflow-hidden">
        <ModalHeader className="border-b border-[#E8E8ED] p-6 bg-[#F5F5F7]">
          <ModalTitle className="text-[17px] font-semibold text-[#1D1D1F] flex items-center gap-2"><BarChart3 className="w-5 h-5" /> Phân tích & Chỉ số học thuật</ModalTitle>
          <ModalDescription className="text-[13px] text-[#6E6E73] mt-2 ml-7">Báo cáo chi tiết hiệu suất tác phẩm</ModalDescription>
        </ModalHeader>
        <ModalContent className="p-0">
          <div className="max-h-[70vh] overflow-y-auto custom-scrollbar">
            {loadingAnalytics ? (
              <div className="flex flex-col items-center justify-center py-24">
                <Loader2 className="w-8 h-8 animate-spin text-[#0071E3] mb-4" />
                <p className="text-[13px] font-medium text-[#6E6E73]">Đang phân tích dữ liệu...</p>
              </div>
            ) : (
              <div className="p-6 space-y-8 bg-white">
                <div className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E8E8ED] pb-3"><Eye className="w-5 h-5 text-[#1D1D1F]" /><h3 className="text-[17px] font-medium text-[#1D1D1F]">Tương tác độc giả</h3></div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-5 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex flex-col justify-between h-[120px]"><Eye className="w-5 h-5 text-[#0071E3] mb-2" /><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Lượt xem</p><p className="text-[24px] font-semibold text-[#1D1D1F]">{(selectedAnalytics?.views || 0).toLocaleString()}</p></div></div>
                    <div className="p-5 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex flex-col justify-between h-[120px]"><Clock className="w-5 h-5 text-[#AF52DE] mb-2" /><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Đọc TB</p><p className="text-[24px] font-semibold text-[#1D1D1F]">{selectedAnalytics?.avg_read_time || "0 phút"}</p></div></div>
                    <div className="p-5 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex flex-col justify-between h-[120px]"><Bookmark className="w-5 h-5 text-[#34C759] mb-2" /><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Lượt lưu</p><p className="text-[24px] font-semibold text-[#1D1D1F]">{selectedAnalytics?.saves || 0}</p></div></div>
                    <div className="p-5 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex flex-col justify-between h-[120px]"><MessageSquare className="w-5 h-5 text-[#FF9F0A] mb-2" /><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Bình luận</p><p className="text-[24px] font-semibold text-[#1D1D1F]">{selectedAnalytics?.comments || 0}</p></div></div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-[#E8E8ED] pb-3"><BookOpen className="w-5 h-5 text-[#1D1D1F]" /><h3 className="text-[17px] font-medium text-[#1D1D1F]">Chỉ số học thuật</h3></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-6 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex items-center justify-between"><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Tổng số từ</p><p className="text-[24px] font-semibold text-[#1D1D1F]">{(selectedAcademic?.word_count || 0).toLocaleString()}</p></div><div className="w-12 h-12 bg-white rounded-full flex items-center justify-center border border-[#E8E8ED]"><FileText className="w-5 h-5 text-[#1D1D1F]" /></div></div>
                    <div className="p-6 bg-[#F5F5F7] border border-[#E8E8ED] rounded-[18px] flex items-center justify-between"><div><p className="text-[12px] font-medium text-[#6E6E73] mb-1">Độ đọc hiểu</p><p className="text-[24px] font-semibold text-[#1D1D1F] flex items-baseline gap-1">{selectedAcademic?.readability_score || 0}<span className="text-[15px] text-[#6E6E73]">/100</span></p></div><div className="w-12 h-12 bg-white rounded-full flex items-center justify-center border border-[#E8E8ED]"><Percent className="w-5 h-5 text-[#1D1D1F]" /></div></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ModalContent>
        <ModalFooter className="border-t border-[#E8E8ED] p-6 bg-[#F5F5F7] flex justify-end"><button onClick={() => setShowAnalyticsModal(false)} className="h-[44px] px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors">Đóng báo cáo</button></ModalFooter>
      </Modal>

      <Modal isOpen={showWithdrawalModal} onClose={() => !requestingWithdrawal && setShowWithdrawalModal(false)} className="max-w-md rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-0 shadow-lg overflow-hidden">
        <ModalHeader className="border-b border-[#E8E8ED] p-6 bg-[#34C759]/10">
          <ModalTitle className="text-[17px] font-semibold text-[#1D1D1F] flex items-center gap-2"><Banknote className="w-5 h-5 text-[#34C759]" /> Yêu cầu rút tiền</ModalTitle>
          <ModalDescription className="text-[13px] text-[#6E6E73] mt-2 ml-7">Chuyển doanh thu về tài khoản ngân hàng</ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <div className="space-y-6">
            <div className="bg-[#34C759]/10 p-4 rounded-[14px] flex items-center justify-between border border-[#34C759]/20"><span className="text-[13px] font-medium text-[#1D1D1F]">Số dư khả dụng:</span><span className="text-[17px] font-semibold text-[#34C759]">{revenue?.available_balance || 0} dl</span></div>
            <div className="space-y-4">
              <div className="space-y-2"><label className="text-[13px] font-medium text-[#1D1D1F]">Số tiền cần rút (dl)</label><div className="relative"><Banknote className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" /><input type="number" value={withdrawalAmount || ""} onChange={(e) => setWithdrawalAmount(parseInt(e.target.value) || 0)} placeholder="" className="w-full h-[48px] pl-12 pr-4 border border-[#E8E8ED] text-[15px] text-[#1D1D1F] rounded-[14px] outline-none focus:border-[#0071E3] bg-[#F5F5F7] focus:bg-white transition-colors" /></div></div>
              <div className="space-y-2"><label className="text-[13px] font-medium text-[#1D1D1F]">Tên ngân hàng</label><input value={bankInfo.bank_name} onChange={(e) => setBankInfo({ ...bankInfo, bank_name: e.target.value })} placeholder="" className="w-full h-[48px] px-4 border border-[#E8E8ED] text-[15px] text-[#1D1D1F] rounded-[14px] outline-none focus:border-[#0071E3] bg-[#F5F5F7] focus:bg-white transition-colors" /></div>
              <div className="space-y-2"><label className="text-[13px] font-medium text-[#1D1D1F]">Số tài khoản</label><input value={bankInfo.account_number} onChange={(e) => setBankInfo({ ...bankInfo, account_number: e.target.value })} placeholder="" className="w-full h-[48px] px-4 border border-[#E8E8ED] text-[15px] text-[#1D1D1F] rounded-[14px] outline-none focus:border-[#0071E3] bg-[#F5F5F7] focus:bg-white transition-colors" /></div>
              <div className="space-y-2"><label className="text-[13px] font-medium text-[#1D1D1F]">Tên chủ tài khoản</label><input value={bankInfo.account_name} onChange={(e) => setBankInfo({ ...bankInfo, account_name: e.target.value })} placeholder="" className="w-full h-[48px] px-4 border border-[#E8E8ED] text-[15px] text-[#1D1D1F] rounded-[14px] outline-none focus:border-[#0071E3] bg-[#F5F5F7] focus:bg-white transition-colors uppercase" /></div>
            </div>
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-[#E8E8ED] p-6 bg-[#F5F5F7]"><button onClick={() => setShowWithdrawalModal(false)} disabled={requestingWithdrawal} className="flex-1 h-[44px] bg-white border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] rounded-full hover:bg-[#F5F5F7] transition-colors disabled:opacity-50">Hủy bỏ</button><button onClick={handleWithdrawal} disabled={requestingWithdrawal || withdrawalAmount <= 0} className="flex-1 h-[44px] bg-[#34C759] text-white text-[15px] font-medium rounded-full flex items-center justify-center hover:bg-[#2EB150] transition-colors disabled:opacity-50 gap-2">{requestingWithdrawal ? <Loader2 className="w-5 h-5 animate-spin" /> : "Gửi yêu cầu"}</button></ModalFooter>
      </Modal>

      <Modal isOpen={showPricingModal} onClose={() => setShowPricingModal(false)} className="max-w-md rounded-[24px] border-[#E8E8ED] bg-[#F5F5F7] p-6 shadow-lg">
        <ModalHeader><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Thiết lập giá bán</ModalTitle><ModalDescription className="text-[15px] text-[#6E6E73] mt-2">Thay đổi giá bán (dl) cho tác phẩm <span className="font-semibold text-[#1D1D1F]">{pricingDocTitle}</span></ModalDescription></ModalHeader>
        <ModalContent className="my-6">
          <div className="space-y-2">
            <label className="text-[13px] font-medium text-[#1D1D1F]">Giá bán mới (dl)</label>
            <div className="relative"><input type="number" min="0" value={newPrice} onChange={(e) => setNewPrice(Number(e.target.value))} className="w-full h-[52px] pl-4 pr-12 rounded-[14px] border border-[#E8E8ED] text-[15px] font-medium bg-[#F5F5F7] focus:bg-white focus:border-[#0071E3] outline-none transition-all" placeholder="" /><span className="absolute right-4 top-1/2 -translate-y-1/2 text-[15px] font-medium text-[#6E6E73]">dl</span></div>
            <p className="text-[13px] text-[#6E6E73] mt-2">Lưu ý: Nhập 0 để phát hành miễn phí.</p>
          </div>
        </ModalContent>
        <ModalFooter className="flex gap-3 justify-end"><button onClick={() => setShowPricingModal(false)} className="px-6 py-3 rounded-full border border-[#E8E8ED] text-[15px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors">Hủy</button><button onClick={handleSetPricing} disabled={settingPrice} className="px-6 py-3 rounded-full bg-[#0071E3] text-white text-[15px] font-medium disabled:opacity-50 flex items-center gap-2 hover:bg-[#0077ED] transition-colors">{settingPrice ? <Loader2 className="w-5 h-5 animate-spin" /> : <Banknote className="w-5 h-5" />} Xác nhận</button></ModalFooter>
      </Modal>
    </div>
  );
}
