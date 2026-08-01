"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { createDepositLinkAPI } from "@/features/payment/services/deposit.service";
import { requestWithdrawalAPI } from "@/features/payment/services/withdrawal.service";
import {
  getWalletBalanceAPI,
  getWalletHistoryAPI,
  transferFundsAPI,
  TransferRecipient,
  verifyTransferRecipientAPI,
} from "@/features/payment/services/wallet.service";

export type WalletTransaction = {
  _id: string;
  amount: number;
  type: string;
  status: string;
  note?: string;
  description?: string;
  created_at: string;
};

export function useWallet() {
  const { user, isLoading: authLoading } = useAuth();
  const [balance, setBalance] = useState(0);
  const [withdrawable, setWithdrawable] = useState(0);
  const [history, setHistory] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [recipient, setRecipient] = useState<TransferRecipient | null>(null);

  const reload = useCallback(async () => {
    if (!user) return setLoading(false);
    setLoading(true);
    setError("");
    try {
      const [balanceResponse, historyResponse] = await Promise.all([
        getWalletBalanceAPI(),
        getWalletHistoryAPI(),
      ]);
      const wallet = balanceResponse.data ?? balanceResponse;
      const rows = historyResponse.data ?? historyResponse;
      setBalance(Number(wallet.balance ?? 0));
      setWithdrawable(Number(wallet.withdrawable_balance ?? 0));
      setHistory(Array.isArray(rows) ? rows : []);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải dữ liệu ví",
      );
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => void reload(), [reload]);

  const topUp = async (amount: number) => {
    setProcessing("topup");
    setError("");
    try {
      const response = await createDepositLinkAPI(amount);
      const url = response.data?.checkout_url ?? response.checkout_url;
      if (!url) throw new Error("Cổng thanh toán không trả về liên kết hợp lệ");
      window.location.assign(url);
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tạo giao dịch nạp tiền",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };

  const withdraw = async (input: {
    amount: number;
    bankName: string;
    accountNumber: string;
    accountName: string;
  }) => {
    setProcessing("withdraw");
    setError("");
    try {
      await requestWithdrawalAPI(input.amount, {
        bank_name: input.bankName.trim(),
        account_number: input.accountNumber.trim(),
        account_name: input.accountName.trim(),
      });
      setNotice("Yêu cầu rút tiền đã được ghi nhận");
      await reload();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tạo yêu cầu rút tiền",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };

  const verifyRecipient = async (identifier: string) => {
    setProcessing("verify");
    setError("");
    setRecipient(null);
    try {
      const response = await verifyTransferRecipientAPI(identifier.trim());
      setRecipient(response.data);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không tìm thấy người nhận",
      );
    } finally {
      setProcessing(null);
    }
  };

  const transfer = async (identifier: string, amount: number, note: string) => {
    setProcessing("transfer");
    setError("");
    try {
      await transferFundsAPI({
        recipient_identifier: identifier.trim(),
        amount,
        note: note.trim(),
        idempotency_key: crypto.randomUUID(),
      });
      setNotice("Chuyển tiền thành công");
      setRecipient(null);
      await reload();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể chuyển tiền",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };

  return {
    user,
    authLoading,
    balance,
    withdrawable,
    history,
    loading,
    processing,
    error,
    notice,
    recipient,
    reload,
    topUp,
    withdraw,
    verifyRecipient,
    transfer,
    clearNotice: () => setNotice(""),
  };
}
