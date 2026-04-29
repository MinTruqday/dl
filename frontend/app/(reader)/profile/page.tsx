"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  API_URL,
  getToken,
  updateProfileAPI,
  depositDLAPI,
  getDetailedHistoryAPI,
  applyAuthorAPI,
} from "@/app/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  ArrowUpRight,
  ArrowDownLeft,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";

export default function ProfilePage() {
  const { user, isLoading, logoutState } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [depositAmount, setDepositAmount] = useState("");
  const [isDepositing, setIsDepositing] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [visible, setVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<"info" | "history">("info");
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
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

  useEffect(() => {
    if (activeTab === "history") {
      fetchHistory();
    }
  }, [activeTab]);

  const fetchHistory = async () => {
    setIsHistoryLoading(true);
    try {
      const data = await getDetailedHistoryAPI();
      setHistoryList(data || []);
    } catch (err: any) {
      console.error("Lỗi tải lịch sử:", err);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage({ type: "", text: "" });
    try {
      const res = await updateProfileAPI({ full_name: fullName, bio, avatar_url: avatarUrl });
      if (res && res.status === 200) {
        setMessage({ type: "success", text: "Cập nhật hồ sơ thành công." });
        setTimeout(() => window.location.reload(), 1500);
      } else {
        setMessage({ type: "error", text: "Cập nhật không thành công, vui lòng thử lại." });
      }
    } catch (err: any) {
      console.error("Lỗi cập nhật hồ sơ:", err);
      setMessage({ type: "error", text: "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeposit = async () => {
    const amount = parseInt(depositAmount);
    if (!amount || amount < 10000) {
      setMessage({ type: "error", text: "Số tiền nạp tối thiểu là 10.000 VNĐ." });
      return;
    }
    setIsDepositing(true);
    try {
      const res = await depositDLAPI(amount);
      if (res.data?.payment_url) {
        window.location.href = res.data.payment_url;
      } else {
        setMessage({ type: "error", text: "Không thể khởi tạo cổng thanh toán." });
      }
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Lỗi nạp tiền." });
    } finally {
      setIsDepositing(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation.trim()) {
      setMessage({ type: "error", text: "Vui lòng nhập lý do ứng tuyển." });
      return;
    }
    setIsApplying(true);
    try {
      const res = await applyAuthorAPI(motivation);
      setMessage({ type: "success", text: res.message || "Đã gửi đơn ứng tuyển." });
      setMotivation("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Lỗi gửi đơn ứng tuyển." });
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
      const res = await fetch(`${API_URL}/social/upload-media`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: formData,
      });
      const data = await res.json();
      if (res.ok && data.url) {
        setAvatarUrl(`${API_URL}${data.url}`);
        setMessage({ type: "success", text: "Tải ảnh lên thành công. Hãy nhấn Lưu để hoàn tất." });
      } else {
        setMessage({ type: "error", text: "Không thể tải ảnh lên." });
      }
    } catch {
      setMessage({ type: "error", text: "Lỗi kết nối khi tải ảnh." });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-10 font-sans text-black selection:bg-black selection:text-white">
      {/* Premium Header */}
      <div 
        className="mb-10 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div>
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
            Hồ sơ cá nhân
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            User Profile & Identity <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
        <Button
          onClick={logoutState}
          className="bg-zinc-50 text-black hover:bg-zinc-100 border border-zinc-100 flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest h-12 px-8 transition-all active:scale-95 rounded-none"
        >
          <LogOut className="w-4 h-4" />
          Đăng xuất tài khoản
        </Button>
      </div>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Sidebar Controls */}
        <aside 
          className="lg:col-span-4 space-y-10 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {/* Identity Card */}
          <div className="border border-zinc-100 bg-white p-8">
            <div className="flex flex-col items-center gap-8">
              <div className="relative group">
                <div className="w-44 h-44 border border-zinc-100 overflow-hidden bg-zinc-50 grayscale group-hover:grayscale-0 transition-all duration-700">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-200">
                      <User className="w-16 h-16 stroke-[1]" />
                    </div>
                  )}
                </div>
                <label className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col items-center justify-center text-white cursor-pointer backdrop-blur-[2px]">
                  <Camera className="w-6 h-6 mb-2" />
                  <span className="text-[10px] font-bold uppercase tracking-widest">Đổi ảnh</span>
                  <input type="file" className="hidden" accept="image/*" onChange={handleAvatarUpload} />
                </label>
              </div>
              
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-black tracking-tighter flex items-center justify-center gap-2">
                  {user.full_name || user.display_name}
                  {user.role === "author" && <BadgeCheck className="w-6 h-6 text-black" />}
                </h2>
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-50 border border-zinc-100 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                  @{user.slug || user._id}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Menu */}
          <div className="space-y-4">
            <div className="text-[11px] font-bold text-black uppercase tracking-widest px-1">Danh mục quản lý</div>
            <nav className="flex flex-col gap-1">
              <button
                onClick={() => setActiveTab("info")}
                className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                  activeTab === "info"
                    ? "bg-black text-white border-black"
                    : "bg-white text-zinc-400 hover:bg-zinc-50 hover:text-black border-zinc-100"
                }`}
              >
                <div className="flex items-center gap-3">
                  <User className="w-4 h-4" /> Thông tin tài khoản
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === "info" ? "rotate-90" : ""}`} />
              </button>
              <button
                onClick={() => setActiveTab("history")}
                className={`flex items-center justify-between px-6 py-4 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                  activeTab === "history"
                    ? "bg-black text-white border-black"
                    : "bg-white text-zinc-400 hover:bg-zinc-50 hover:text-black border-zinc-100"
                }`}
              >
                <div className="flex items-center gap-3">
                  <History className="w-4 h-4" /> Lịch sử giao dịch
                </div>
                <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === "history" ? "rotate-90" : ""}`} />
              </button>
            </nav>
          </div>

          {/* Wallet Widget */}
          <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-8">
            <div className="flex items-center justify-between border-b border-zinc-200 pb-6">
              <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">Số dư ví DL</span>
              <span className="text-3xl font-bold text-black tracking-tighter">{user.wallet_balance?.toLocaleString() || 0} <span className="text-zinc-300 text-sm italic">dl</span></span>
            </div>
            <div className="space-y-4">
              <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                <CreditCard className="w-3.5 h-3.5" /> Nạp thêm tri thức (VNĐ)
              </label>
              <div className="flex flex-col gap-3">
                <Input
                  type="number"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  placeholder=""
                  className="h-14 bg-white border-zinc-100 focus-visible:ring-black rounded-none text-sm font-medium transition-all"
                />
                <Button
                  onClick={handleDeposit}
                  disabled={isDepositing}
                  className="h-14 w-full bg-black text-white hover:bg-zinc-800 text-[11px] font-bold uppercase tracking-widest transition-all active:scale-95 rounded-none"
                >
                  {isDepositing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận nạp tiền"}
                </Button>
              </div>
            </div>
          </div>

          {/* Author Application Widget - For Readers only */}
          {user.role === "reader" && (
            <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-6">
              <div className="flex items-center gap-3 text-black">
                 <Sparkles className="w-5 h-5" />
                 <span className="text-[11px] font-bold uppercase tracking-widest">Thăng cấp Tác giả</span>
              </div>
              <p className="text-[10px] font-medium text-zinc-400 leading-relaxed italic">
                Trở thành người kiến tạo tri thức và nhận doanh thu từ tác phẩm của bạn.
              </p>
              <div className="space-y-4">
                <textarea
                  value={motivation}
                  onChange={(e) => setMotivation(e.target.value)}
                  placeholder=""
                  className="w-full min-h-[100px] p-4 text-[11px] border border-zinc-100 bg-white focus:outline-none focus:border-black transition-all font-medium"
                />
                <Button
                  onClick={handleApplyAuthor}
                  disabled={isApplying}
                  className="h-12 w-full bg-black text-white hover:bg-zinc-800 text-[10px] font-bold uppercase tracking-widest transition-all active:scale-95 rounded-none"
                >
                  {isApplying ? <Loader2 className="w-4 h-4 animate-spin" /> : "Gửi đơn ứng tuyển"}
                </Button>
              </div>
            </div>
          )}
        </aside>

        {/* Main Content Area */}
        <main 
          className="lg:col-span-8 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          {activeTab === "info" ? (
            <div className="bg-white border border-zinc-100 p-10 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="space-y-2">
                <h3 className="text-2xl font-bold text-black tracking-tighter">Chi tiết định danh</h3>
                <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-widest">Cập nhật thông tin cá nhân trên nền tảng</p>
              </div>

              {message.text && (
                <div className={`p-5 border text-[11px] font-bold uppercase tracking-widest transition-all duration-300 ${
                  message.type === "success" ? "bg-zinc-50 border-black text-black" : "bg-white border-zinc-200 text-zinc-400"
                }`}>
                  {message.text}
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-10">
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                    <Mail className="w-3.5 h-3.5" /> Địa chỉ Email
                  </label>
                  <Input value={user.email} disabled className="h-14 bg-zinc-50 border-zinc-100 text-zinc-300 font-bold cursor-not-allowed rounded-none" />
                  <p className="text-[9px] text-zinc-300 font-bold uppercase italic">* Thông tin bảo mật không thể thay đổi</p>
                </div>
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Họ và tên hiển thị</label>
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder=""
                    className="h-14 border-zinc-100 focus-visible:ring-black font-bold rounded-none transition-all"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                  <LinkIcon className="w-3.5 h-3.5" /> Tiểu sử tri thức (Bio)
                </label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder=""
                  className="w-full min-h-[220px] p-8 text-sm border border-zinc-100 rounded-none focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all duration-300 font-medium bg-zinc-50/30"
                />
              </div>

              <div className="flex justify-end pt-8 border-t border-zinc-50">
                <Button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="bg-black text-white hover:bg-zinc-800 px-12 h-16 flex items-center gap-4 transition-all active:scale-95 rounded-none shadow-xl shadow-black/5"
                >
                  {isSaving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                  <span className="text-[11px] font-bold uppercase tracking-[0.2em]">Cập nhật thông tin</span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-zinc-100 p-10 space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between border-b border-zinc-100 pb-8">
                <div className="space-y-1">
                  <h3 className="text-2xl font-bold text-black tracking-tighter">Nhật ký tài chính</h3>
                  <p className="text-zinc-400 text-[11px] font-bold uppercase tracking-widest">Dòng tiền và giao dịch tri thức</p>
                </div>
                <div className="px-4 py-2 bg-zinc-50 border border-zinc-100 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                  Gần đây nhất
                </div>
              </div>

              {isHistoryLoading ? (
                <div className="py-32 flex flex-col items-center justify-center gap-4">
                  <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">Đang tải dữ liệu</p>
                </div>
              ) : historyList.length > 0 ? (
                <div className="space-y-4">
                  {historyList.map((tx, idx) => (
                    <div
                      key={idx}
                      className="group p-6 flex items-center justify-between border border-zinc-50 hover:border-zinc-200 hover:bg-zinc-50/50 transition-all duration-500"
                    >
                      <div className="flex items-center gap-8">
                        <div
                          className={`w-14 h-14 flex items-center justify-center border transition-all duration-500 ${
                            tx.amount > 0 ? "bg-white text-black border-zinc-100 group-hover:bg-black group-hover:text-white group-hover:border-black" : "bg-black text-white border-black"
                          }`}
                        >
                          {tx.amount > 0 ? <ArrowUpRight className="w-6 h-6" /> : <ArrowDownLeft className="w-6 h-6" />}
                        </div>
                        <div>
                          <p className="text-[15px] font-bold text-black tracking-tight group-hover:translate-x-1 transition-transform">
                            {tx.description || tx.type_display || "Giao dịch hệ thống"}
                          </p>
                          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mt-1.5 flex items-center gap-2">
                            <History className="w-3 h-3" /> {new Date(tx.created_at).toLocaleString("vi-VN")}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-xl font-bold tracking-tighter ${tx.amount > 0 ? "text-zinc-400" : "text-black"}`}>
                          {tx.amount > 0 ? "+" : ""}
                          {tx.amount.toLocaleString()} <span className="text-[10px] italic">dl</span>
                        </p>
                        <div className="mt-1 flex items-center justify-end gap-1.5">
                          <div className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
                          <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Hoàn tất</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-40 flex flex-col items-center justify-center border border-dashed border-zinc-100 bg-zinc-50/30">
                  <CreditCard className="w-14 h-14 text-zinc-100 mb-8 stroke-[1]" />
                  <h4 className="text-lg font-bold tracking-tighter text-black mb-2">Chưa có giao dịch</h4>
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest text-center max-w-xs leading-loose">
                    Bạn chưa thực hiện giao dịch nạp tiền hoặc mua tài liệu nào gần đây.
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
