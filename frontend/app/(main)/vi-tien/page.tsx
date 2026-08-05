"use client";

import { useState } from "react";
import { ArrowDownLeft, ArrowUpRight } from "lucide-react";
import InlineState from "@/app/_components/InlineState";
import MetricStrip from "@/app/_components/MetricStrip";
import PageHeader from "@/app/_components/PageHeader";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import { TopUpModal, TransferModal, WithdrawModal } from "./WalletModals";
import { useWallet, WalletTransaction } from "./useWallet";

const incomingTypes = new Set(["TOPUP", "RECEIVE", "REFUND", "TRANSFER_IN"]);
const typeLabels: Record<string, string> = {
  TOPUP: "Nạp tiền",
  PURCHASE: "Mua tài liệu",
  RECEIVE: "Nhận doanh thu",
  WITHDRAW: "Rút tiền",
  REFUND: "Hoàn tiền",
  TRANSFER_OUT: "Chuyển tiền",
  TRANSFER_IN: "Nhận chuyển tiền",
};

function TransactionRow({ transaction }: { transaction: WalletTransaction }) {
  const incoming =
    incomingTypes.has(transaction.type) || transaction.amount > 0;
  return (
    <li className="flex items-center justify-between gap-4 border-b border-border px-5 py-4 last:border-b-0">
      <div className="flex min-w-0 items-center gap-3">
        <span
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-control ${incoming ? "bg-brand-soft text-brand" : "bg-surface-quiet text-ink-muted"}`}
        >
          {incoming ? <ArrowDownLeft size={17} /> : <ArrowUpRight size={17} />}
        </span>
        <div className="min-w-0">
          <p className="truncate text-[14px] font-semibold text-ink">
            {transaction.note ||
              transaction.description ||
              typeLabels[transaction.type] ||
              "Giao dịch"}
          </p>
          <p className="mt-1 text-[12px] text-ink-muted">
            {new Date(transaction.created_at).toLocaleString("vi-VN")}
          </p>
        </div>
      </div>
      <p
        className={`shrink-0 text-[14px] font-semibold tabular-nums ${incoming ? "text-brand" : "text-ink"}`}
      >
        {incoming ? "+" : "-"}
        {Math.abs(transaction.amount).toLocaleString("vi-VN")} dl
      </p>
    </li>
  );
}

export default function WalletPage() {
  const wallet = useWallet();
  const [topUpOpen, setTopUpOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [transferOpen, setTransferOpen] = useState(false);

  if (wallet.authLoading || wallet.loading) return <PageLoader rows={6} />;
  if (!wallet.user)
    return (
      <InlineState title="Cần đăng nhập" detail="Đăng nhập để sử dụng ví" />
    );

  const canWithdraw =
    wallet.user.role === "author" || wallet.user.role === "admin";
  return (
    <div className="w-full">
      <PageHeader
        title="Ví tiền"
        actions={
          <>
            <Button variant="secondary" onClick={() => setTransferOpen(true)}>
              Chuyển tiền
            </Button>
            {canWithdraw && (
              <Button variant="secondary" onClick={() => setWithdrawOpen(true)}>
                Rút tiền
              </Button>
            )}
            <Button onClick={() => setTopUpOpen(true)}>Nạp tiền</Button>
          </>
        }
      />
      {wallet.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể hoàn tất thao tác"
            detail={wallet.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={wallet.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      {wallet.notice && (
        <div className="mb-6">
          <InlineState
            title={wallet.notice}
            action={
              <Button variant="ghost" onClick={wallet.clearNotice}>
                Đóng
              </Button>
            }
          />
        </div>
      )}
      <MetricStrip
        items={[
          {
            label: "Số dư",
            value: `${wallet.balance.toLocaleString("vi-VN")} dl`,
            detail: `${(wallet.balance * 1000).toLocaleString("vi-VN")} VNĐ`,
          },
          {
            label: "Có thể rút",
            value: `${wallet.withdrawable.toLocaleString("vi-VN")} dl`,
          },
          { label: "Giao dịch", value: wallet.history.length },
        ]}
      />
      <section className="mt-8">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[17px] font-semibold text-ink">
            Lịch sử giao dịch
          </h2>
          <span className="text-[12px] text-ink-muted">Mới nhất trước</span>
        </div>
        {wallet.history.length ? (
          <ul className="overflow-hidden rounded-panel border border-border bg-surface">
            {wallet.history.map((transaction) => (
              <TransactionRow key={transaction._id} transaction={transaction} />
            ))}
          </ul>
        ) : (
          <InlineState
            title="Chưa có giao dịch"
            detail="Các khoản nạp, rút, mua và chuyển tiền sẽ xuất hiện tại đây"
          />
        )}
      </section>
      <TopUpModal
        open={topUpOpen}
        close={() => setTopUpOpen(false)}
        processing={wallet.processing}
        submit={wallet.topUp}
      />
      <WithdrawModal
        open={withdrawOpen}
        close={() => setWithdrawOpen(false)}
        processing={wallet.processing}
        maximum={wallet.withdrawable}
        submit={wallet.withdraw}
      />
      <TransferModal
        open={transferOpen}
        close={() => setTransferOpen(false)}
        processing={wallet.processing}
        balance={wallet.balance}
        recipient={wallet.recipient}
        verify={wallet.verifyRecipient}
        submit={wallet.transfer}
      />
    </div>
  );
}
