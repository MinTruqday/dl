"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  API_URL,
  updateProfileAPI,
  depositDLAPI,
  getDetailedHistoryAPI,
  applyAuthorAPI,
  uploadMediaAPI,
  getBookmarksAPI
} from "@/app/lib/api";
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
  Sparkles,
  Bookmark,
  FileText,
  ArrowUpRight,
  ArrowDownLeft,
  Settings
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Notification } from "@/app/components/NotificationToast";
import Link from "next/link";

export default function ProfilePage() {
  const { user, isLoading, logoutState } = useAuth() as any;
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [isDepositing, setIsDepositing] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"info" | "bookmarks" | "history">("info");
  
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
        setNotification({ type: "error", text: "Không thể tải lịch sử tài chính" });
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  const fetchBookmarks = useCallback(async () => {
    setIsBookmarksLoading(true);
    try {
      const res = await getBookmarksAPI();
      setBookmarks(res.data || []);
    } catch (err: any) {
        setNotification({ type: "error", text: "Không thể tải bộ sưu tập cá nhân" });
    } finally {
      setIsBookmarksLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "history") fetchHistory();
    if (activeTab === "bookmarks") fetchBookmarks();
  }, [activeTab, fetchHistory, fetchBookmarks]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await updateProfileAPI({ full_name: fullName, bio, avatar_url: avatarUrl });
      if (res && (res.status === 200 || res.id)) {
        setNotification({ type: "success", text: "Đã cập nhật định danh hồ sơ thành công" });
      } else {
        setNotification({ type: "error", text: "Cập nhật thất bại. Vui lòng thử lại" });
      }
    } catch (err: any) {
      setNotification({ type: "error", text: "Hệ thống bảo trì. Vui lòng thử lại sau" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeposit = async () => {
    const amount = parseInt(depositAmount);
    if (!amount || amount < 10000) {
      setNotification({ type: "error", text: "Số tiền nạp tối thiểu quy định là 10.000 VNĐ" });
      return;
    }
    setIsDepositing(true);
    try {
      const res = await depositDLAPI(amount);
      if (res.data?.payment_url) {
        window.location.href = res.data.payment_url;
      } else {
        setNotification({ type: "error", text: "Giao thức thanh toán chưa được kích hoạt" });
      }
    } catch (e: any) {
      setNotification({ type: "error", text: "Lỗi kết nối cổng thanh toán tri thức" });
    } finally {
      setIsDepositing(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) {
      setNotification({ type: "error", text: "Vui lòng nhập lý do ứng tuyển tác giả" });
      return;
    }
    setIsApplying(true);
    try {
      await applyAuthorAPI(motivation);
      setNotification({ type: "success", text: "Đã gửi đơn ứng tuyển vào mạng lưới tác giả" });
      setMotivation("");
    } catch (e: any) {
      setNotification({ type: "error", text: "Giao thức ứng tuyển thất bại" });
    } finally {
      setIsApplying(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setIsSaving(true);
    const formData = new FormData();
    formData.append("file", e.target.files[0]);
    try {
      const data = await uploadMediaAPI(formData);
      if (data.url) {
        setAvatarUrl(data.url.startsWith("http") ? data.url : `${API_URL}${data.url}`);
        setNotification({ type: "success", text: "Đã tích hợp ảnh định danh mới" });
      }
    } catch {
      setNotification({ type: "error", text: "Lỗi kết nối khi tải ảnh định danh" });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <Loader2 className="w-12 h-12 animate-spin text-zinc-100 stroke-[1]" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-7xl mx-auto px-10 py-16 font-sans text-black">
      {notification && (
          <div className="fixed top-24 right-8 z-[1100] w-80 animate-in slide-in-from-right-4 duration-300">
              <Notification type={notification.type} message={notification.text} />
          </div>
      )}

      <div 
        className="mb-20 border-b border-zinc-100 pb-16 flex flex-col md:flex-row md:items-end justify-between gap-12 transition-opacity duration-1000"
        style={{ opacity: visible ? 1 : 0 }}
      >
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tighter uppercase text-black leading-none">
            Hồ sơ & Định danh
          </h1>
          <p className="text-zinc-300 text-[11px] font-bold uppercase tracking-widest flex items-center gap-4">
            QUẢN LÝ THỰC THỂ CÁ NHÂN <div className="w-2 h-2 bg-black rounded-full animate-pulse" /> <Sparkles className="w-4 h-4 text-zinc-100" />
          </p>
        </div>
        <button
          onClick={logoutState}
          className="bg-zinc-50/50 text-black hover:bg-black hover:text-white border border-zinc-100 flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest h-14 px-10 transition-all active:scale-95 rounded-sm"
        >
          <LogOut className="w-4 h-4" />
          Đăng xuất hệ thống
        </button>
      </div>

      <div className="grid lg:grid-cols-12 gap-16">
        <aside className="lg:col-span-4 space-y-12">
          <div className="border border-zinc-100 bg-white p-12 rounded-sm relative group">
            <div className="flex flex-col items-center gap-10">
              <div className="relative group">
                <div className="w-52 h-52 border border-zinc-100 overflow-hidden bg-zinc-50 grayscale group-hover:grayscale-0 transition-all duration-700 rounded-sm">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="" className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-100">
                      <User className="w-20 h-20 stroke-[1]" />
                    </div>
                  )}
                </div>
                <label className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col items-center justify-center text-white cursor-pointer backdrop-blur-[2px] rounded-sm">
                  <Camera className="w-6 h-6 mb-3" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">Thay đổi định danh</span>
                  <input type="file" className="hidden" accept="image/*" onChange={handleAvatarUpload} />
                </label>
              </div>
              
              <div className="text-center space-y-4">
                <div className="flex items-center justify-center gap-3">
                    <h2 className="text-xl font-bold text-black uppercase tracking-tight">{user.full_name || "Thực thể ẩn danh"}</h2>
                    {user.role === "author" && <BadgeCheck className="w-5 h-5 text-black" />}
                </div>
                <div className="inline-flex items-center gap-3 px-4 py-2 bg-zinc-50 border border-zinc-100 text-[10px] font-bold text-zinc-300 uppercase tracking-widest rounded-sm">
                  @{user.username || "doclib_user"}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Giao diện quản trị</h3>
            <nav className="flex flex-col gap-3">
              {[
                { id: "info", icon: User, label: "Thông tin định danh" },
                { id: "bookmarks", icon: Bookmark, label: "Bộ sưu tập tri thức" },
                { id: "history", icon: History, label: "Lịch sử tương tác" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center justify-between px-8 h-16 text-[10px] font-bold uppercase tracking-widest transition-all border rounded-sm ${
                    activeTab === tab.id
                      ? "bg-black text-white border-black"
                      : "bg-white text-zinc-400 hover:bg-zinc-50 hover:text-black border-zinc-100"
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <tab.icon className="w-4 h-4" /> {tab.label}
                  </div>
                  <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === tab.id ? "rotate-90" : ""}`} />
                </button>
              ))}
            </nav>
          </div>

          <div className="p-10 border border-zinc-100 bg-zinc-50/20 space-y-10 rounded-sm">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Nguồn lực DL</span>
              <span className="text-2xl font-bold text-black tracking-tighter">{user.wallet_balance?.toLocaleString() || 0} <span className="text-zinc-200 text-sm italic">dl</span></span>
            </div>
            <div className="space-y-6">
              <label className="text-[9px] font-bold text-zinc-300 uppercase tracking-[0.2em] flex items-center gap-3 px-1">
                <CreditCard className="w-3.5 h-3.5" /> Nạp thêm nguồn lực (VNĐ)
              </label>
              <div className="space-y-4">
                <input
                  type="number"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  placeholder="Nhập giá trị..."
                  className="w-full h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:outline-none focus:border-black rounded-sm transition-all placeholder:text-zinc-100"
                />
                <button
                  onClick={handleDeposit}
                  disabled={isDepositing}
                  className="h-14 w-full bg-black text-white hover:bg-zinc-800 text-[10px] font-bold uppercase tracking-widest transition-all active:scale-95 rounded-sm"
                >
                  {isDepositing ? <Loader2 className="w-4 h-4 animate-spin" /> : "Kích hoạt nạp tiền"}
                </button>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-8">
          {activeTab === "info" && (
            <div className="bg-white border border-zinc-100 p-12 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700 rounded-sm">
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-black uppercase tracking-tight">Chi tiết thực thể</h3>
                <p className="text-zinc-300 text-[10px] font-bold uppercase tracking-widest">Đồng bộ hóa dữ liệu định danh hệ thống</p>
              </div>

              <div className="grid md:grid-cols-2 gap-12">
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1 flex items-center gap-3">
                    <Mail className="w-3.5 h-3.5" /> Địa chỉ liên kết
                  </label>
                  <div className="h-14 bg-zinc-50 border border-zinc-100 px-6 flex items-center text-zinc-300 text-xs font-bold rounded-sm cursor-not-allowed">
                    {user.email}
                  </div>
                </div>
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1">Danh xưng hiển thị</label>
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full h-14 bg-white border border-zinc-100 px-6 text-sm font-bold focus:outline-none focus:border-black rounded-sm transition-all"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest px-1 flex items-center gap-3">
                  <LinkIcon className="w-3.5 h-3.5" /> Tiểu sử tri thức (Bio)
                </label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Mô tả ngắn gọn về hành trình tri thức của bạn..."
                  className="w-full min-h-[260px] p-10 text-sm border border-zinc-100 rounded-sm focus:outline-none focus:border-black transition-all font-medium bg-zinc-50/20"
                />
              </div>

              <div className="flex justify-end pt-10 border-t border-zinc-50">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="bg-black text-white hover:bg-zinc-800 px-16 h-16 flex items-center gap-6 transition-all active:scale-95 rounded-sm"
                >
                  {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  <span className="text-[11px] font-bold uppercase tracking-[0.3em]">Cập nhật định danh</span>
                </button>
              </div>
            </div>
          )}

          {activeTab === "bookmarks" && (
            <div className="bg-white border border-zinc-100 p-12 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700 rounded-sm">
                <div className="flex items-center justify-between border-b border-zinc-100 pb-10">
                    <div className="space-y-4">
                        <h3 className="text-xl font-bold text-black uppercase tracking-tight">Bộ sưu tập tri thức</h3>
                        <p className="text-zinc-300 text-[10px] font-bold uppercase tracking-widest">Tài liệu đã được lưu trữ vào không gian cá nhân</p>
                    </div>
                    <div className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">{bookmarks.length} THỰC THỂ</div>
                </div>

                {isBookmarksLoading ? (
                    <div className="py-40 flex flex-col items-center justify-center gap-10">
                        <Loader2 className="w-12 h-12 animate-spin text-zinc-50 stroke-[1]" />
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Đang truy xuất bộ sưu tập</p>
                    </div>
                ) : bookmarks.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        {bookmarks.map((doc) => (
                            <Link href={`/document/${doc.slug || doc._id}`} key={doc._id} className="group border border-zinc-100 p-8 rounded-sm hover:border-black transition-all duration-700 bg-white">
                                <div className="flex items-start gap-6">
                                    <div className="w-16 h-20 bg-zinc-50 border border-zinc-50 flex items-center justify-center rounded-sm transition-all group-hover:bg-black group-hover:rotate-6">
                                        <FileText className="w-8 h-8 text-zinc-100 group-hover:text-white stroke-[1.5]" />
                                    </div>
                                    <div className="flex-1 space-y-4">
                                        <h4 className="text-sm font-bold text-black uppercase tracking-tight line-clamp-2 leading-relaxed">{doc.title}</h4>
                                        <div className="flex items-center gap-4 text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                                            <span>{doc.publisher_name || "DocLib Institutional"}</span>
                                            <div className="w-1 h-1 bg-zinc-100 rounded-full" />
                                            <span>{new Date(doc.created_at).toLocaleDateString("vi-VN")}</span>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/10 rounded-sm">
                        <Bookmark className="w-16 h-16 text-zinc-50 mb-10 stroke-[1]" />
                        <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-4">Bộ sưu tập rỗng</h4>
                        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-sm leading-loose">
                            Bắt đầu lưu trữ các thực thể tri thức yêu thích để xây dựng không gian học thuật cá nhân của bạn
                        </p>
                    </div>
                )}
            </div>
          )}

          {activeTab === "history" && (
            <div className="bg-white border border-zinc-100 p-12 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700 rounded-sm">
              <div className="flex items-center justify-between border-b border-zinc-100 pb-10">
                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-black uppercase tracking-tight">Nhật ký mạng lưới</h3>
                  <p className="text-zinc-300 text-[10px] font-bold uppercase tracking-widest">Dòng tiền và giao dịch tri thức hệ thống</p>
                </div>
                <div className="px-6 py-2 bg-zinc-50 border border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest rounded-sm">
                  Lịch sử gần đây
                </div>
              </div>

              {isHistoryLoading ? (
                <div className="py-40 flex flex-col items-center justify-center gap-10">
                  <Loader2 className="w-12 h-12 animate-spin text-zinc-50 stroke-[1]" />
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Đang tải dữ liệu mạng lưới</p>
                </div>
              ) : historyList.length > 0 ? (
                <div className="space-y-6">
                  {historyList.map((tx, idx) => (
                    <div
                      key={idx}
                      className="group p-8 flex items-center justify-between border border-zinc-50 hover:border-black transition-all duration-700 rounded-sm bg-white"
                    >
                      <div className="flex items-center gap-10">
                        <div
                          className={`w-14 h-14 flex items-center justify-center border transition-all duration-700 rounded-sm ${
                            tx.amount > 0 ? "bg-white text-black border-zinc-100 group-hover:bg-black group-hover:text-white" : "bg-black text-white border-black"
                          }`}
                        >
                          {tx.amount > 0 ? <ArrowUpRight className="w-6 h-6" /> : <ArrowDownLeft className="w-6 h-6" />}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-black uppercase tracking-tight group-hover:translate-x-2 transition-transform duration-500">
                            {tx.description || tx.type_display || "Giao dịch tri thức"}
                          </p>
                          <div className="flex items-center gap-4 mt-3">
                            <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">{new Date(tx.created_at).toLocaleString("vi-VN")}</span>
                            <div className="w-1 h-1 bg-zinc-100 rounded-full" />
                            <span className="text-[9px] font-bold text-zinc-200 uppercase tracking-widest">Mã hiệu: TX-{idx + 1000}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-2xl font-bold tracking-tighter ${tx.amount > 0 ? "text-zinc-200" : "text-black"}`}>
                          {tx.amount > 0 ? "+" : ""}
                          {tx.amount.toLocaleString()} <span className="text-[10px] italic">dl</span>
                        </p>
                        <div className="mt-2 flex items-center justify-end gap-2">
                           <div className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
                           <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Hoàn tất</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/10 rounded-sm">
                  <CreditCard className="w-16 h-16 text-zinc-50 mb-10 stroke-[1]" />
                  <h4 className="text-sm font-bold uppercase tracking-widest text-black mb-4">Mạng lưới rỗng</h4>
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-sm leading-loose">
                    Bạn chưa thực hiện giao dịch nạp tiền hoặc chuyển đổi tri thức nào gần đây trên hệ thống.
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
