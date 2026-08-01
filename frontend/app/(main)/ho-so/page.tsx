"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { API_URL } from "@/features/authentication/services/session.service";
import { updateProfileAPI } from "@/features/management/services/setting.service";
import { uploadAssetAPI } from "@/features/cloud/services/upload.service";
import {
  User,
  Camera,
  LogOut,
  Loader2,
  BadgeCheck,
  ShieldCheck,
  Crown,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";

export default function ProfilePage() {
  const { user, isLoading, logoutState } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [visible, setVisible] = useState(false);
  const [motivation, setMotivation] = useState("");
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/dang-nhap");
    } else if (user) {
      setFullName(user.full_name || "");
      setBio(user.bio || "");
      setAvatarUrl(user.avatar_url || "");
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (!isLoading && user) {
      requestAnimationFrame(() => setVisible(true));
    }
  }, [isLoading, user]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await updateProfileAPI({
        full_name: fullName,
        bio,
        avatar_url: avatarUrl,
      });
      if (res && (res.status === 200 || res.id)) {
        showToast("Cập nhật thông tin hồ sơ hoàn tất", "success");
      } else {
        showToast("Không thể cập nhật thông tin hồ sơ", "error");
      }
    } catch (err: any) {
      showToast("Lỗi gián đoạn hệ thống", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) return showToast("Lỗi thiếu hụt nội dung giải trình", "error");
    setIsApplying(true);
    try {
      showToast("Khởi tạo yêu cầu cấp quyền hoàn tất", "success");
      setMotivation("");
    } catch (e: any) {
      showToast("Không thể tạo yêu cầu cấp quyền", "error");
    } finally {
      setIsApplying(false);
    }
  };

  const handleBecomeAuthor = async () => {
    setIsSaving(true);
    try {
      showToast("Cập nhật phân quyền tác giả hoàn tất", "success");
      window.location.reload();
    } catch (e: any) {
      showToast("Không thể cập nhật phân quyền tác giả", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsSaving(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const res = await uploadAssetAPI(e.target.files[0], "image");
      if (res.data?.url) {
        setAvatarUrl(
          res.data.url.startsWith("http")
            ? res.data.url
            : `${API_URL}/tai-len/luu-tru/${res.data.url}`,
        );
        showToast("Lưu trữ tệp đa phương tiện hoàn tất", "success");
      }
    } catch (err: any) {
      showToast("Không thể truyền tệp đa phương tiện", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-ink-muted" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full h-full flex flex-col font-sans text-ink">
      <div
        className={`grid md:grid-cols-12 gap-8 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <aside className="md:col-span-4 xl:col-span-4 space-y-6">
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 flex flex-col items-center text-center">
            <div className="relative group mb-6">
              <div className="w-32 h-32 rounded-full bg-border flex items-center justify-center overflow-hidden transition-transform duration-300 group-hover:scale-105">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-brand text-white flex items-center justify-center text-[56px] font-semibold uppercase">
                    {(user.full_name || user.username || "U").charAt(0)}
                  </div>
                )}
              </div>
              <label className="absolute inset-0 bg-[rgba(0,0,0,0.5)] opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center text-white cursor-pointer rounded-full transition-all duration-300">
                <Camera className="w-6 h-6 mb-1" />
                <span className="text-[12px] font-medium">Đổi ảnh</span>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                />
              </label>
            </div>

            <div className="w-full mb-8">
              <div className="flex items-center justify-center gap-2 mb-1">
                <h1 className="text-[20px] font-semibold text-ink truncate px-2">
                  {user.full_name || "Ẩn danh"}
                </h1>
                {user.role === "admin" && (
                  <ShieldCheck className="w-5 h-5 text-ink-muted" />
                )}
                {user.role === "author" && (
                  <BadgeCheck className="w-5 h-5 text-brand" />
                )}
                {user.role === "potential_author" && (
                  <Crown className="w-5 h-5 text-warning" />
                )}
              </div>
              <p className="text-[14px] text-ink-muted">
                @{user.slug || "nguoidung"}
              </p>

              <div className="mt-4 flex justify-center">
                <span
                  className={`px-3 py-1 text-[13px] font-medium rounded-full ${
                    user.role === "admin"
                      ? "bg-border text-ink"
                      : user.role === "author"
                        ? "bg-brand-soft text-brand"
                        : user.role === "potential_author"
                          ? "bg-warning-soft text-warning"
                          : "bg-border text-ink"
                  }`}
                >
                  {user.role === "admin"
                    ? "Quản trị viên"
                    : user.role === "author"
                      ? "Tác giả"
                      : user.role === "potential_author"
                        ? "Tác giả tiềm năng"
                        : "Độc giả"}
                </span>
              </div>
            </div>

            <button
              onClick={logoutState}
              className="w-full py-3 bg-white text-danger text-[15px] font-medium flex items-center justify-center gap-2 rounded-full transition-colors hover:bg-surface-quiet"
            >
              <LogOut className="w-4 h-4" /> Đăng xuất
            </button>
          </div>
        </aside>

        <main className="md:col-span-8 xl:col-span-8 space-y-6">
          <div className="bg-surface-quiet md:bg-transparent rounded-panel md:rounded-none p-6 md:p-0 md:pt-6 space-y-6">
            <h2 className="text-[20px] font-semibold text-ink mb-6">
              Thông tin cá nhân
            </h2>

            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-ink-muted ml-1 block">
                  Địa chỉ Email
                </label>
                <div className="apple-input w-full h-[48px] bg-border border-transparent px-4 flex items-center text-ink-muted text-[15px] cursor-not-allowed">
                  {user.email}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-ink-muted ml-1 block">
                  Tên hiển thị
                </label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="apple-input w-full h-[48px]"
                  placeholder=""
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[13px] font-medium text-ink-muted ml-1 block">
                Tiểu sử
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder=""
                className="apple-input w-full min-h-[100px] resize-none py-3"
              />
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="pill-button"
              >
                {isSaving ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  "Lưu thay đổi"
                )}
              </button>
            </div>
          </div>

          {user.role === "reader" && (
            <div className="bg-brand-soft rounded-panel p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-[17px] font-medium text-brand flex items-center gap-2 mb-2">
                  <BadgeCheck className="w-5 h-5" /> Trở thành Tác giả
                </h3>
                <p className="text-[14px] text-brand-hover">
                  Nâng cấp tài khoản để xuất bản nội dung và xây dựng cộng đồng của riêng bạn
                </p>
              </div>
              <button
                onClick={handleBecomeAuthor}
                disabled={isSaving}
                className="pill-button shrink-0 bg-brand hover:bg-brand-hover"
              >
                {isSaving ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  "Nâng cấp"
                )}
              </button>
            </div>
          )}

          {user.role === "author" && (
            <div className="bg-warning-soft rounded-panel p-8 space-y-6">
              <div>
                <h3 className="text-[17px] font-medium text-warning flex items-center gap-2 mb-2">
                  <Crown className="w-5 h-5" /> Ứng tuyển Tác giả Tiềm năng
                </h3>
                <p className="text-[14px] text-warning">
                  Trở thành Tác giả Tiềm năng để nhận ưu đãi hiển thị và thu nhập đặc biệt
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <input
                  value={motivation}
                  onChange={(e) => setMotivation(e.target.value)}
                  placeholder=""
                  className="apple-input flex-1 h-[48px] border-warning-soft focus:border-warning bg-white"
                />
                <button
                  onClick={handleApplyAuthor}
                  disabled={isApplying}
                  className="pill-button bg-warning hover:bg-warning shrink-0"
                >
                  {isApplying ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    "Gửi yêu cầu"
                  )}
                </button>
              </div>
            </div>
          )}

          {user.role === "potential_author" && (
            <div className="bg-ink rounded-panel p-8 flex items-center gap-6 relative overflow-hidden">
              <div className="w-16 h-16 bg-ink rounded-full flex items-center justify-center shrink-0 z-10">
                <Crown className="w-8 h-8 text-warning" />
              </div>
              <div className="relative z-10">
                <h3 className="text-[17px] font-medium text-white mb-1">
                  Tác giả Tiềm năng
                </h3>
                <p className="text-[14px] text-ink-faint">
                  Danh hiệu cao quý dành cho tác giả xuất sắc
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
