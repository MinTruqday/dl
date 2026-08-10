"use client";

import { useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import type { TransferRecipient } from "@/features/finance/services/wallet.service";

type Shared = { open: boolean; close: () => void; processing: string | null };

export function TopUpModal({
  open,
  close,
  processing,
  submit,
}: Shared & { submit: (amount: number) => Promise<boolean> }) {
  const [amount, setAmount] = useState(50000);
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Nạp tiền</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="topup-amount"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          Số tiền
        </label>
        <input
          id="topup-amount"
          type="number"
          min={10000}
          step={10000}
          value={amount}
          onChange={(event) => setAmount(Number(event.target.value))}
          className="apple-input w-full"
        />
        <p className="mt-2 text-[12px] text-ink-muted">
          Tối thiểu 10.000 VNĐ, quy đổi 1.000 VNĐ thành 1 dl
        </p>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button
          disabled={processing === "topup" || amount < 10000}
          onClick={() => submit(amount)}
        >
          {processing === "topup" ? "Đang chuyển hướng" : "Tiếp tục"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function WithdrawModal({
  open,
  close,
  processing,
  maximum,
  submit,
}: Shared & {
  maximum: number;
  submit: (input: {
    amount: number;
    bankName: string;
    accountNumber: string;
    accountName: string;
  }) => Promise<boolean>;
}) {
  const [amount, setAmount] = useState(50);
  const [bankName, setBankName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");
  const valid =
    amount >= 50 &&
    amount <= maximum &&
    bankName.trim().length >= 2 &&
    /^[A-Za-z0-9]{6,34}$/.test(accountNumber.trim()) &&
    accountName.trim().length >= 2;
  const handleSubmit = async () => {
    if (await submit({ amount, bankName, accountNumber, accountName })) close();
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Rút tiền</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="withdraw-amount"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Số dl
            </label>
            <input
              id="withdraw-amount"
              type="number"
              min={50}
              max={maximum}
              value={amount}
              onChange={(event) => setAmount(Number(event.target.value))}
              className="apple-input w-full"
            />
            <p className="mt-2 text-[12px] text-ink-muted">
              Số dư có thể rút {maximum.toLocaleString("vi-VN")} dl. Phí tăng
              theo số lượt rút trong tuần
            </p>
          </div>
          <div>
            <label
              htmlFor="bank-name"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Ngân hàng
            </label>
            <input
              id="bank-name"
              value={bankName}
              onChange={(event) => setBankName(event.target.value)}
              className="apple-input w-full"
            />
          </div>
          <div>
            <label
              htmlFor="bank-account"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Số tài khoản
            </label>
            <input
              id="bank-account"
              value={accountNumber}
              onChange={(event) => setAccountNumber(event.target.value)}
              className="apple-input w-full"
            />
          </div>
          <div>
            <label
              htmlFor="account-name"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Chủ tài khoản
            </label>
            <input
              id="account-name"
              value={accountName}
              onChange={(event) => setAccountName(event.target.value)}
              className="apple-input w-full"
            />
          </div>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button
          disabled={processing === "withdraw" || !valid}
          onClick={handleSubmit}
        >
          {processing === "withdraw" ? "Đang gửi" : "Gửi yêu cầu"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export function TransferModal({
  open,
  close,
  processing,
  balance,
  recipient,
  verify,
  submit,
}: Shared & {
  balance: number;
  recipient: TransferRecipient | null;
  verify: (identifier: string) => Promise<void>;
  submit: (
    identifier: string,
    amount: number,
    note: string,
  ) => Promise<boolean>;
}) {
  const [identifier, setIdentifier] = useState("");
  const [amount, setAmount] = useState(1);
  const [note, setNote] = useState("");
  const handleSubmit = async () => {
    if (await submit(identifier, amount, note)) close();
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Chuyển tiền</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="recipient"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Email, tên tài khoản hoặc mã tài khoản
            </label>
            <div className="flex gap-2">
              <input
                id="recipient"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                className="apple-input min-w-0 flex-1"
              />
              <Button
                variant="secondary"
                disabled={!identifier.trim() || processing === "verify"}
                onClick={() => verify(identifier)}
              >
                {processing === "verify" ? "Đang tìm" : "Kiểm tra"}
              </Button>
            </div>
          </div>
          {recipient && (
            <div className="rounded-control border border-border bg-surface-quiet p-4">
              <p className="font-semibold text-ink">{recipient.full_name}</p>
              <p className="mt-1 text-[12px] text-ink-muted">
                {recipient.email || recipient.account_number}
              </p>
            </div>
          )}
          <div>
            <label
              htmlFor="transfer-amount"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Số dl
            </label>
            <input
              id="transfer-amount"
              type="number"
              min={1}
              max={balance}
              value={amount}
              onChange={(event) => setAmount(Number(event.target.value))}
              className="apple-input w-full"
            />
          </div>
          <div>
            <label
              htmlFor="transfer-note"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Nội dung
            </label>
            <input
              id="transfer-note"
              maxLength={500}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              className="apple-input w-full"
            />
          </div>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button
          disabled={
            !recipient ||
            amount < 1 ||
            amount > balance ||
            processing === "transfer"
          }
          onClick={handleSubmit}
        >
          {processing === "transfer" ? "Đang chuyển" : "Chuyển tiền"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
