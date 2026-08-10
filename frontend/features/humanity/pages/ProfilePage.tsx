"use client";

import Link from "next/link";
import PageLoader from "@/shared/components/common/PageLoader";
import { Button } from "@/shared/components/ui/Button";
import InlineState from "@/shared/components/common/InlineState";
import PageHeader from "@/shared/components/layout/PageHeader";
import { useProfile } from "../hooks/useProfile";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";

const roleLabels: Record<string, string> = {
  reader: "Độc giả",
  author: "Tác giả",
  admin: "Quản trị viên",
};

export default function ProfilePage() {
  const profile = useProfile();
  useNoticeToast(profile.notice);

  if (profile.loading) return <PageLoader rows={3} />;
  if (!profile.user)
    return (
      <InlineState
        title="Cần đăng nhập"
        detail="Đăng nhập để xem hồ sơ"
        action={
          <Link href="/dang-nhap" className="secondary-button">
            Đăng nhập
          </Link>
        }
      />
    );

  const initials = String(profile.user.full_name || profile.user.email || "D")
    .trim()
    .charAt(0)
    .toUpperCase();

  return (
    <div className="w-full">
      <PageHeader
        title="Hồ sơ"
        actions={
          <Button variant="ghost" onClick={profile.logout}>
            Đăng xuất
          </Button>
        }
      />
      {profile.error && (
        <div className="mb-6">
          <InlineState
            title="Không thể cập nhật hồ sơ"
            detail={profile.error}
            tone="danger"
          />
        </div>
      )}
      <div className="grid gap-8 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <aside>
          <div className="rounded-panel border border-border bg-surface p-5">
            <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full bg-brand text-[34px] font-semibold text-white">
              {profile.avatarUrl ? (
                <img
                  src={profile.avatarUrl}
                  alt=""
                  className="h-full w-full object-cover"
                />
              ) : (
                initials
              )}
            </div>
            <p className="mt-5 truncate text-[17px] font-semibold text-ink">
              {profile.user.full_name || "Chưa có tên"}
            </p>
            <p className="mt-1 truncate text-[13px] text-ink-muted">
              @{profile.user.slug || "chua-co-ten"}
            </p>
            <p className="mt-3 text-[13px] font-semibold text-brand">
              {roleLabels[
                String(profile.user.role || "reader").toLowerCase()
              ] || profile.user.role}
            </p>
            <label className="secondary-button mt-5 w-full cursor-pointer">
              {profile.processing === "avatar" ? "Đang tải" : "Đổi ảnh"}
              <input
                type="file"
                className="sr-only"
                accept="image/*"
                disabled={Boolean(profile.processing)}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) profile.uploadAvatar(file);
                }}
              />
            </label>
          </div>
        </aside>

        <section aria-labelledby="profile-form-title">
          <h2
            id="profile-form-title"
            className="mb-4 text-[18px] font-semibold text-ink"
          >
            Thông tin cá nhân
          </h2>
          <div className="space-y-5 rounded-workspace border border-border bg-surface p-5 md:p-7">
            <div>
              <label
                htmlFor="profile-email"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Email
              </label>
              <input
                id="profile-email"
                className="apple-input w-full"
                value={profile.user.email || ""}
                readOnly
                disabled
              />
            </div>
            <div>
              <label
                htmlFor="profile-name"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Tên hiển thị
              </label>
              <input
                id="profile-name"
                className="apple-input w-full"
                value={profile.fullName}
                onChange={(event) => profile.setFullName(event.target.value)}
                maxLength={100}
              />
            </div>
            <div>
              <label
                htmlFor="profile-bio"
                className="mb-2 block text-[13px] font-semibold text-ink"
              >
                Giới thiệu
              </label>
              <textarea
                id="profile-bio"
                className="apple-input min-h-28 w-full resize-y"
                value={profile.bio}
                onChange={(event) => profile.setBio(event.target.value)}
                maxLength={800}
              />
            </div>
            <div className="flex flex-wrap justify-between gap-3 border-t border-border pt-5">
              <Link href="/cai-dat" className="secondary-button">
                Cài đặt tài khoản
              </Link>
              <Button
                onClick={profile.save}
                disabled={
                  Boolean(profile.processing) || !profile.fullName.trim()
                }
              >
                {profile.processing === "save" ? "Đang lưu" : "Lưu thay đổi"}
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
