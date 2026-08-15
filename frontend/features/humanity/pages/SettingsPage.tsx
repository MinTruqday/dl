"use client";

import { useState } from "react";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import PasskeySetup from "@/features/authentication/components/PasskeySetup";
import { useSettings } from "../hooks/useSettings";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";

type Tab = "general" | "notifications" | "privacy" | "author" | "account";

function ToggleRow({
  label,
  detail,
  checked,
  onChange,
}: {
  label: string;
  detail: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-6 border-b border-border py-4 last:border-b-0">
      <span>
        <span className="block font-semibold text-ink">{label}</span>
        <span className="mt-1 block text-[13px] leading-relaxed text-ink-muted">
          {detail}
        </span>
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-1 h-5 w-5 shrink-0 accent-[hsl(var(--brand))]"
      />
    </label>
  );
}

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("general");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [passkeyOpen, setPasskeyOpen] = useState(false);
  const [motivation, setMotivation] = useState("");
  const [portfolio, setPortfolio] = useState("");
  const settings = useSettings();
  useNoticeToast(settings.notice);

  if (settings.loading) return <PageLoader rows={5} />;
  if (!settings.user)
    return (
      <InlineState
        title="Cần đăng nhập"
        detail="Đăng nhập để thay đổi cài đặt"
      />
    );

  const tabs: { id: Tab; label: string }[] = [
    { id: "general", label: "Chung" },
    { id: "notifications", label: "Thông báo" },
    { id: "privacy", label: "Riêng tư" },
    ...(settings.user.role === "reader"
      ? [{ id: "author" as Tab, label: "Ứng tuyển tác giả" }]
      : []),
    { id: "account", label: "Tài khoản" },
  ];

  return (
    <div className="w-full">
      <PageHeader title="Cài đặt" />
      {settings.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể lưu cài đặt"
            detail={settings.error}
            tone="danger"
            action={
              <Button variant="secondary" onClick={settings.reload}>
                Tải lại
              </Button>
            }
          />
        </div>
      )}
      <div className="mb-6">
        <SegmentedTabs<Tab>
          label="Nhóm cài đặt"
          value={tab}
          onChange={setTab}
          tabs={tabs}
        />
      </div>

      <div className="mx-auto max-w-3xl">
        {tab === "general" && (
          <section aria-labelledby="general-settings-title">
            <h2
              id="general-settings-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Cài đặt chung
            </h2>
            <div className="rounded-panel border border-border bg-surface px-5">
              <ToggleRow
                label="Tự động lưu"
                detail="Lưu nội dung khi đang soạn thảo"
                checked={settings.general.auto_save}
                onChange={(value) =>
                  settings.setGeneral({ ...settings.general, auto_save: value })
                }
              />
              <ToggleRow
                label="Tự động làm mới"
                detail="Làm mới các danh sách dữ liệu khi quay lại ứng dụng"
                checked={settings.general.auto_refresh}
                onChange={(value) =>
                  settings.setGeneral({
                    ...settings.general,
                    auto_refresh: value,
                  })
                }
              />
              <div className="py-4">
                <label
                  htmlFor="default-visibility"
                  className="mb-2 block font-semibold text-ink"
                >
                  Quyền truy cập mặc định
                </label>
                <select
                  id="default-visibility"
                  className="apple-input w-full"
                  value={settings.general.default_visibility}
                  onChange={(event) =>
                    settings.setGeneral({
                      ...settings.general,
                      default_visibility: event.target
                        .value as typeof settings.general.default_visibility,
                    })
                  }
                >
                  <option value="public">Công khai</option>
                  <option value="private">Riêng tư</option>
                  <option value="unlisted">Không công bố</option>
                </select>
              </div>
            </div>
            <div className="mt-5 flex justify-end">
              <Button
                onClick={settings.saveGeneral}
                disabled={Boolean(settings.processing)}
              >
                {settings.processing === "general"
                  ? "Đang lưu"
                  : "Lưu thay đổi"}
              </Button>
            </div>
          </section>
        )}

        {tab === "notifications" && (
          <section aria-labelledby="notification-settings-title">
            <h2
              id="notification-settings-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Thông báo
            </h2>
            <div className="rounded-panel border border-border bg-surface px-5">
              <ToggleRow
                label="Bình luận"
                detail="Nhận thông báo khi có bình luận mới"
                checked={settings.notifications.enable_comment_notifications}
                onChange={(value) =>
                  settings.setNotifications({
                    ...settings.notifications,
                    enable_comment_notifications: value,
                  })
                }
              />
              <ToggleRow
                label="Lượt nhắc"
                detail="Nhận thông báo khi có người nhắc đến bạn"
                checked={settings.notifications.enable_mention_notifications}
                onChange={(value) =>
                  settings.setNotifications({
                    ...settings.notifications,
                    enable_mention_notifications: value,
                  })
                }
              />
              <ToggleRow
                label="Hệ thống"
                detail="Nhận thông báo vận hành và bảo mật"
                checked={settings.notifications.enable_system_notifications}
                onChange={(value) =>
                  settings.setNotifications({
                    ...settings.notifications,
                    enable_system_notifications: value,
                  })
                }
              />
              <ToggleRow
                label="Tổng hợp qua email"
                detail="Nhận bản tổng hợp thông báo qua email"
                checked={settings.notifications.enable_email_digest}
                onChange={(value) =>
                  settings.setNotifications({
                    ...settings.notifications,
                    enable_email_digest: value,
                  })
                }
              />
            </div>
            <div className="mt-5 flex justify-end">
              <Button
                onClick={settings.saveNotifications}
                disabled={Boolean(settings.processing)}
              >
                {settings.processing === "notifications"
                  ? "Đang lưu"
                  : "Lưu thay đổi"}
              </Button>
            </div>
          </section>
        )}

        {tab === "privacy" && (
          <section aria-labelledby="privacy-settings-title">
            <h2
              id="privacy-settings-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Quyền riêng tư
            </h2>
            <div className="rounded-panel border border-border bg-surface px-5">
              <ToggleRow
                label="Chế độ riêng tư"
                detail="Hạn chế hiển thị hoạt động cá nhân trên hồ sơ công khai"
                checked={settings.privacyMode}
                onChange={settings.setPrivacyMode}
              />
            </div>
            <div className="mt-5 flex justify-end">
              <Button
                onClick={settings.savePrivacy}
                disabled={Boolean(settings.processing)}
              >
                {settings.processing === "privacy"
                  ? "Đang lưu"
                  : "Lưu thay đổi"}
              </Button>
            </div>
          </section>
        )}

        {tab === "author" && (
          <section aria-labelledby="author-application-title">
            <h2
              id="author-application-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Ứng tuyển tác giả
            </h2>
            {settings.user.creator_status === "PENDING" ? (
              <InlineState
                title="Đơn ứng tuyển đang được xem xét"
                detail="Bạn sẽ nhận thông báo khi có kết quả"
              />
            ) : (
              <div className="space-y-5 rounded-panel border border-border bg-surface p-5">
                <div>
                  <label
                    htmlFor="author-motivation"
                    className="mb-2 block text-[13px] font-semibold text-ink"
                  >
                    Lý do ứng tuyển
                  </label>
                  <textarea
                    id="author-motivation"
                    className="apple-input min-h-32 w-full resize-y"
                    value={motivation}
                    onChange={(event) => setMotivation(event.target.value)}
                    minLength={20}
                    maxLength={2000}
                  />
                </div>
                <div>
                  <label
                    htmlFor="author-portfolio"
                    className="mb-2 block text-[13px] font-semibold text-ink"
                  >
                    Liên kết tác phẩm
                  </label>
                  <input
                    id="author-portfolio"
                    type="url"
                    className="apple-input w-full"
                    value={portfolio}
                    onChange={(event) => setPortfolio(event.target.value)}
                    maxLength={2048}
                  />
                </div>
                <div className="flex justify-end">
                  <Button
                    onClick={() => settings.applyAuthor(motivation, portfolio)}
                    disabled={
                      Boolean(settings.processing) ||
                      motivation.trim().length < 20
                    }
                  >
                    {settings.processing === "author" ? "Đang gửi" : "Gửi đơn"}
                  </Button>
                </div>
              </div>
            )}
          </section>
        )}

        {tab === "account" && (
          <section aria-labelledby="account-settings-title">
            <h2
              id="account-settings-title"
              className="mb-4 text-[18px] font-semibold text-ink"
            >
              Tài khoản
            </h2>
            <div className="overflow-hidden rounded-panel border border-border bg-surface">
              <div className="flex flex-col gap-4 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-ink">Passkey</p>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    Dùng sinh trắc học hoặc khóa thiết bị để đăng nhập nhanh
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => setPasskeyOpen(true)}
                  disabled={Boolean(settings.processing)}
                >
                  Thiết lập Passkey
                </Button>
              </div>
              <div className="flex flex-col gap-4 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-ink">Kết thúc mọi phiên</p>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    Đăng xuất tài khoản trên tất cả thiết bị
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={settings.logoutAll}
                  disabled={Boolean(settings.processing)}
                >
                  {settings.processing === "sessions"
                    ? "Đang xử lý"
                    : "Đăng xuất tất cả"}
                </Button>
              </div>
              <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-danger">
                    Vô hiệu hóa tài khoản
                  </p>
                  <p className="mt-1 text-[13px] text-ink-muted">
                    Tài khoản sẽ không thể đăng nhập hoặc hiển thị nội dung mới
                  </p>
                </div>
                <Button variant="danger" onClick={() => setDeleteOpen(true)}>
                  Vô hiệu hóa
                </Button>
              </div>
            </div>
          </section>
        )}
      </div>

      <Modal
        isOpen={passkeyOpen}
        onClose={() => setPasskeyOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>Thiết lập Passkey</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <PasskeySetup
            email={settings.user.email}
            onClose={() => setPasskeyOpen(false)}
            onSuccess={() => setPasskeyOpen(false)}
          />
        </ModalContent>
      </Modal>

      <Modal
        isOpen={deleteOpen}
        onClose={() => !settings.processing && setDeleteOpen(false)}
      >
        <ModalHeader>
          <ModalTitle>Vô hiệu hóa tài khoản</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[14px] leading-relaxed text-ink-muted">
            Bạn sẽ bị đăng xuất ngay sau khi tài khoản được vô hiệu hóa
          </p>
        </ModalContent>
        <ModalFooter>
          <Button
            variant="secondary"
            onClick={() => setDeleteOpen(false)}
            disabled={Boolean(settings.processing)}
          >
            Hủy
          </Button>
          <Button
            variant="danger"
            onClick={settings.deleteAccount}
            disabled={Boolean(settings.processing)}
          >
            {settings.processing === "delete" ? "Đang xử lý" : "Vô hiệu hóa"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
