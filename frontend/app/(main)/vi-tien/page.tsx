"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { ArrowUpRight, ArrowDownLeft, Loader2, AlertCircle, Info, Wallet, Ticket, History } from "lucide-react";
import { getWalletBalanceAPI, getWalletHistoryAPI, redeemVoucherAPI } from "@/features/finance/services/account_ledger.service";
import { createDepositLinkAPI } from "@/features/finance/services/fiat_deposit.service";
import { requestWithdrawalAPI } from "@/features/finance/services/fiat_withdrawal.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";
import { usePayOS } from "@payos/payos-checkout";

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

const PayOSEmbedded = ({ checkoutUrl, onSuccess, onCancel, onExit }: { checkoutUrl: string; onSuccess?: (event: any) => void; onCancel?: (event: any) => void; onExit?: (event: any) => void; }) => {
  const { open, exit } = usePayOS({
    RETURN_URL: window.location.origin + "/vi-tien",
    ELEMENT_ID: "payos-checkout-container",
    CHECKOUT_URL: checkoutUrl,
    embedded: true,
    onSuccess: (event: any) => onSuccess?.(event),
    onCancel: (event: any) => onCancel?.(event),
    onExit: (event: any) => onExit?.(event),
  } as any);

  useEffect(() => { open(); return () => { if (exit) exit(); }; }, [open, exit]);

  return <div id="payos-checkout-container" className="w-full min-h-[450px] border border-[#D2D2D7] rounded-[18px] overflow-hidden bg-white"></div>;
};

