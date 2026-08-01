"use client";

import { useState } from "react";
import type {
  ProtectedShareResult,
  StorageItem,
} from "@/features/cloud/services/storage.service";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

export function StorageTextModal({
  open,
  close,
  title,
  label,
  processing,
  submit,
}: {
  open: boolean;
  close: () => void;
  title: string;
  label: string;
  processing: boolean;
  submit: (value: string) => Promise<boolean>;
}) {
  const [value, setValue] = useState("");
  const save = async () => {
    if (await submit(value)) {
      setValue("");
      close();
    }
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>{title}</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <label
          htmlFor="storage-text"
          className="mb-2 block text-[13px] font-semibold text-ink"
        >
          {label}
        </label>
        <input
          id="storage-text"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="apple-input w-full"
        />
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
        <Button disabled={!value.trim() || processing} onClick={save}>
          {processing ? "Đang lưu" : "Lưu"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
export function StorageShareModal({
  item,
  close,
  processing,
  submit,
  createLink,
}: {
  item: StorageItem | null;
  close: () => void;
  processing: boolean;
  submit: (email: string, role: string) => Promise<boolean>;
  createLink: (
    password: string,
    expiresInHours: number,
  ) => Promise<ProtectedShareResult>;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [password, setPassword] = useState("");
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [link, setLink] = useState("");
  const [linkError, setLinkError] = useState("");
  const [creatingLink, setCreatingLink] = useState(false);
  const save = async () => {
    if (await submit(email, role)) {
      setEmail("");
      close();
    }
  };
  const generateLink = async () => {
    setCreatingLink(true);
    setLinkError("");
    try {
      const result = await createLink(password, expiresInHours);
      setLink(`${window.location.origin}/chia-se/${result.share_token}`);
    } catch (cause) {
      setLinkError(
        cause instanceof Error ? cause.message : "Không thể tạo liên kết",
      );
    } finally {
      setCreatingLink(false);
    }
  };
  return (
    <Modal isOpen={Boolean(item)} onClose={close}>
      <ModalHeader>
        <ModalTitle>Chia sẻ {item?.name}</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="space-y-5">
          <section className="space-y-4">
            <p className="text-[13px] font-semibold text-ink">
              Cấp quyền cho tài khoản
            </p>
            <div>
              <label
                htmlFor="share-email"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Email
              </label>
              <input
                id="share-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="apple-input w-full"
              />
            </div>
            <div>
              <label
                htmlFor="share-role"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Quyền
              </label>
              <select
                id="share-role"
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="apple-input w-full"
              >
                <option value="viewer">Xem</option>
                <option value="editor">Chỉnh sửa</option>
              </select>
            </div>
            <Button disabled={!email.trim() || processing} onClick={save}>
              {processing ? "Đang chia sẻ" : "Cấp quyền"}
            </Button>
          </section>
          <section className="space-y-4 border-t border-border pt-5">
            <p className="text-[13px] font-semibold text-ink">
              Tạo liên kết bảo vệ
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="share-password"
                  className="mb-2 block text-[13px] text-ink-muted"
                >
                  Mật khẩu tùy chọn
                </label>
                <input
                  id="share-password"
                  type="password"
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="apple-input w-full"
                />
              </div>
              <div>
                <label
                  htmlFor="share-expiry"
                  className="mb-2 block text-[13px] text-ink-muted"
                >
                  Thời hạn
                </label>
                <select
                  id="share-expiry"
                  value={expiresInHours}
                  onChange={(event) =>
                    setExpiresInHours(Number(event.target.value))
                  }
                  className="apple-input w-full"
                >
                  <option value={24}>24 giờ</option>
                  <option value={72}>3 ngày</option>
                  <option value={168}>7 ngày</option>
                  <option value={720}>30 ngày</option>
                </select>
              </div>
            </div>
            {linkError && (
              <p className="text-[13px] text-danger">{linkError}</p>
            )}
            {link && (
              <div className="flex gap-2">
                <input
                  readOnly
                  value={link}
                  className="apple-input min-w-0 flex-1"
                />
                <Button
                  variant="secondary"
                  onClick={() => navigator.clipboard.writeText(link)}
                >
                  Sao chép
                </Button>
              </div>
            )}
            <Button
              variant="secondary"
              disabled={
                creatingLink || (password.length > 0 && password.length < 8)
              }
              onClick={generateLink}
            >
              {creatingLink ? "Đang tạo" : "Tạo liên kết"}
            </Button>
          </section>
        </div>
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Hủy
        </Button>
      </ModalFooter>
    </Modal>
  );
}
