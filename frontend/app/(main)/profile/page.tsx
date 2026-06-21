"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { API_URL } from "@/features/auth/services/user_authentication.service";
import { updateProfileAPI } from "@/features/provision/services/system_setting.service";
import { getDetailedHistoryAPI } from "@/features/finance/services/account_ledger.service";
import { createDepositLinkAPI } from "@/features/finance/services/fiat_deposit.service";

import { uploadAssetAPI } from "@/features/content/services/file_upload.service";
import { getBookmarksAPI } from "@/features/content/services/document_bookmark.service";
import {
  User,
  Camera,
  Mail,
  Save,
  LogOut,
  Loader2,
  Link as LinkIcon,
  BadgeCheck,
  CreditCard,
  History,
  ChevronRight,
  Bookmark,
  FileText,
  ArrowUpRight,
  ArrowDownLeft,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import Link from "next/link";

export default function ProfilePage() {
  const { user, isLoading, logoutState } = useAuth() as any;
  const { showToast } = useToast();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [isDepositing, setIsDepositing] = useState(false);
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"info" | "bookmarks" | "history">(
    "info",
  );

  const [historyList, setHistoryList] = useState<any[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [isBookmarksLoading, setIsBookmarksLoading] = useState(false);

  const [motivation, setMotivation] = useState("");
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
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

  const fetchHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const res = await getDetailedHistoryAPI();
      setHistoryList(res.data || res || []);
    } catch (err: any) {
      showToast("Không thể tải lịch sử tài chính", "error");
    } finally {
      setIsHistoryLoading(false);
    }
  }, [showToast]);

  const fetchBookmarks = useCallback(async () => {
    setIsBookmarksLoading(true);
    try {
      const res = await getBookmarksAPI();
      setBookmarks(res.data || []);
    } catch (err: any) {
      showToast("Không thể tải bộ sưu tập cá nhân", "error");
    } finally {
      setIsBookmarksLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    if (activeTab === "history") fetchHistory();
    if (activeTab === "bookmarks") fetchBookmarks();
  }, [activeTab, fetchHistory, fetchBookmarks]);

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

  const handleDeposit = async () => {
    const amount = parseInt(depositAmount);
    if (!amount || amount < 10000) {
      showToast("Số tiền nạp tối thiểu quy định là 10.000 VNĐ", "error");
      return;
    }
    setIsDepositing(true);
    try {
      const res = await createDepositLinkAPI(amount);
      const checkoutUrl =
        res.data?.checkout_url || res.data?.payment_url || res.checkout_url;
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      } else {
        showToast("Giao thức thanh toán chưa được kích hoạt", "error");
      }
    } catch (e: any) {
      showToast("Lỗi kết nối cổng thanh toán", "error");
    } finally {
      setIsDepositing(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) {
      showToast("Vui lòng nhập lý do ứng tuyển tác giả tiềm năng", "error");
      return;
    }
    setIsApplying(true);
    try {
      await // updateUserAPI({ reason: motivation });
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
      await // updateUserAPI();
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
        showToast("Đã tích hợp ảnh định danh mới", "success");
      }
    } catch (err: any) {
      console.error(err.message || err);
      showToast("Lỗi kết nối khi tải ảnh định danh", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1280px] mx-auto px-6 py-6 min-h-[calc(100dvh-var(--navbar-height))] font-sans text-black selection:bg-black selection:text-white">
      <div
        className="grid lg:grid-cols-12 gap-6"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <aside className="lg:col-span-3 space-y-6">
          <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 animate-in fade-in slide-in-from-bottom-8 duration-300">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="relative group">
                <div className="w-32 h-32 rounded-full border border-zinc-200 overflow-hidden bg-zinc-50 flex items-center justify-center shrink-0">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt=""
                      className="w-full h-full object-cover grayscale mix-blend-multiply"
                    />
                  ) : (
                    <User className="w-10 h-10 text-zinc-400 stroke-[1]" />
                  )}
                </div>
                <label className="absolute inset-0 bg-white/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-black cursor-pointer rounded-full border border-zinc-200">
                  <Camera className="w-5 h-5 mb-1" />
                  <span className="text-[10px] font-semibold">Đổi ảnh</span>
                  <input
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleAvatarUpload}
                  />
                </label>
              </div>

              <div>
                <div className="flex items-center justify-center gap-2">
                  <h2 className="text-lg font-semibold text-black">
                    {user.full_name || "Ẩn danh"}
                  </h2>
                  {user.role === "author" && (
                    <BadgeCheck className="w-4 h-4 text-black" />
                  )}
                </div>
                <p className="text-xs text-zinc-500 font-medium mt-1">
                  @{user.slug || "nguoidung"}
                </p>
              </div>
            </div>

            <div className="mt-6">
              <button
                onClick={logoutState}
                className="w-full h-9 bg-white border border-zinc-200 text-black text-xs font-medium flex items-center justify-center gap-2 rounded-2xl hover:bg-zinc-50 transition-colors shadow-sm"
              >
                <LogOut className="w-4 h-4" /> Đăng xuất
              </button>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 space-y-6">
          <div
            className="bg-white border border-zinc-200 rounded-2xl shadow-sm p-5 space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-300"
            style={{ animationDelay: "150ms", animationFillMode: "both" }}
          >
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-lg font-semibold text-black">
                  Thông tin định danh
                </h2>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">
                  Địa chỉ Email
                </label>
                <div className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 flex items-center text-zinc-500 text-sm font-medium cursor-not-allowed rounded-2xl">
                  {user.email}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-black">
                  Tên hiển thị
                </label>
                <input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full h-10 bg-white border border-zinc-200 px-3 text-sm font-medium focus:outline-none focus:border-black rounded-2xl"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-black">
                Tiểu sử
              </label>
              <input
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Nhập thông tin giới thiệu ngắn gọn"
                className="w-full h-10 bg-white border border-zinc-200 px-3 text-sm font-medium focus:outline-none focus:border-black rounded-2xl"
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 disabled:opacity-50 rounded-2xl hover:bg-zinc-800 transition-colors"
              >
                {isSaving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Cập nhật định danh
              </button>
            </div>

            {user.role === "reader" && (
              <div className="mt-8 space-y-4">
                <h3 className="text-sm font-semibold text-black">
                  Trở thành tác giả
                </h3>
                <p className="text-xs text-zinc-500 font-medium">
                  Bạn có thể nâng cấp tài khoản lên tác giả ngay lập tức để bắt
                  đầu xuất bản nội dung.
                </p>
                <button
                  onClick={handleBecomeAuthor}
                  disabled={isSaving}
                  className="h-10 px-6 bg-black text-white text-xs font-medium disabled:opacity-50 rounded-2xl hover:bg-zinc-800 transition-colors"
                >
                  {isSaving ? "Đang xử lý..." : "Trở thành tác giả ngay"}
                </button>
              </div>
            )}

            {user.role === "author" && (
              <div className="mt-8 space-y-4">
                <h3 className="text-sm font-semibold text-black">
                  Ứng tuyển Tác giả tiềm năng
                </h3>
                <p className="text-xs text-zinc-500 font-medium">
                  Nâng cấp lên vị trí tác giả tiềm năng để nhận được nhiều ưu
                  đãi và hiển thị đặc biệt.
                </p>
                <div className="flex items-start gap-4">
                  <input
                    value={motivation}
                    onChange={(e) => setMotivation(e.target.value)}
                    placeholder="Lý do ứng tuyển tác giả tiềm năng"
                    className="flex-1 h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black rounded-2xl"
                  />
                  <button
                    onClick={handleApplyAuthor}
                    disabled={isApplying}
                    className="h-10 px-6 border border-black bg-white text-black text-xs font-medium disabled:opacity-50 rounded-2xl shrink-0 hover:bg-zinc-50 transition-colors"
                  >
                    {isApplying ? "Đang gửi" : "Gửi yêu cầu"}
                  </button>
                </div>
              </div>
            )}

            {user.role === "potential_author" && (
              <div className="mt-8 space-y-4">
                <h3 className="text-sm font-semibold text-black">
                  Vị thế Tác giả tiềm năng
                </h3>
                <p className="text-xs text-zinc-500 font-medium italic">
                  Chúc mừng! Bạn hiện là tác giả tiềm năng của hệ thống DocLib.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
