"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/Auth";
import {
  History,
  CreditCard,
  Gift,
  ArrowUpRight,
  ArrowDownLeft,
  Plus,
  Loader2,
  AlertCircle,
  Info,
  TrendingUp,
  Clock,
} from "lucide-react";
import {
  getWalletBalanceAPI,
  getWalletHistoryAPI,
  redeemVoucherAPI,
} from "@/services/wallet.service";
import { createDepositLinkAPI } from "@/services/deposit.service";
import { requestWithdrawalAPI } from "@/services/withdrawal.service";
import { getAuthorRevenueAPI } from "@/services/monetization.service";
import { useToast } from "@/contexts/Toast";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
import { usePayOS } from "@payos/payos-checkout";

interface Transaction {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note: string;
  created_at: string;
}

const PayOSEmbedded = ({
  checkoutUrl,
  onSuccess,
  onCancel,
  onExit,
}: {
  checkoutUrl: string;
  onSuccess?: (event: any) => void;
  onCancel?: (event: any) => void;
  onExit?: (event: any) => void;
}) => {
  const { open, exit } = usePayOS({
    RETURN_URL: window.location.origin + "/vi-tien",
    ELEMENT_ID: "payos-checkout-container",
    CHECKOUT_URL: checkoutUrl,
    embedded: true,
    onSuccess: (event: any) => onSuccess?.(event),
    onCancel: (event: any) => onCancel?.(event),
    onExit: (event: any) => onExit?.(event),
  } as any);

  useEffect(() => {
    open();
    return () => {
      if (exit) exit();
    };
  }, [open, exit]);

  return (
    <div
      id="payos-checkout-container"
      className="w-full min-h-[450px] border border-zinc-200"
    ></div>
  );
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

  const [revenue, setRevenue] = useState<any>(null);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [withdrawalAmount, setWithdrawalAmount] = useState("");
  const [bankInfo, setBankInfo] = useState("");
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  const fetchWalletData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [balanceRes, historyRes] = await Promise.all([
        getWalletBalanceAPI(),
        getWalletHistoryAPI(),
      ]);

      setBalance(balanceRes.data?.balance || balanceRes.balance || 0);
      setHistory(historyRes.data || historyRes || []);

      if (user?.role === "author" || user?.role === "admin") {
        try {
          const revRes = await getAuthorRevenueAPI();
          setRevenue(revRes.data || revRes || {});
        } catch (e) {
          console.error("Error loading revenue", e);
        }
      }
    } catch (error) {
      showToast("Lỗi tải dữ liệu ví", "error");
    } finally {
      setIsLoading(false);
      requestAnimationFrame(() => setVisible(true));
    }
  }, [user, showToast]);

  useEffect(() => {
    if (user) fetchWalletData();
  }, [user, fetchWalletData]);

  const handleRedeemVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!voucherCode.trim() || isRedeeming) return;

    setIsRedeeming(true);
    try {
      const res = await redeemVoucherAPI(voucherCode.trim());
      if (res) {
        showToast(
          "Kích hoạt voucher thành công. Số dư đã được cập nhật",
          "success"
        );
        setVoucherCode("");
        fetchWalletData();
      }
    } catch (error: any) {
      showToast(
        error.message || "Voucher không hợp lệ hoặc đã hết hạn",
        "error"
      );
    } finally {
      setIsRedeeming(false);
    }
  };

  const handleTopup = async () => {
    if (topupAmount < 10000) {
      showToast("Số tiền nạp tối thiểu là 10.000 VNĐ", "error");
      return;
    }
    setTopupLoading(true);
    try {
      const res = await createDepositLinkAPI(topupAmount);
      const url = res.data?.checkout_url || res.data?.payment_url || res.checkout_url;
      if (url) {
        setCheckoutUrl(url);
      } else {
        showToast("Không thể khởi tạo thanh toán lúc này", "error");
      }
    } catch (e: any) {
      showToast(e.message || "Lỗi hệ thống khi nạp tiền", "error");
    } finally {
      setTopupLoading(false);
    }
  };

  const handleWithdrawal = async () => {
    const amount = parseInt(withdrawalAmount);
    if (!amount || amount < 50000) {
      showToast("Số tiền tối thiểu để rút là 50.000 dl", "error");
      return;
    }
    if (!bankInfo.trim()) {
      showToast("Vui lòng nhập thông tin ngân hàng", "error");
      return;
    }
    setWithdrawLoading(true);
    try {
      await requestWithdrawalAPI(amount, bankInfo);
      showToast("Yêu cầu rút tiền đã được gửi thành công", "success");
      setWithdrawalAmount("");
      setBankInfo("");
      setShowWithdrawModal(false);
      fetchWalletData();
    } catch (e: any) {
      showToast(e.message || "Yêu cầu rút tiền thất bại", "error");
    } finally {
      setWithdrawLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-6 font-sans px-6 text-center">
        <div className="w-16 h-16 bg-zinc-50 flex items-center justify-center border border-zinc-200">
          <AlertCircle className="w-6 h-6 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-black">
            Truy cập bị hạn chế
          </h2>
          <p className="text-sm font-medium text-zinc-500">
            Vui lòng đăng nhập để quản lý tài chính cá nhân
          </p>
        </div>
        <button
          onClick={() => (window.location.href = "/dang-nhap")}
          className="bg-black text-white h-10 px-8 text-xs font-medium flex items-center justify-center rounded-none"
        >
          Đăng nhập ngay
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <Modal
        isOpen={showTopupModal}
        onClose={() => {
          setShowTopupModal(false);
          setCheckoutUrl(null);
        }}
        className={checkoutUrl ? "max-w-2xl" : "max-w-md"}
      >
        <ModalHeader>
          <ModalTitle>{checkoutUrl ? "Thanh toán giao dịch" : "Nạp tiền (VNĐ)"}</ModalTitle>
          {!checkoutUrl && <ModalDescription>Chọn mệnh giá hoặc nhập số tiền cần nạp</ModalDescription>}
        </ModalHeader>

        <ModalContent>
          {checkoutUrl ? (
            <PayOSEmbedded
              checkoutUrl={checkoutUrl}
              onSuccess={() => {
                showToast("Nạp tiền thành công", "success");
                setCheckoutUrl(null);
                setShowTopupModal(false);
                fetchWalletData();
              }}
              onCancel={() => {
                showToast("Đã hủy thanh toán", "error");
                setCheckoutUrl(null);
              }}
              onExit={() => {
                setCheckoutUrl(null);
              }}
            />
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[50000, 100000, 200000, 500000].map((amt) => (
                  <button
                    key={amt}
                    onClick={() => setTopupAmount(amt)}
                    className={`py-3 text-xs font-medium border rounded-none ${
                      topupAmount === amt
                        ? "bg-zinc-100 border-zinc-200 text-black font-semibold"
                        : "bg-white border-zinc-200 text-zinc-500"
                    }`}
                  >
                    {amt.toLocaleString()} VNĐ
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Số tiền khác</label>
                <div className="relative">
                  <input
                    type="number"
                    value={topupAmount}
                    onChange={(e) => setTopupAmount(parseInt(e.target.value) || 0)}
                    className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-zinc-400">VNĐ</span>
                </div>
              </div>

              <div className="flex items-center justify-between py-3 border-t border-zinc-200">
                <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Tỷ giá</span>
                <span className="text-xs font-medium text-black">1.000 VNĐ = 1 dl</span>
              </div>
            </div>
          )}
        </ModalContent>

        {!checkoutUrl && (
          <ModalFooter>
            <button
              onClick={() => setShowTopupModal(false)}
              disabled={topupLoading}
              className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50"
            >
              Hủy bỏ
            </button>
            <button
              onClick={handleTopup}
              disabled={topupLoading || topupAmount < 10000}
              className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {topupLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận nạp"}
            </button>
          </ModalFooter>
        )}
      </Modal>

      <Modal
        isOpen={showWithdrawModal}
        onClose={() => setShowWithdrawModal(false)}
        className="max-w-md"
      >
        <ModalHeader>
          <ModalTitle>Rút tiền (dl)</ModalTitle>
          <ModalDescription>Tỷ lệ quy đổi: 1 dl = 1.000 VNĐ (Phí hệ thống 2%)</ModalDescription>
        </ModalHeader>

        <ModalContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Số tiền rút (dl)</label>
            <div className="relative">
              <input
                type="number"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none"
                placeholder="Tối thiểu 50.000"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-zinc-400">dl</span>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-semibold text-black uppercase tracking-widest">Thông tin ngân hàng</label>
            <input
              type="text"
              value={bankInfo}
              onChange={(e) => setBankInfo(e.target.value)}
              className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-none"
              placeholder="VD: VCB - 123456789 - NGUYEN VAN A"
            />
          </div>

          <div className="border border-zinc-200 bg-zinc-50 p-4 space-y-2">
            <h4 className="text-[10px] font-semibold text-black uppercase tracking-widest flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" /> Quy định rút tiền
            </h4>
            <ul className="text-[10px] font-medium text-zinc-500 space-y-1 list-disc list-inside">
              <li>Tối thiểu 50.000 dl cho mỗi lần rút.</li>
              <li>Giao dịch được xử lý trong vòng 48h làm việc.</li>
              <li>Vui lòng điền chính xác thông tin để tránh sai sót.</li>
            </ul>
          </div>
        </ModalContent>

        <ModalFooter>
          <button
            onClick={() => setShowWithdrawModal(false)}
            disabled={withdrawLoading}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black disabled:opacity-50"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={withdrawLoading || !withdrawalAmount || !bankInfo}
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {withdrawLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : "Xác nhận rút"}
          </button>
        </ModalFooter>
      </Modal>

      <div
        className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6  "
        style={{ opacity: visible ? 1 : 0 }}
      >
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Ví điện tử</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Quản lý tài nguyên và lịch sử giao dịch
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowTopupModal(true)}
            className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 rounded-none border border-black  "
          >
            <Plus className="w-4 h-4" /> Nạp tiền
          </button>
          {(user?.role === "author" || user?.role === "admin") && (
            <button
              onClick={() => setShowWithdrawModal(true)}
              className="h-10 px-6 bg-white text-black text-xs font-medium flex items-center gap-2 rounded-none border border-zinc-200  "
            >
              <ArrowDownLeft className="w-4 h-4 rotate-180" /> Rút tiền
            </button>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-12  " style={{ opacity: visible ? 1 : 0 }}>
        <aside className="lg:col-span-4 space-y-6">
          <div className="border border-zinc-200 bg-white p-6 space-y-6">
            <div>
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Số dư hiện tại</p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-4xl font-bold text-black tracking-tight">{balance.toLocaleString()}</span>
                <span className="text-sm font-semibold text-black">dl</span>
              </div>
            </div>
            
            <div className="pt-4 border-t border-zinc-200 flex items-center justify-between">
               <span className="text-xs font-medium text-zinc-500">Tài khoản an toàn</span>
               <div className="w-1.5 h-1.5 bg-black rounded-none"></div>
            </div>
          </div>

          {(user?.role === "author" || user?.role === "admin") && revenue && (
            <>
              <div className="border border-zinc-200 bg-white p-6">
                <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Tổng thu nhập</p>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-bold text-black tracking-tight">{revenue.total_revenue?.toLocaleString() || 0}</span>
                  <span className="text-xs font-semibold text-black">dl</span>
                </div>
              </div>

              <div className="border border-zinc-200 bg-white p-6">
                <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">Đang chờ duyệt</p>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-bold text-black tracking-tight">{revenue.pending_withdrawal?.toLocaleString() || 0}</span>
                  <span className="text-xs font-semibold text-black">dl</span>
                </div>
              </div>
            </>
          )}

          <div className="border border-zinc-200 bg-white p-6 space-y-4">
            <div className="space-y-1 border-b border-zinc-200 pb-3">
              <h3 className="text-sm font-semibold text-black flex items-center gap-2">
                <Gift className="w-4 h-4" /> Kích hoạt Voucher
              </h3>
            </div>
            <form onSubmit={handleRedeemVoucher} className="space-y-3">
              <input
                type="text"
                value={voucherCode}
                onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                placeholder="Nhập mã"
                className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium text-center focus:outline-none focus:border-black  rounded-none"
              />
              <button
                type="submit"
                disabled={isRedeeming || !voucherCode.trim()}
                className="w-full h-10 bg-white text-black border border-zinc-200 text-xs font-medium disabled:opacity-50 rounded-none flex items-center justify-center"
              >
                {isRedeeming ? <Loader2 className="w-4 h-4 animate-spin" /> : "Xác nhận mã"}
              </button>
            </form>
          </div>
        </aside>

        <main className="lg:col-span-8">
          <div className="border border-zinc-200 bg-white p-8">
            <div className="border-b border-zinc-200 pb-4 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-black flex items-center gap-2">
                  <History className="w-4 h-4" /> Nhật ký giao dịch
                </h3>
                <p className="text-xs text-zinc-500 font-medium mt-1">
                  Lịch sử chi tiết dòng tiền
                </p>
              </div>
              <span className="text-xs font-semibold text-black">{history.length} giao dịch</span>
            </div>

            <div className="pt-4">
              {isLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-4 bg-zinc-50 border border-dashed border-zinc-200">
                  <Loader2 className="animate-spin w-6 h-6 text-zinc-400" />
                  <span className="text-xs font-medium text-zinc-500">Đang đồng bộ dữ liệu ví</span>
                </div>
              ) : history.length === 0 ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 bg-zinc-50 border border-dashed border-zinc-200">
                  <History className="w-5 h-5 text-zinc-400 mb-2" />
                  <span className="text-xs font-semibold text-black">Nhật ký trống</span>
                  <span className="text-[10px] font-medium text-zinc-500">Chưa có giao dịch nào được ghi nhận</span>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((tx) => (
                    <div
                      key={tx._id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-zinc-200 bg-zinc-50 gap-4"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 flex items-center justify-center border shrink-0 ${
                            tx.type === "TOPUP"
                              ? "border-zinc-200 bg-white text-black"
                              : "border-black bg-black text-white"
                          }`}
                        >
                          {tx.type === "TOPUP" ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-black">
                            {tx.note || (tx.type === "TOPUP" ? "Nạp tiền" : "Giao dịch")}
                          </p>
                          <p className="text-[10px] font-medium text-zinc-500 mt-1">
                            {new Date(tx.created_at).toLocaleString("vi-VN")} • TX-{tx._id.slice(-8)}
                          </p>
                        </div>
                      </div>

                      <div className="text-left sm:text-right flex flex-col sm:items-end">
                        <span
                          className={`text-sm font-bold ${
                            tx.type === "TOPUP" ? "text-black" : "text-zinc-500"
                          }`}
                        >
                          {tx.type === "TOPUP" ? "+" : "-"}{tx.amount.toLocaleString()} dl
                        </span>
                        <span className="text-[10px] font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
                          {tx.status === "COMPLETED" ? (
                            <>
                              <div className="w-1.5 h-1.5 bg-black rounded-none"></div> Hoàn tất
                            </>
                          ) : (
                            <>
                              <div className="w-1.5 h-1.5 bg-zinc-300 rounded-none"></div> {tx.status}
                            </>
                          )}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
