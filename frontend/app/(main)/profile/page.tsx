"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { API_URL } from "@/features/auth/services/user_authentication.service";
import { updateProfileAPI } from "@/features/provision/services/system_setting.service";
import { uploadAssetAPI } from "@/features/content/services/file_upload.service";
import {
  User,
  Camera,
  Save,
  LogOut,
  Loader2,
  BadgeCheck,
  ShieldCheck,
  Crown
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
        showToast("Đã cập nhật định danh hồ sơ thành công", "success");
      } else {
        showToast("Cập nhật thất bại. Vui lòng thử lại", "error");
      }
    } catch (err: any) {
      showToast("Hệ thống bảo trì. Vui lòng thử lại sau", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) {
      showToast("Vui lòng nhập lý do ứng tuyển", "error");
      return;
    }
    setIsApplying(true);
    try {
      showToast("Đã gửi đơn ứng tuyển tác giả tiềm năng", "success");
      setMotivation("");
    } catch (e: any) {
      showToast("Giao thức ứng tuyển thất bại", "error");
    } finally {
      setIsApplying(false);
    }
  };

  const handleBecomeAuthor = async () => {
    setIsSaving(true);
    try {
      showToast("Chúc mừng! Bạn đã trở thành tác giả chính thức", "success");
      window.location.reload();
    } catch (e: any) {
      showToast("Nâng cấp tác giả thất bại", "error");
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
        showToast("Đã cập nhật ảnh đại diện mới", "success");
      }
    } catch (err: any) {
      showToast("Lỗi kết nối khi tải ảnh", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 h-[calc(100dvh-var(--navbar-height))] flex flex-col font-sans text-black selection:bg-black selection:text-white">
      <div className="border-b border-zinc-100 pb-4 mb-6 shrink-0 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 mb-1 flex items-center gap-2">
          Hồ sơ cá nhân
        </h1>
        <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
          Quản lý thông tin định danh và cài đặt tài khoản
        </p>
      </div>

      <div
        className="grid lg:grid-cols-12 gap-6 flex-1 min-h-0 transition-opacity duration-500"
        style={{ opacity: visible ? 1 : 0, transitionDelay: "100ms" }}
      >
        <aside className="lg:col-span-4 xl:col-span-3 space-y-6 flex flex-col shrink-0">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-8 flex flex-col items-center text-center">
            <div className="relative group mb-6">
              <div className="w-32 h-32 rounded-full border border-zinc-100 bg-zinc-50 flex items-center justify-center overflow-hidden shadow-sm transition-transform duration-300 group-hover:scale-105">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-12 h-12 text-zinc-300 stroke-[1.5]" />
                )}
              </div>
              <label className="absolute inset-0 bg-white/60 backdrop-blur-sm opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center text-black cursor-pointer rounded-full transition-all duration-300">
                <Camera className="w-6 h-6 mb-2 text-black" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-black">
                  Đổi ảnh
                </span>
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                />
              </label>
            </div>

            <div className="w-full mb-8">
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <h2 className="text-xl font-bold tracking-tight text-zinc-900 truncate px-2">
                  {user.full_name || "Ẩn danh"}
                </h2>
                {user.role === "admin" && <ShieldCheck className="w-5 h-5 text-purple-600 shrink-0" />}
                {user.role === "author" && <BadgeCheck className="w-5 h-5 text-blue-500 shrink-0" />}
                {user.role === "potential_author" && <Crown className="w-5 h-5 text-amber-500 shrink-0" />}
              </div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                @{user.slug || "nguoidung"}
              </p>
              
              <div className="mt-4 flex justify-center">
                <span className={`px-3 py-1.5 text-[9px] font-bold uppercase tracking-widest rounded-xl ${
                  user.role === "admin" ? "bg-purple-50 text-purple-700 border border-purple-100" :
                  user.role === "author" ? "bg-blue-50 text-blue-700 border border-blue-100" :
                  user.role === "potential_author" ? "bg-amber-50 text-amber-700 border border-amber-100" :
                  "bg-zinc-100 text-zinc-700 border border-zinc-200"
                }`}>
                  {user.role === "admin" ? "Quản trị viên" : user.role === "author" ? "Tác giả" : user.role === "potential_author" ? "Tác giả tiềm năng" : "Độc giả"}
                </span>
              </div>
            </div>

            <button
              onClick={logoutState}
              className="w-full h-11 bg-white border border-red-100 text-red-600 text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:bg-red-50 hover:border-red-200 shadow-sm"
            >
              <LogOut className="w-4 h-4" /> Đăng xuất
            </button>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-9 space-y-6 flex-1 overflow-y-auto custom-scrollbar pr-2">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-sm p-8 space-y-8">
            <div className="flex items-center gap-2 mb-2 pb-4 border-b border-zinc-100">
              <User className="w-5 h-5 text-black" />
              <div>
                <h2 className="text-sm font-bold uppercase tracking-widest text-zinc-900">
                  Thông tin định danh
                </h2>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 block">
                  Địa chỉ Email
                </label>
                <div className="w-full h-12 bg-zinc-50/80 border border-zinc-200 px-4 flex items-center text-zinc-500 text-sm font-medium cursor-not-allowed rounded-2xl">
                  {user.email}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 block">
                  Tên hiển thị
                </label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full h-12 bg-zinc-50 border border-zinc-200 px-4 text-sm font-bold focus:outline-none focus:border-black focus:bg-white rounded-2xl shadow-sm transition-all"
                  placeholder="Nhập tên hiển thị"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 block">
                Tiểu sử
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Nhập thông tin giới thiệu ngắn gọn"
                className="w-full h-24 bg-zinc-50 border border-zinc-200 p-4 text-sm font-medium focus:outline-none focus:border-black focus:bg-white rounded-2xl shadow-sm transition-all resize-none"
              />
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="h-11 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest flex items-center justify-center gap-2 disabled:opacity-50 rounded-2xl hover:bg-zinc-800 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Lưu thay đổi
              </button>
            </div>
          </div>

          {user.role === "reader" && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50/30 border border-blue-100 rounded-3xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-sm font-bold tracking-tight text-blue-900 mb-1 flex items-center gap-2">
                  <BadgeCheck className="w-5 h-5 text-blue-600" /> Trở thành Tác giả
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-blue-600/80 mt-2">
                  Nâng cấp tài khoản để bắt đầu xuất bản nội dung và xây dựng cộng đồng của riêng bạn.
                </p>
              </div>
              <button
                onClick={handleBecomeAuthor}
                disabled={isSaving}
                className="h-11 px-6 bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md shrink-0 flex items-center gap-2"
              >
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : "Nâng cấp ngay"}
              </button>
            </div>
          )}

          {user.role === "author" && (
            <div className="bg-gradient-to-br from-amber-50 to-orange-50/30 border border-amber-100 rounded-3xl p-8 space-y-6">
              <div>
                <h3 className="text-sm font-bold tracking-tight text-amber-900 mb-1 flex items-center gap-2">
                  <Crown className="w-5 h-5 text-amber-600" /> Ứng tuyển Tác giả Tiềm năng
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-amber-700/80 mt-2">
                  Trở thành Tác giả Tiềm năng để nhận ưu đãi hiển thị và thu nhập đặc biệt từ nền tảng.
                </p>
              </div>
              <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
                <input
                  value={motivation}
                  onChange={(e) => setMotivation(e.target.value)}
                  placeholder="Lý do ứng tuyển tác giả tiềm năng..."
                  className="flex-1 w-full h-11 bg-white border border-amber-200 px-4 text-sm font-medium focus:outline-none focus:border-amber-400 rounded-2xl shadow-sm transition-all placeholder:text-amber-300 text-amber-900"
                />
                <button
                  onClick={handleApplyAuthor}
                  disabled={isApplying}
                  className="w-full md:w-auto h-11 px-8 bg-amber-500 text-white text-[10px] font-bold uppercase tracking-widest disabled:opacity-50 rounded-2xl shrink-0 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
                >
                  {isApplying ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Gửi yêu cầu"}
                </button>
              </div>
            </div>
          )}

          {user.role === "potential_author" && (
            <div className="bg-gradient-to-br from-zinc-900 to-black border border-zinc-800 rounded-3xl shadow-xl p-8 flex items-center gap-5 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10"></div>
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center shrink-0 border border-white/10 backdrop-blur-md relative z-10">
                <Crown className="w-7 h-7 text-amber-400" />
              </div>
              <div className="relative z-10">
                <h3 className="text-sm font-bold tracking-widest text-white mb-1 uppercase">
                  Tác giả Tiềm năng
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
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
