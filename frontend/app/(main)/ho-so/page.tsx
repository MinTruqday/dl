"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/Auth";
import { API_URL } from "@/services/authentication.service";
import { updateProfileAPI } from "@/services/setting.service";
import { getDetailedHistoryAPI } from "@/services/wallet.service";
import { createDepositLinkAPI } from "@/services/deposit.service";
import { applyAuthorAPI, becomeAuthorAPI } from "@/services/setting.service";
import { uploadAssetAPI } from "@/services/upload.service";
import { getBookmarksAPI } from "@/services/bookmark.service";
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
import { useToast } from "@/contexts/Toast";
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
    "info"
  );

  const [historyList, setHistoryList] = useState<any[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);

  const [bookmarks, setBookmarks] = useState<any[]>([]);
  const [isBookmarksLoading, setIsBookmarksLoading] = useState(false);

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
      const checkoutUrl = res.data?.checkout_url || res.data?.payment_url || res.checkout_url;
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
      await applyAuthorAPI({ reason: motivation });
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
      await becomeAuthorAPI();
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
      const res = await uploadAssetAPI(e.target.files[0], 'image');
      if (res.data?.url) {
        setAvatarUrl(
          res.data.url.startsWith("http") ? res.data.url : `${API_URL}/storage/${res.data.url}`
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6  "
        style={{ opacity: visible ? 1 : 0 }}
      >
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Hồ sơ cá nhân</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Quản lý định danh và tài sản hệ thống
          </p>
        </div>
        <button
          onClick={logoutState}
          className="h-10 px-6 bg-white border border-zinc-200 text-black text-xs font-medium flex items-center gap-2 rounded-none"
        >
          <LogOut className="w-4 h-4" /> Đăng xuất
        </button>
      </div>

      <div
        className="grid lg:grid-cols-12 gap-12  "
        style={{ opacity: visible ? 1 : 0 }}
      >
        <aside className="lg:col-span-4 space-y-8">
          <div className="border border-zinc-200 bg-white p-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="relative group">
                <div className="w-32 h-32 rounded-none border border-zinc-200 overflow-hidden bg-zinc-50 flex items-center justify-center shrink-0">
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
                <label className="absolute inset-0 bg-white/80 opacity-0 flex flex-col items-center justify-center text-black cursor-pointer rounded-none border border-zinc-200">
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
                  @{user.username || "nguoidung"}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 border-t border-zinc-200 pt-6 mt-6">
              <div className="flex flex-col items-center justify-center border-r border-zinc-200 px-2">
                <span className="text-[10px] text-zinc-500 font-medium mb-1 uppercase tracking-widest">
                  Chuỗi
                </span>
                <span className="text-sm font-semibold text-black">
                  {user.streak_days || 0}
                </span>
              </div>
              <div className="flex flex-col items-center justify-center border-r border-zinc-200 px-2">
                <span className="text-[10px] text-zinc-500 font-medium mb-1 uppercase tracking-widest">
                  Thực thể
                </span>
                <span className="text-sm font-semibold text-black">
                  {bookmarks.length || 0}
                </span>
              </div>
              <div className="flex flex-col items-center justify-center px-2">
                <span className="text-[10px] text-zinc-500 font-medium mb-1 uppercase tracking-widest">
                  Số dư
                </span>
                <span className="text-sm font-semibold text-black">
                  {user.wallet_balance?.toLocaleString() || 0}
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-semibold text-black border-b border-zinc-200 pb-2">
              Giao diện quản trị
            </h3>
            <nav className="flex flex-col border border-zinc-200 bg-white">
              {[
                { id: "info", icon: User, label: "Thông tin định danh" },
                {
                  id: "bookmarks",
                  icon: Bookmark,
                  label: "Bộ sưu tập nội dung",
                },
                { id: "history", icon: History, label: "Nhật ký hoạt động" },
              ].map((tab, idx) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-4 py-3 text-xs font-medium ${idx !== 2 ? "border-b border-zinc-200" : ""
                    } ${activeTab === tab.id
                      ? "bg-zinc-50 text-black font-semibold"
                      : "text-zinc-500"
                    }`}
                >
                  <div className="flex items-center gap-3">
                    {tab.label}
                  </div>
                  {activeTab === tab.id && (
                    <ChevronRight className="w-4 h-4 text-black" />
                  )}
                </button>
              ))}
            </nav>
          </div>

          <div className="border border-zinc-200 bg-zinc-50 p-6 space-y-4">
            <div className="border-b border-zinc-200 pb-3">
              <span className="text-xs font-semibold text-black flex items-center gap-2">
                <CreditCard className="w-4 h-4" /> Nạp tiền (VNĐ)
              </span>
            </div>
            <div className="space-y-3">
              <input
                type="number"
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                placeholder="Nhập số tiền"
                className="w-full h-10 bg-white border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none"
              />
              <button
                onClick={handleDeposit}
                disabled={isDepositing}
                className="w-full h-10 bg-black text-white text-xs font-medium flex items-center justify-center gap-2 disabled:opacity-50 rounded-none"
              >
                {isDepositing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Kích hoạt nạp tiền"
                )}
              </button>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-8">
          {activeTab === "info" && (
            <div className="border border-zinc-200 bg-white p-8 space-y-8">
              <div className="border-b border-zinc-200 pb-4">
                <h3 className="text-sm font-semibold text-black">
                  Thông tin định danh
                </h3>
                <p className="text-xs text-zinc-500 font-medium mt-1">
                  Cập nhật dữ liệu hệ thống cho tài khoản của bạn
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest flex items-center gap-2">
                    <Mail className="w-3 h-3" /> Địa chỉ liên kết
                  </label>
                  <div className="w-full h-10 bg-zinc-50 border border-zinc-200 px-3 flex items-center text-zinc-500 text-xs font-medium cursor-not-allowed rounded-none">
                    {user.email}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                    Danh xưng hiển thị
                  </label>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full h-10 bg-white border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-black uppercase tracking-widest flex items-center gap-2">
                  <LinkIcon className="w-3 h-3" /> Tiểu sử (Bio)
                </label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Nhập thông tin giới thiệu ngắn gọn"
                  className="w-full min-h-[160px] bg-white border border-zinc-200 p-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none resize-none placeholder:text-zinc-400"
                />
              </div>

              <div className="flex justify-end pt-6 border-t border-zinc-200">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="h-10 px-6 bg-black text-white text-xs font-medium flex items-center gap-2 disabled:opacity-50 rounded-none"
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
                <div className="mt-12 pt-8 border-t border-zinc-200 space-y-4">
                  <h3 className="text-sm font-semibold text-black">
                    Trở thành tác giả
                  </h3>
                  <p className="text-xs text-zinc-500 font-medium">
                    Bạn có thể nâng cấp tài khoản lên tác giả ngay lập tức để bắt đầu xuất bản nội dung.
                  </p>
                  <button
                    onClick={handleBecomeAuthor}
                    disabled={isSaving}
                    className="h-10 px-6 bg-black text-white text-xs font-medium disabled:opacity-50 rounded-none"
                  >
                    {isSaving ? "Đang xử lý..." : "Trở thành tác giả ngay"}
                  </button>
                </div>
              )}

              {user.role === "author" && (
                <div className="mt-12 pt-8 border-t border-zinc-200 space-y-4">
                  <h3 className="text-sm font-semibold text-black">
                    Ứng tuyển Tác giả tiềm năng
                  </h3>
                  <p className="text-xs text-zinc-500 font-medium">
                    Nâng cấp lên vị trí tác giả tiềm năng để nhận được nhiều ưu đãi và hiển thị đặc biệt.
                  </p>
                  <div className="flex items-start gap-4">
                    <input
                      value={motivation}
                      onChange={(e) => setMotivation(e.target.value)}
                      placeholder="Lý do ứng tuyển tác giả tiềm năng"
                      className="flex-1 h-10 bg-zinc-50 border border-zinc-200 px-3 text-xs font-medium focus:outline-none focus:border-black  rounded-none"
                    />
                    <button
                      onClick={handleApplyAuthor}
                      disabled={isApplying}
                      className="h-10 px-6 border border-black bg-white text-black text-xs font-medium disabled:opacity-50 rounded-none shrink-0"
                    >
                      {isApplying ? "Đang gửi" : "Gửi yêu cầu"}
                    </button>
                  </div>
                </div>
              )}

              {user.role === "potential_author" && (
                <div className="mt-12 pt-8 border-t border-zinc-200 space-y-4">
                  <h3 className="text-sm font-semibold text-black">
                    Vị thế Tác giả tiềm năng
                  </h3>
                  <p className="text-xs text-zinc-500 font-medium italic">
                    Chúc mừng! Bạn hiện là tác giả tiềm năng của hệ thống DocLib.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "bookmarks" && (
            <div className="border border-zinc-200 bg-white p-8 space-y-8">
              <div className="border-b border-zinc-200 pb-4 flex justify-between items-end">
                <div>
                  <h3 className="text-sm font-semibold text-black">
                    Bộ sưu tập nội dung
                  </h3>
                  <p className="text-xs text-zinc-500 font-medium mt-1">
                    Tài liệu đã được lưu trữ vào không gian cá nhân
                  </p>
                </div>
                <span className="text-xs font-semibold text-black">
                  {bookmarks.length} thực thể
                </span>
              </div>

              {isBookmarksLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-4 border border-dashed border-zinc-200 bg-zinc-50">
                  <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                  <span className="text-xs font-medium text-zinc-500">
                    Đang tải bộ sưu tập
                  </span>
                </div>
              ) : bookmarks.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {bookmarks.map((doc) => (
                    <Link
                      key={doc._id}
                      href={`/tai-lieu/${doc.slug || doc._id}`}
                      className="border border-zinc-200 bg-white group flex flex-col"
                    >
                      <div className="aspect-[3/4] border-b border-zinc-200 bg-zinc-50 overflow-hidden relative shrink-0">
                        {doc.cover_url ? (
                          <img
                            src={
                              doc.cover_url.startsWith("http")
                                ? doc.cover_url
                                : `${API_URL}/storage/${doc.cover_url}`
                            }
                            className="w-full h-full object-cover grayscale mix-blend-multiply"
                            alt={doc.title}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <FileText className="w-6 h-6 text-zinc-400 stroke-[1]" />
                          </div>
                        )}
                      </div>
                      <div className="p-3 flex-1 flex flex-col justify-between">
                        <h4 className="text-xs font-semibold text-black line-clamp-2">
                          {doc.title}
                        </h4>
                        <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-medium mt-2">
                          <span className="truncate">
                            {doc.publisher_name || "DocLib Institutional"}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
                  <p className="text-sm font-medium text-zinc-500">
                    Chưa có dữ liệu
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === "history" && (
            <div className="border border-zinc-200 bg-white p-8 space-y-8">
              <div className="border-b border-zinc-200 pb-4 flex justify-between items-end">
                <div>
                  <h3 className="text-sm font-semibold text-black">
                    Nhật ký hoạt động
                  </h3>
                  <p className="text-xs text-zinc-500 font-medium mt-1">
                    Dòng tiền và giao dịch hệ thống
                  </p>
                </div>
              </div>

              {isHistoryLoading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-4 border border-dashed border-zinc-200 bg-zinc-50">
                  <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                  <span className="text-xs font-medium text-zinc-500">
                    Đang tải dữ liệu
                  </span>
                </div>
              ) : historyList.length > 0 ? (
                <div className="space-y-4">
                  {historyList.map((tx, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border border-zinc-200 bg-zinc-50 gap-4"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 flex items-center justify-center border shrink-0 ${tx.amount > 0
                              ? "border-zinc-200 bg-white text-black"
                              : "border-black bg-black text-white"
                            }`}
                        >
                          {tx.amount > 0 ? (
                            <ArrowUpRight className="w-5 h-5" />
                          ) : (
                            <ArrowDownLeft className="w-5 h-5" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-black">
                            {tx.description ||
                              tx.type_display ||
                              "Giao dịch"}
                          </p>
                          <p className="text-[10px] font-medium text-zinc-500 mt-1">
                            {new Date(tx.created_at).toLocaleString("vi-VN")} •
                            TX-{idx + 1000}
                          </p>
                        </div>
                      </div>
                      <div className="text-left sm:text-right flex flex-col sm:items-end">
                        <span
                          className={`text-sm font-bold ${tx.amount > 0 ? "text-black" : "text-zinc-500"
                            }`}
                        >
                          {tx.amount > 0 ? "+" : ""}
                          {tx.amount.toLocaleString()} dl
                        </span>
                        <span className="text-[10px] font-medium text-zinc-500 mt-1 flex items-center gap-1.5">
                          <div className="w-1.5 h-1.5 bg-black rounded-none"></div>
                          Hoàn tất
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-24 flex flex-col items-center justify-center border border-zinc-200 bg-white">
                  <p className="text-sm font-medium text-zinc-500">
                    Chưa có dữ liệu
                  </p>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