export default function WalletPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  
  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [voucherCode, setVoucherCode] = useState("");
  const [isRedeeming, setIsRedeeming] = useState(false);
  const [visible, setVisible] = useState(false);

  const [showTopupModal, setShowTopupModal] = useState(false);
  const [topupAmount, setTopupAmount] = useState(50000);
  const [topupLoading, setTopupLoading] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);

  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState("");
  const [bankInfo, setBankInfo] = useState("");
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  const fetchWalletData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [balanceRes, historyRes] = await Promise.all([getWalletBalanceAPI(), getWalletHistoryAPI()]);
      setBalance(balanceRes.data?.balance || balanceRes.balance || 0);
      setHistory(historyRes.data || historyRes || []);
    } catch (error) {
      showToast("Lỗi tải dữ liệu ví", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [user, showToast]);

  useEffect(() => { if (user) fetchWalletData(); }, [user, fetchWalletData]);

  const handleRedeemVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!voucherCode.trim() || isRedeeming) return;
    setIsRedeeming(true);
    try {
      const res = await redeemVoucherAPI(voucherCode.trim());
      if (res) {
        showToast("Kích hoạt voucher thành công.", "success");
        setVoucherCode("");
        fetchWalletData();
      }
    } catch (error: any) {
      showToast(error.message || "Voucher không hợp lệ", "error");
    } finally { setIsRedeeming(false); }
  };

  const handleTopup = async () => {
    if (topupAmount < 10000) return showToast("Số tiền tối thiểu là 10.000 VNĐ", "error");
    setTopupLoading(true);
    try {
      const res = await createDepositLinkAPI(topupAmount);
      const url = res.data?.checkout_url || res.data?.payment_url || res.checkout_url;
      if (url) setCheckoutUrl(url);
      else showToast("Lỗi khởi tạo thanh toán", "error");
    } catch (e: any) { showToast(e.message || "Lỗi nạp tiền", "error"); } finally { setTopupLoading(false); }
  };

  const handleWithdrawal = async () => {
    const amount = parseInt(withdrawalAmount);
    if (!amount || amount < 50000) return showToast("Tối thiểu 50.000 dl", "error");
    if (!bankInfo.trim()) return showToast("Nhập thông tin ngân hàng", "error");
    setWithdrawLoading(true);
    try {
      await requestWithdrawalAPI(amount, bankInfo);
      showToast("Yêu cầu rút tiền thành công", "success");
      setWithdrawalAmount(""); setBankInfo(""); setShowWithdrawModal(false); fetchWalletData();
    } catch (e: any) { showToast(e.message || "Rút tiền thất bại", "error"); } finally { setWithdrawLoading(false); }
  };

  if (authLoading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>;

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-44px)] gap-6 px-6 text-center">
        <div className="w-20 h-20 bg-[#F5F5F7] rounded-[24px] flex items-center justify-center"><AlertCircle className="w-8 h-8 text-[#6E6E73]" /></div>
        <div>
          <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Truy cập bị hạn chế</h2>
          <p className="text-[15px] text-[#6E6E73] mt-2">Đăng nhập để quản lý ví cá nhân</p>
        </div>
        <button onClick={() => (window.location.href = "/dang-nhap")} className="pill-button">Đăng nhập</button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-8 min-h-[calc(100dvh-44px)] font-sans text-[#1D1D1F]">
      <Modal isOpen={showTopupModal} onClose={() => { setShowTopupModal(false); setCheckoutUrl(null); }} className={`rounded-[24px] bg-[#F5F5F7] p-0 border-none shadow-2xl ${checkoutUrl ? "max-w-2xl" : "max-w-md"}`}>
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">{checkoutUrl ? "Thanh toán giao dịch" : "Nạp tiền"}</ModalTitle>
          {!checkoutUrl && <p className="text-[13px] text-[#6E6E73] mt-1">Chọn mệnh giá nạp (VNĐ)</p>}
        </ModalHeader>
        <ModalContent className="p-6 pt-0">
          {checkoutUrl ? (
            <PayOSEmbedded checkoutUrl={checkoutUrl} onSuccess={() => { showToast("Thành công", "success"); setCheckoutUrl(null); setShowTopupModal(false); fetchWalletData(); }} onCancel={() => { showToast("Đã hủy", "error"); setCheckoutUrl(null); }} onExit={() => setCheckoutUrl(null)} />
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-3">
                {[50000, 100000, 200000, 500000].map((amt) => (
                  <button key={amt} onClick={() => setTopupAmount(amt)} className={`py-3 text-[15px] font-medium rounded-[14px] transition-colors ${topupAmount === amt ? "bg-[#0071E3] text-white" : "bg-white text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}>
                    {amt.toLocaleString()} ₫
                  </button>
                ))}
              </div>
              <div className="relative">
                <input type="number" value={topupAmount} onChange={(e) => setTopupAmount(parseInt(e.target.value) || 0)} className="apple-input w-full pr-12 text-center text-[17px] font-semibold" />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[15px] text-[#6E6E73]">₫</span>
              </div>
              <p className="text-[13px] text-[#6E6E73] text-center">1.000 VNĐ = 1 dl</p>
            </div>
          )}
        </ModalContent>
        {!checkoutUrl && (
          <ModalFooter className="p-4 flex justify-end gap-3 bg-white rounded-b-[24px]">
            <button onClick={() => setShowTopupModal(false)} disabled={topupLoading} className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7] transition-colors">Hủy</button>
            <button onClick={handleTopup} disabled={topupLoading || topupAmount < 10000} className="pill-button">{topupLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Tiếp tục"}</button>
          </ModalFooter>
        )}
      </Modal>

      <Modal isOpen={showWithdrawModal} onClose={() => setShowWithdrawModal(false)} className="max-w-md rounded-[24px] bg-[#F5F5F7] p-0 border-none shadow-2xl">
        <ModalHeader className="p-6">
          <ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Rút thu nhập</ModalTitle>
          <p className="text-[13px] text-[#6E6E73] mt-1">1 dl = 1.000 VNĐ (Phí 2%)</p>
        </ModalHeader>
        <ModalContent className="p-6 pt-0 space-y-4">
          <input type="number" value={withdrawalAmount} onChange={(e) => setWithdrawalAmount(e.target.value)} className="apple-input w-full" placeholder="Số tiền rút (dl) tối thiểu 50.000" />
          <input type="text" value={bankInfo} onChange={(e) => setBankInfo(e.target.value)} className="apple-input w-full" placeholder="VCB - 123456789 - NGUYEN VAN A" />
          <div className="bg-[#EBF4FF] p-4 rounded-[14px]">
            <h4 className="text-[13px] font-semibold text-[#0071E3] flex items-center gap-1.5 mb-2"><Info className="w-4 h-4" /> Lưu ý</h4>
            <ul className="text-[12px] text-[#0055C6] list-disc list-inside space-y-1"><li>Xử lý trong 48h</li><li>Kiểm tra kỹ thông tin</li></ul>
          </div>
        </ModalContent>
        <ModalFooter className="p-4 flex justify-end gap-3 bg-white rounded-b-[24px]">
          <button onClick={() => setShowWithdrawModal(false)} disabled={withdrawLoading} className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7] transition-colors">Hủy</button>
          <button onClick={handleWithdrawal} disabled={withdrawLoading || !withdrawalAmount || !bankInfo} className="pill-button">{withdrawLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Rút tiền"}</button>
        </ModalFooter>
      </Modal>

      <div className={`grid lg:grid-cols-12 gap-8 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}>
        <aside className="lg:col-span-4 xl:col-span-4 space-y-8">
          <div className="bg-[#F5F5F7] rounded-[24px] p-8 text-center">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm"><Wallet className="w-8 h-8 text-[#0071E3]" /></div>
            <p className="text-[14px] font-medium text-[#6E6E73] mb-1">Số dư khả dụng</p>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-[48px] font-bold tracking-tight text-[#1D1D1F]">{balance.toLocaleString()}</span>
              <span className="text-[20px] font-medium text-[#6E6E73]">dl</span>
            </div>
            <div className="flex flex-col gap-3 mt-8">
              <button onClick={() => setShowTopupModal(true)} className="pill-button w-full">Nạp tiền</button>
              {(user?.role === "author" || user?.role === "admin") && <button onClick={() => setShowWithdrawModal(true)} className="py-3 bg-white text-[#1D1D1F] font-medium rounded-full hover:bg-[#E8E8ED] transition-colors">Rút tiền</button>}
            </div>
          </div>

          <div className="bg-[#F5F5F7] rounded-[24px] p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm"><Ticket className="w-5 h-5 text-[#0071E3]" /></div>
              <h3 className="text-[17px] font-semibold text-[#1D1D1F]">Voucher</h3>
            </div>
            <form onSubmit={handleRedeemVoucher} className="space-y-4">
              <input type="text" value={voucherCode} onChange={(e) => setVoucherCode(e.target.value.toUpperCase())} placeholder="Nhập mã ưu đãi" className="apple-input w-full text-center uppercase tracking-wider" />
              <button type="submit" disabled={isRedeeming || !voucherCode.trim()} className="pill-button w-full">{isRedeeming ? <Loader2 className="w-5 h-5 animate-spin" /> : "Kích hoạt"}</button>
            </form>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-8">
          <div className="bg-[#F5F5F7] rounded-[24px] p-8 min-h-[500px]">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Lịch sử giao dịch</h2>
              <span className="px-3 py-1 bg-[#E8E8ED] text-[#1D1D1F] text-[13px] font-medium rounded-full">{history.length} mục</span>
            </div>

            {isLoading ? (
              <div className="py-24 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" /></div>
            ) : history.length === 0 ? (
              <div className="py-24 text-center"><History className="w-12 h-12 text-[#D2D2D7] mx-auto mb-4" /><p className="text-[15px] text-[#6E6E73]">Chưa có giao dịch</p></div>
            ) : (
              <div className="space-y-3">
                {history.map((tx) => (
                  <div key={tx._id} className="flex items-center justify-between p-4 bg-white rounded-[16px] hover:shadow-sm transition-shadow">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${tx.type === "TOPUP" ? "bg-[#E3F2E1] text-[#34C759]" : "bg-[#F5F5F7] text-[#1D1D1F]"}`}>
                        {tx.type === "TOPUP" ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                      </div>
                      <div>
                        <p className="text-[15px] font-medium text-[#1D1D1F]">{tx.note || (tx.type === "TOPUP" ? "Nạp tiền" : "Rút tiền")}</p>
                        <p className="text-[13px] text-[#6E6E73]">{new Date(tx.created_at).toLocaleString("vi-VN")}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-[17px] font-semibold ${tx.type === "TOPUP" ? "text-[#34C759]" : "text-[#1D1D1F]"}`}>{tx.type === "TOPUP" ? "+" : "-"}{tx.amount.toLocaleString()} dl</p>
                      <p className="text-[12px] text-[#6E6E73] flex items-center justify-end gap-1.5 mt-0.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${tx.status === "COMPLETED" ? "bg-[#34C759]" : "bg-[#FF9500]"}`} />
                        {tx.status === "COMPLETED" ? "Hoàn tất" : "Đang xử lý"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
