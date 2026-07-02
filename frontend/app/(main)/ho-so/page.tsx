"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { API_URL } from "@/features/auth/services/user_authentication.service";
import { updateProfileAPI } from "@/features/provision/services/system_setting.service";
import { uploadAssetAPI } from "@/features/content/services/file_upload.service";
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
        showToast("Đã cập nhật hồ sơ", "success");
      } else {
        showToast("Cập nhật thất bại", "error");
      }
    } catch (err: any) {
      showToast("Lỗi hệ thống", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) return showToast("Vui lòng nhập lý do", "error");
    setIsApplying(true);
    try {
      showToast("Đã gửi đơn ứng tuyển", "success");
      setMotivation("");
    } catch (e: any) {
      showToast("Ứng tuyển thất bại", "error");
    } finally {
      setIsApplying(false);
    }
  };

  const handleBecomeAuthor = async () => {
    setIsSaving(true);
    try {
      showToast("Đã trở thành tác giả", "success");
      window.location.reload();
    } catch (e: any) {
      showToast("Nâng cấp thất bại", "error");
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
            : `${API_URL}/storage/${res.data.url}`,
        );
        showToast("Đã cập nhật ảnh đại diện", "success");
      }
    } catch (err: any) {
      showToast("Lỗi tải ảnh", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#6E6E73]" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-6 min-h-[calc(100dvh-56px)] flex flex-col font-sans text-[#1D1D1F]">
      <div
        className={`grid md:grid-cols-12 gap-8 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <aside className="md:col-span-4 xl:col-span-4 space-y-6">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6 flex flex-col items-center text-center">
            <div className="relative group mb-6">
              <div className="w-32 h-32 rounded-full bg-[#D2D2D7] flex items-center justify-center overflow-hidden transition-transform duration-300 group-hover:scale-105">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-12 h-12 text-white" />
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
                <p className="text-[13px] font-medium text-[#6E6E73] mb-4 truncate px-2">
                  {user.full_name || "Ẩn danh"}
                </p>
                {user.role === "admin" && (
                  <ShieldCheck className="w-5 h-5 text-[#8E8D91]" />
                )}
                {user.role === "author" && (
                  <BadgeCheck className="w-5 h-5 text-[#0071E3]" />
                )}
                {user.role === "potential_author" && (
                  <Crown className="w-5 h-5 text-[#FF9500]" />
                )}
              </div>
              <p className="text-[14px] text-[#6E6E73]">
                @{user.slug || "nguoidung"}
              </p>

              <div className="mt-4 flex justify-center">
                <span
                  className={`px-3 py-1 text-[13px] font-medium rounded-full ${
                    user.role === "admin"
                      ? "bg-[#E8E8ED] text-[#1D1D1F]"
                      : user.role === "author"
                        ? "bg-[#EBF4FF] text-[#0071E3]"
                        : user.role === "potential_author"
                          ? "bg-[#FFF4E5] text-[#FF9500]"
                          : "bg-[#E8E8ED] text-[#1D1D1F]"
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
              className="w-full py-3 bg-white text-[#FF3B30] text-[15px] font-medium flex items-center justify-center gap-2 rounded-full transition-colors hover:bg-[#F5F5F7]"
            >
              <LogOut className="w-4 h-4" /> Đăng xuất
            </button>
          </div>
        </aside>

        <main className="md:col-span-8 xl:col-span-8 space-y-6">
          <div className="bg-[#F5F5F7] rounded-[18px] p-6 space-y-6">
            <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-6">
              Thông tin cá nhân
            </h2>

            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
                  Địa chỉ Email
                </label>
                <div className="apple-input w-full h-[48px] bg-[#E8E8ED] border-transparent px-4 flex items-center text-[#6E6E73] text-[15px] cursor-not-allowed">
                  {user.email}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
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
              <label className="text-[13px] font-medium text-[#6E6E73] ml-1 block">
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
            <div className="bg-[#EBF4FF] rounded-[18px] p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-[17px] font-medium text-[#0071E3] flex items-center gap-2 mb-2">
                  <BadgeCheck className="w-5 h-5" /> Trở thành Tác giả
                </h3>
                <p className="text-[14px] text-[#0055C6]">
                  Nâng cấp tài khoản để xuất bản nội dung và xây dựng cộng đồng
                  của riêng bạn.
                </p>
              </div>
              <button
                onClick={handleBecomeAuthor}
                disabled={isSaving}
                className="pill-button shrink-0 bg-[#0071E3] hover:bg-[#0055C6]"
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
            <div className="bg-[#FFF4E5] rounded-[18px] p-8 space-y-6">
              <div>
                <h3 className="text-[17px] font-medium text-[#FF9500] flex items-center gap-2 mb-2">
                  <Crown className="w-5 h-5" /> Ứng tuyển Tác giả Tiềm năng
                </h3>
                <p className="text-[14px] text-[#CC7700]">
                  Trở thành Tác giả Tiềm năng để nhận ưu đãi hiển thị và thu
                  nhập đặc biệt.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <input
                  value={motivation}
                  onChange={(e) => setMotivation(e.target.value)}
                  placeholder=""
                  className="apple-input flex-1 h-[48px] border-[#FFD699] focus:border-[#FF9500] bg-white"
                />
                <button
                  onClick={handleApplyAuthor}
                  disabled={isApplying}
                  className="pill-button bg-[#FF9500] hover:bg-[#CC7700] shrink-0"
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
            <div className="bg-[#1D1D1F] rounded-[18px] p-8 flex items-center gap-6 relative overflow-hidden">
              <div className="w-16 h-16 bg-[#333336] rounded-full flex items-center justify-center shrink-0 z-10">
                <Crown className="w-8 h-8 text-[#FF9500]" />
              </div>
              <div className="relative z-10">
                <h3 className="text-[17px] font-medium text-white mb-1">
                  Tác giả Tiềm năng
                </h3>
                <p className="text-[14px] text-[#A1A1A6]">
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
