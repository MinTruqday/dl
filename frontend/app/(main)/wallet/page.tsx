"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import {
  ArrowUpRight,
  ArrowDownLeft,
  Loader2,
  AlertCircle,
  Info,
  Wallet,
  Ticket,
  History,
} from "lucide-react";
import {
  getWalletBalanceAPI,
  getWalletHistoryAPI,
  redeemVoucherAPI,
} from "@/features/finance/services/account_ledger.service";
import { createDepositLinkAPI } from "@/features/finance/services/fiat_deposit.service";
import { requestWithdrawalAPI } from "@/features/finance/services/fiat_withdrawal.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
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
    RETURN_URL: window.location.origin + "/wallet",
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
      className="w-full min-h-[450px] border border-zinc-100 rounded-2xl overflow-hidden shadow-sm"
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
        setRevenue({});
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
          "success",
        );
        setVoucherCode("");
        fetchWalletData();
      }
    } catch (error: any) {
      showToast(
        error.message || "Voucher không hợp lệ hoặc đã hết hạn",
        "error",
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
      const url =
        res.data?.checkout_url || res.data?.payment_url || res.checkout_url;
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
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-6 font-sans bg-zinc-50 px-6 text-center">
        <div className="w-20 h-20 bg-white shadow-sm flex items-center justify-center border border-zinc-100 rounded-3xl">
          <AlertCircle className="w-8 h-8 text-zinc-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-zinc-900">
            Truy cập bị hạn chế
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            Vui lòng đăng nhập để quản lý tài chính cá nhân
          </p>
        </div>
        <button
          onClick={() => (window.location.href = "/dang-nhap")}
          className="bg-black text-white h-11 px-8 text-xs font-bold flex items-center justify-center rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
        >
          Đăng nhập ngay
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-zinc-900 bg-zinc-50 selection:bg-black selection:text-white">
      <Modal
        isOpen={showTopupModal}
        onClose={() => {
          setShowTopupModal(false);
          setCheckoutUrl(null);
        }}
        className={`rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden ${checkoutUrl ? "max-w-2xl" : "max-w-md"}`}
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">
            {checkoutUrl ? "Thanh toán giao dịch" : "Nạp tiền (VNĐ)"}
          </ModalTitle>
          {!checkoutUrl && (
            <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
              Chọn mệnh giá hoặc nhập số tiền cần nạp
            </ModalDescription>
          )}
        </ModalHeader>

        <ModalContent className="p-6">
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
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-3">
                {[50000, 100000, 200000, 500000].map((amt) => (
                  <button
                    key={amt}
                    onClick={() => setTopupAmount(amt)}
                    className={`py-3 text-[10px] font-bold uppercase tracking-widest border rounded-2xl transition-all duration-200 ${
                      topupAmount === amt
                        ? "bg-black border-black text-white shadow-md hover:scale-[1.02]"
                        : "bg-white border-zinc-200 text-zinc-500 hover:bg-zinc-50"
                    }`}
                  >
                    {amt.toLocaleString()} VNĐ
                  </button>
                ))}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                  Số tiền khác
                </label>
                <div className="relative">
                  <input
                    type="number"
                    value={topupAmount}
                    onChange={(e) =>
                      setTopupAmount(parseInt(e.target.value) || 0)
                    }
                    className="w-full h-11 bg-white border border-zinc-200 px-4 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
                  />
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                    VNĐ
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between py-4 border-t border-zinc-100">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                  Tỷ giá quy đổi
                </span>
                <span className="text-xs font-bold text-zinc-900 bg-zinc-100 px-3 py-1.5 rounded-xl">
                  1.000 VNĐ = 1 dl
                </span>
              </div>
            </div>
          )}
        </ModalContent>

        {!checkoutUrl && (
          <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
            <button
              onClick={() => setShowTopupModal(false)}
              disabled={topupLoading}
              className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm"
            >
              Hủy bỏ
            </button>
            <button
              onClick={handleTopup}
              disabled={topupLoading || topupAmount < 10000}
              className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
            >
              {topupLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Xác nhận nạp"
              )}
            </button>
          </ModalFooter>
        )}
      </Modal>

      <Modal
        isOpen={showWithdrawModal}
        onClose={() => setShowWithdrawModal(false)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md shadow-xl p-0 overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight">Rút tiền (dl)</ModalTitle>
          <ModalDescription className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1">
            Tỷ lệ quy đổi: 1 dl = 1.000 VNĐ (Phí hệ thống 2%)
          </ModalDescription>
        </ModalHeader>

        <ModalContent className="p-6 space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
              Số tiền rút (dl)
            </label>
            <div className="relative">
              <input
                type="number"
                value={withdrawalAmount}
                onChange={(e) => setWithdrawalAmount(e.target.value)}
                className="w-full h-11 bg-white border border-zinc-200 px-4 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
                placeholder="Tối thiểu 50.000"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                dl
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
              Thông tin ngân hàng
            </label>
            <input
              type="text"
              value={bankInfo}
              onChange={(e) => setBankInfo(e.target.value)}
              className="w-full h-11 bg-white border border-zinc-200 px-4 text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
              placeholder="VD: VCB - 123456789 - NGUYEN VAN A"
            />
          </div>

          <div className="border border-zinc-100 bg-zinc-50 p-5 space-y-3 rounded-2xl shadow-sm">
            <h4 className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest flex items-center gap-2">
              <Info className="w-4 h-4 text-zinc-400" /> Quy định rút tiền
            </h4>
            <ul className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest space-y-2 list-disc list-inside ml-1">
              <li>Tối thiểu 50.000 dl cho mỗi lần rút.</li>
              <li>Giao dịch được xử lý trong 48h làm việc.</li>
              <li>Vui lòng điền chính xác thông tin.</li>
            </ul>
          </div>
        </ModalContent>

        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setShowWithdrawModal(false)}
            disabled={withdrawLoading}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold text-black uppercase tracking-widest disabled:opacity-50 rounded-2xl transition-all duration-200 hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={handleWithdrawal}
            disabled={withdrawLoading || !withdrawalAmount || !bankInfo}
            className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
          >
            {withdrawLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Xác nhận rút"
            )}
          </button>
        </ModalFooter>
      </Modal>

      <div className="grid lg:grid-cols-12 gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <aside className="lg:col-span-4 xl:col-span-3 space-y-6">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 space-y-6 rounded-3xl shadow-sm text-center">
            <div className="w-16 h-16 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mx-auto mb-2">
              <Wallet className="w-8 h-8 text-black" />
            </div>
            
            <div className="space-y-1">
              <h2 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Số dư khả dụng
              </h2>
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-4xl md:text-5xl font-bold tracking-tight text-zinc-900">
                  {balance.toLocaleString()}
                </span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">dl</span>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-4 border-t border-zinc-50">
              <button
                onClick={() => setShowTopupModal(true)}
                className="w-full h-11 bg-black text-white text-xs font-bold flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
              >
                Nạp tiền vào ví
              </button>
              {(user?.role === "author" || user?.role === "admin") && (
                <button
                  onClick={() => setShowWithdrawModal(true)}
                  className="w-full h-11 bg-white text-zinc-900 border border-zinc-200 text-xs font-bold flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] shadow-sm"
                >
                  Rút thu nhập
                </button>
              )}
            </div>
          </div>

          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 space-y-6 rounded-3xl shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-zinc-50 border border-zinc-100 rounded-2xl flex items-center justify-center shrink-0 shadow-sm">
                <Ticket className="w-5 h-5 text-black" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-900 tracking-tight">
                  Kích hoạt Voucher
                </h3>
                <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">
                  Nhập mã để nhận thưởng
                </p>
              </div>
            </div>
            
            <form onSubmit={handleRedeemVoucher} className="space-y-4">
              <input
                type="text"
                value={voucherCode}
                onChange={(e) => setVoucherCode(e.target.value.toUpperCase())}
                placeholder="Nhập mã voucher"
                className="w-full h-11 bg-white border border-zinc-200 px-4 text-xs font-bold text-center uppercase tracking-widest focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
              />
              <button
                type="submit"
                disabled={isRedeeming || !voucherCode.trim()}
                className="w-full h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 rounded-2xl flex items-center justify-center transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
              >
                {isRedeeming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Xác nhận mã"
                )}
              </button>
            </form>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-9 space-y-6">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8 min-h-[500px]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-100 pb-6">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Nhật ký giao dịch
                </h2>
                <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                  Theo dõi hoạt động tài chính cá nhân
                </p>
              </div>
              <span className="px-3 py-1.5 bg-zinc-100 text-zinc-900 text-[10px] font-bold uppercase tracking-widest rounded-xl">
                {history.length} giao dịch
              </span>
            </div>

            <div className="flex-1">
              {isLoading ? (
                <div className="py-24 flex flex-col items-center justify-center bg-zinc-50 border border-zinc-100 rounded-3xl">
                  <Loader2 className="animate-spin w-8 h-8 text-zinc-300 mb-4" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Đang đồng bộ dữ liệu...
                  </p>
                </div>
              ) : history.length === 0 ? (
                <div className="py-24 flex flex-col items-center justify-center bg-zinc-50 border border-zinc-100 rounded-3xl">
                  <History className="w-12 h-12 text-zinc-200 mb-4" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Chưa có phát sinh giao dịch
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((tx) => (
                    <div
                      key={tx._id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-white rounded-3xl gap-4 shadow-sm hover:border-zinc-200 hover:shadow-md transition-all duration-300 group"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-12 h-12 flex items-center justify-center border shrink-0 rounded-2xl shadow-sm transition-transform duration-300 group-hover:scale-110 ${
                            tx.type === "TOPUP"
                              ? "border-zinc-100 bg-zinc-50 text-black"
                              : "border-black bg-black text-white"
                          }`}
                        >
                          {tx.type === "TOPUP" ? (
                            <ArrowDownLeft className="w-5 h-5" />
                          ) : (
                            <ArrowUpRight className="w-5 h-5" />
                          )}
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-bold text-zinc-900 tracking-tight">
                            {tx.note ||
                              (tx.type === "TOPUP" ? "Nạp tiền" : "Giao dịch")}
                          </p>
                          <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-1.5">
                            {new Date(tx.created_at).toLocaleString("vi-VN")} <span className="text-zinc-200">•</span> TX-{tx._id.slice(-8)}
                          </p>
                        </div>
                      </div>

                      <div className="text-left sm:text-right flex flex-col sm:items-end justify-center space-y-1.5 bg-zinc-50 p-3 rounded-2xl sm:bg-transparent sm:p-0">
                        <span
                          className={`text-sm font-bold tracking-tight ${
                            tx.type === "TOPUP" ? "text-green-600" : "text-zinc-500"
                          }`}
                        >
                          {tx.type === "TOPUP" ? "+" : "-"}
                          {tx.amount.toLocaleString()} dl
                        </span>
                        <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500 flex items-center gap-1.5">
                          {tx.status === "COMPLETED" ? (
                            <>
                              <div className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>{" "}
                              Hoàn tất
                            </>
                          ) : (
                            <>
                              <div className="w-1.5 h-1.5 bg-zinc-300 rounded-full"></div>{" "}
                              {tx.status}
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
