"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  ArrowUpRight,
  ArrowDownLeft,
  Loader2,
  AlertCircle,
  Info,
  ExternalLink,
  CheckCircle,
} from "lucide-react";
import {
  getWalletBalanceAPI,
  getWalletHistoryAPI,
} from "@/features/payment/services/wallet.service";
import { createDepositLinkAPI } from "@/features/payment/services/deposit.service";
import { requestWithdrawalAPI } from "@/features/payment/services/withdrawal.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PageLoader from "@/shared/components/common/PageLoader";

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

export default function WalletPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();

  const [balance, setBalance] = useState<number>(0);
  const [history, setHistory] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [visible, setVisible] = useState(false);

  const [showTopupModal, setShowTopupModal] = useState(false);
  const [topupAmount, setTopupAmount] = useState(50000);
  const [topupLoading, setTopupLoading] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null);

  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [bankName, setBankName] = useState("");
  const [bankAccount, setBankAccount] = useState("");
  const [accountHolder, setAccountHolder] = useState("");
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  const fetchWalletData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [balanceRes, historyRes] = await Promise.all([
        getWalletBalanceAPI(),
        getWalletHistoryAPI(),
      ]);
      setBalance(balanceRes.data?.balance ?? balanceRes.balance ?? 0);
      const txList = historyRes.data ?? historyRes ?? [];
      setHistory(Array.isArray(txList) ? txList : []);
    } catch (error) {
      showToast("Lỗi trích xuất dữ liệu ví điện tử", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [showToast]);

  useEffect(() => {
    if (user) fetchWalletData();
  }, [user, fetchWalletData]);

  const handleTopup = async () => {
    if (topupAmount < 10000)
      return showToast("Mức nạp tối thiểu là 10.000 VNĐ", "error");
    setTopupLoading(true);
    try {
      const res = await createDepositLinkAPI(topupAmount);
      const url = res?.data?.checkout_url ?? res?.checkout_url ?? null;
      if (url) {
        setShowTopupModal(false);
        window.location.href = url;
      } else {
        showToast("Lỗi kết nối đến cổng thanh toán", "error");
        console.error("Deposit response:", res);
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi khởi tạo giao dịch nạp tiền", "error");
    } finally {
      setTopupLoading(false);
    }
  };

  const handleOpenPayment = () => {
    if (checkoutUrl) {
      window.location.href = checkoutUrl;
    }
  };

  const handleTopupDone = () => {
    setCheckoutUrl(null);
    setShowTopupModal(false);
    setTopupAmount(50000);
    fetchWalletData();
  };

  const handleWithdrawal = async () => {
    const amount = parseInt(withdrawAmount);
    if (!amount || amount < 50)
      return showToast("Mức rút tối thiểu là 50 dl", "error");
    if (amount > balance)
      return showToast("Số dư trong ví không đủ để thực hiện giao dịch", "error");
    if (!bankName.trim()) return showToast("Tên ngân hàng không được để trống", "error");
    if (!bankAccount.trim()) return showToast("Số tài khoản không được để trống", "error");
    if (!accountHolder.trim()) return showToast("Tên chủ tài khoản không được để trống", "error");

    const bankInfo = `${bankName.trim()} | ${bankAccount.trim()} | ${accountHolder.trim()}`;

    setWithdrawLoading(true);
    try {
      await requestWithdrawalAPI(amount, bankInfo);
      showToast("Khởi tạo yêu cầu rút tiền hoàn tất", "success");
      setWithdrawAmount("");
      setBankName("");
      setBankAccount("");
      setAccountHolder("");
      setShowWithdrawModal(false);
      fetchWalletData();
    } catch (e: any) {
      showToast(e.message || "Lỗi thực thi giao dịch rút tiền", "error");
    } finally {
      setWithdrawLoading(false);
    }
  };

  if (authLoading) return <PageLoader />;

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-56px)] gap-6 px-6 text-center">
        <div className="w-20 h-20 bg-[#F5F5F7] rounded-[18px] flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-[#6E6E73]" />
        </div>
        <div>
          <p className="text-[13px] font-medium text-[#6E6E73] mb-4">Truy cập bị hạn chế</p>
          <p className="text-[15px] text-[#6E6E73] mt-2">Đăng nhập để quản lý ví cá nhân</p>
        </div>
        <button onClick={() => (window.location.href = "/dang-nhap")} className="pill-button">
          Đăng nhập
        </button>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col font-sans text-[#1D1D1F]">

      <Modal
        isOpen={showTopupModal}
        onClose={() => {
          if (!topupLoading) {
            setShowTopupModal(false);
            setCheckoutUrl(null);
          }
        }}
      >
        <ModalHeader>
          <ModalTitle>{checkoutUrl ? "Thanh toán đang chờ xác nhận" : "Nạp tiền"}</ModalTitle>
          {!checkoutUrl && (
            <p className="text-[13px] text-[#6E6E73] mt-1">Chọn mệnh giá nạp (VNĐ)</p>
          )}
        </ModalHeader>
        <ModalContent>
          {checkoutUrl ? (
            <div className="space-y-5 text-center">
              <div className="w-16 h-16 bg-[#EBF4FF] rounded-full flex items-center justify-center mx-auto">
                <ExternalLink className="w-8 h-8 text-[#0071E3]" />
              </div>
              <div>
                <p className="text-[17px] font-semibold text-[#1D1D1F]">Trang thanh toán đã mở</p>
                <p className="text-[14px] text-[#6E6E73] mt-2">
                  Hoàn tất thanh toán trên trang PayOS, sau đó nhấn <strong>Xác nhận hoàn tất</strong> để cập nhật số dư.
                </p>
              </div>
              <div className="bg-[#F5F5F7] rounded-[12px] p-4 text-left">
                <p className="text-[13px] text-[#6E6E73]">Số tiền nạp</p>
                <p className="text-[20px] font-bold text-[#1D1D1F]">{topupAmount.toLocaleString()} ₫</p>
                <p className="text-[12px] text-[#6E6E73] mt-1">≈ {(topupAmount / 1000).toFixed(0)} dl</p>
              </div>
              <button
                onClick={handleOpenPayment}
                className="w-full flex items-center justify-center gap-2 py-3 text-[15px] text-[#0071E3] font-medium rounded-[10px] border border-[#D2D2D7] hover:bg-[#F5F5F7] transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Mở lại trang thanh toán
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-3">
                {[50000, 100000, 200000, 500000].map((amt) => (
                  <button
                    key={amt}
                    onClick={() => setTopupAmount(amt)}
                    className={`py-3 text-[15px] font-medium rounded-[10px] transition-colors border ${
                      topupAmount === amt
                        ? "bg-[#0071E3] text-white border-[#0071E3]"
                        : "bg-white text-[#0071E3] border-[#D2D2D7] hover:bg-[#E8E8ED]"
                    }`}
                  >
                    {amt.toLocaleString()} ₫
                  </button>
                ))}
              </div>
              <div className="relative">
                <input
                  type="number"
                  value={topupAmount}
                  onChange={(e) => setTopupAmount(parseInt(e.target.value) || 0)}
                  className="apple-input w-full pr-12 text-center text-[17px] font-semibold"
                  min={10000}
                  step={10000}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[15px] text-[#6E6E73]">₫</span>
              </div>
              <p className="text-[13px] text-[#6E6E73] text-center">1.000 VNĐ = 1 dl</p>
            </div>
          )}
        </ModalContent>
        <ModalFooter>
          {checkoutUrl ? (
            <>
              <button
                onClick={() => setCheckoutUrl(null)}
                className="px-4 py-2 text-[#6E6E73] font-medium rounded-full hover:bg-[#F5F5F7] transition-colors"
              >
                Quay lại
              </button>
              <button
                onClick={handleTopupDone}
                className="pill-button"
              >
                Xác nhận hoàn tất
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setShowTopupModal(false)}
                disabled={topupLoading}
                className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7] transition-colors"
              >
                Hủy
              </button>
              <button
                onClick={handleTopup}
                disabled={topupLoading || topupAmount < 10000}
                className="pill-button disabled:opacity-50 flex items-center gap-2"
              >
                {topupLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Tiếp tục"}
              </button>
            </>
          )}
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={showWithdrawModal}
        onClose={() => !withdrawLoading && setShowWithdrawModal(false)}
      >
        <ModalHeader>
          <ModalTitle>Rút thu nhập</ModalTitle>
          <p className="text-[13px] text-[#6E6E73] mt-1">1 dl = 1.000 VNĐ · Phí 2% · Tối thiểu 50 dl (50.000 VNĐ)</p>
        </ModalHeader>
        <ModalContent>
          <div className="space-y-4">
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1.5">
                Số dl muốn rút
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  placeholder="Tối thiểu 50"
                  min={50}
                  className="apple-input w-full pr-12"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[14px] text-[#6E6E73] font-medium">dl</span>
              </div>
              {withdrawAmount && parseInt(withdrawAmount) >= 50 && (
                <p className="text-[12px] text-[#34C759] mt-1">
                  ≈ {(parseInt(withdrawAmount) * 980).toLocaleString()} VNĐ (sau phí 2%)
                </p>
              )}
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1.5">Tên ngân hàng</label>
              <input
                type="text"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="VD: Vietcombank, MB Bank..."
                className="apple-input w-full"
              />
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1.5">Số tài khoản</label>
              <input
                type="text"
                value={bankAccount}
                onChange={(e) => setBankAccount(e.target.value)}
                placeholder="Nhập số tài khoản ngân hàng"
                className="apple-input w-full"
              />
            </div>
            <div>
              <label className="block text-[13px] font-medium text-[#6E6E73] mb-1.5">Tên chủ tài khoản</label>
              <input
                type="text"
                value={accountHolder}
                onChange={(e) => setAccountHolder(e.target.value)}
                placeholder="Nhập đúng tên chủ tài khoản"
                className="apple-input w-full"
              />
            </div>
            <div className="bg-[#EBF4FF] p-4 rounded-[10px]">
              <h4 className="text-[13px] font-semibold text-[#0071E3] flex items-center gap-1.5 mb-2">
                <Info className="w-4 h-4" /> Lưu ý
              </h4>
              <ul className="text-[12px] text-[#0055C6] list-disc list-inside space-y-1">
                <li>Xử lý trong vòng 24-48 giờ làm việc</li>
                <li>Kiểm tra kỹ thông tin ngân hàng trước khi gửi</li>
                <li>Số dư sẽ bị trừ ngay, hoàn lại nếu bị từ chối</li>
              </ul>
            </div>
          </div>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setShowWithdrawModal(false)}
            disabled={withdrawLoading}
            className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7] transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={
              withdrawLoading ||
              !withdrawAmount ||
              parseInt(withdrawAmount) < 50 ||
              !bankName.trim() ||
              !bankAccount.trim() ||
              !accountHolder.trim()
            }
            className="pill-button disabled:opacity-50 flex items-center gap-2"
          >
            {withdrawLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Gửi yêu cầu"}
          </button>
        </ModalFooter>
      </Modal>

      {/* ===== MAIN CONTENT ===== */}
      <div
        className={`flex flex-col md:flex-row gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
      >
        {/* Sidebar */}
        <aside className="w-full md:w-[280px] shrink-0 space-y-6">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 text-center">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">Số dư khả dụng</h2>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-[48px] font-bold tracking-tight text-[#1D1D1F]">
                {isLoading ? "..." : balance.toLocaleString()}
              </span>
              <span className="text-[20px] font-medium text-[#6E6E73]">dl</span>
            </div>
            <p className="text-[13px] text-[#6E6E73] mt-1">
              ≈ {isLoading ? "..." : (balance * 1000).toLocaleString()} VNĐ
            </p>
            <div className="flex flex-col gap-3 mt-8">
              <button
                onClick={() => { setCheckoutUrl(null); setShowTopupModal(true); }}
                className="pill-button w-full"
              >
                Nạp tiền
              </button>
              {(user?.role === "author" || user?.role === "admin") && (
                <button
                  onClick={() => setShowWithdrawModal(true)}
                  className="py-3 bg-white text-[#0071E3] font-medium rounded-full border border-[#D2D2D7] hover:bg-[#E8E8ED] transition-colors"
                >
                  Rút tiền
                </button>
              )}
            </div>
          </div>
        </aside>

        {/* Transaction history */}
        <main className="flex-1 min-w-0">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 min-h-[500px]">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Lịch sử giao dịch</h2>
              <span className="px-3 py-1 bg-[#E8E8ED] text-[#1D1D1F] text-[13px] font-medium rounded-full">
                {history.length} mục
              </span>
            </div>

            {isLoading ? (
              <div className="py-24 flex justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
              </div>
            ) : history.length === 0 ? (
              <div className="py-24 flex flex-col items-center justify-center bg-[#F5F5F7] rounded-[18px] w-full text-center">
                <p className="text-[17px] text-[#6E6E73]">Chưa có giao dịch nào</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((tx) => {
                  const isIn = tx.type === "TOPUP" || tx.amount > 0;
                  const displayAmount = Math.abs(tx.amount);
                  return (
                    <div
                      key={tx._id}
                      className="flex items-center justify-between p-4 bg-white rounded-[16px] hover:bg-[#FAFAFA] transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                            isIn ? "bg-[#E3F2E1] text-[#34C759]" : "bg-[#F5F5F7] text-[#6E6E73]"
                          }`}
                        >
                          {isIn ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                        </div>
                        <div>
                          <p className="text-[15px] font-medium text-[#1D1D1F]">
                            {tx.note || (tx.type === "TOPUP" ? "Nạp tiền" : tx.type === "WITHDRAW" ? "Rút tiền" : "Giao dịch")}
                          </p>
                          <p className="text-[13px] text-[#6E6E73]">
                            {new Date(tx.created_at).toLocaleString("vi-VN")}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-[17px] font-semibold ${isIn ? "text-[#34C759]" : "text-[#1D1D1F]"}`}>
                          {isIn ? "+" : "-"}{displayAmount.toLocaleString()} dl
                        </p>
                        <p className="text-[12px] text-[#6E6E73] flex items-center justify-end gap-1.5 mt-0.5">
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              tx.status === "COMPLETED" ? "bg-[#34C759]" : "bg-[#FF9500]"
                            }`}
                          />
                          {tx.status === "COMPLETED" ? "Hoàn tất" : "Đang xử lý"}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
