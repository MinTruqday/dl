"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { requestWithdrawalAPI } from "@/features/payment/services/withdrawal.service";
import { getWalletBalanceAPI } from "@/features/payment/services/wallet.service";
import { useToast } from "@/shared/contexts/ToastContext";
import PageLoader from "@/shared/components/common/PageLoader";
import { Loader2, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function WithdrawPage() {
  const { isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();

  const [balance, setBalance] = useState<number>(0);
  const [initialLoading, setInitialLoading] = useState(true);

  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [bankName, setBankName] = useState("");
  const [bankAccount, setBankAccount] = useState("");
  const [accountHolder, setAccountHolder] = useState("");
  const [withdrawLoading, setWithdrawLoading] = useState(false);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const res = await getWalletBalanceAPI();
        setBalance(res.data?.balance ?? res.balance ?? 0);
      } catch (error) {
        showToast("Không thể lấy số dư ví", "error");
      } finally {
        setInitialLoading(false);
      }
    };
    if (!authLoading) fetchBalance();
  }, [authLoading, showToast]);

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
      router.push("/vi-tien/tong-quan");
    } catch (e: any) {
      showToast(e.message || "Lỗi thực thi giao dịch rút tiền", "error");
    } finally {
      setWithdrawLoading(false);
    }
  };

  if (authLoading || initialLoading) return <PageLoader />;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
          Rút tiền
        </h2>
      </div>
      <div className="bg-white rounded-[18px] p-6">
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-[#F5F5F7] p-4 rounded-[12px]">
            <span className="text-[14px] font-medium text-[#6E6E73]">Số dư khả dụng</span>
            <span className="text-[17px] font-semibold text-[#1D1D1F]">{balance.toLocaleString()} dl</span>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73]">
                Số dl cần rút
              </label>
              <input
                type="number"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                className="w-full h-12 px-4 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] rounded-[12px] outline-none text-[#1D1D1F] text-[15px] transition-all duration-200"
                placeholder="Tối thiểu 50 dl"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73]">
                Tên ngân hàng
              </label>
              <input
                type="text"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                className="w-full h-12 px-4 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] rounded-[12px] outline-none text-[#1D1D1F] text-[15px] transition-all duration-200"
                placeholder="Ví dụ: Vietcombank, TPBank..."
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73]">
                Số tài khoản
              </label>
              <input
                type="text"
                value={bankAccount}
                onChange={(e) => setBankAccount(e.target.value)}
                className="w-full h-12 px-4 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] rounded-[12px] outline-none text-[#1D1D1F] text-[15px] transition-all duration-200"
                placeholder="Số tài khoản ngân hàng"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-[#6E6E73]">
                Tên chủ tài khoản
              </label>
              <input
                type="text"
                value={accountHolder}
                onChange={(e) => setAccountHolder(e.target.value)}
                className="w-full h-12 px-4 bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] rounded-[12px] outline-none text-[#1D1D1F] text-[15px] transition-all duration-200 uppercase"
                placeholder="Tên in trên thẻ"
              />
            </div>
          </div>

          <div className="bg-[#FFF0F0] p-4 rounded-[12px] flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#FF3B30] shrink-0 mt-0.5" />
            <div className="text-[13px] text-[#FF3B30] leading-relaxed">
              <p>Giao dịch rút tiền sẽ được xử lý thủ công trong vòng 24-48 giờ.</p>
              <p>Tỷ lệ quy đổi: 1 dl = 1 VNĐ.</p>
            </div>
          </div>

          <button
            onClick={handleWithdrawal}
            disabled={withdrawLoading}
            className="w-full py-3.5 bg-[#0071E3] hover:bg-[#0055C6] text-white rounded-[12px] font-medium text-[15px] transition-all duration-200 flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {withdrawLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Đang xử lý...
              </>
            ) : (
              "Gửi yêu cầu"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
