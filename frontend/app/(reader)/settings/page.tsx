"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import {
  API_URL,
  getToken,
  formatError,
} from "@/app/lib/api";
import {
  Settings,
  Type,
  Shield,
  Bell,
  Globe,
  Lock,
  Eye,
  EyeOff,
  ChevronRight,
  Save,
  Loader2,
  Sparkles,
  Smartphone,
  Moon,
  Sun,
  Monitor,
  PenTool,
  ShieldCheck,
  CreditCard,
  History,
  Zap,
  UserPlus,
  BookOpen,
  Award,
  Clock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Notification } from "@/app/components/NotificationToast";

type TabKey = "appearance" | "privacy" | "notifications" | "account" | "apply_author" | "author" | "moderator" | "admin";

export default function SettingsPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const [visible, setVisible] = useState(false);
  const [activeSection, setActiveSection] = useState<TabKey>("appearance");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Typography Settings
  const [fontFamily, setFontFamily] = useState("Inter");
  const [fontSize, setFontSize] = useState(16);
  const [lineHeight, setLineHeight] = useState(1.8);

  // Privacy Settings
  const [hideActivity, setHideActivity] = useState(false);
  const [hideLibrary, setHideLibrary] = useState(false);

  // Author Application
  const [motivation, setMotivation] = useState("");
  const [portfolio, setPortfolio] = useState("");

  // Author Settings
  const [autoSave, setAutoSave] = useState(true);
  const [defaultVisibility, setDefaultVisibility] = useState("public");
  const [payoutInfo, setPayoutInfo] = useState("");

  // Moderator Settings
  const [modNotifs, setModNotifs] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Admin Settings
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [registrationEnabled, setRegistrationEnabled] = useState(true);

  useEffect(() => {
    if (user) {
      requestAnimationFrame(() => setVisible(true));
      fetchSettings();
      
      // Initialize from user.settings if available
      if (user.settings) {
        setModNotifs(user.settings.mod_notifs ?? true);
        setAutoRefresh(user.settings.auto_refresh ?? false);
        setAutoSave(user.settings.auto_save ?? true);
        setDefaultVisibility(user.settings.default_visibility ?? "public");
      }

      if (user.role === "admin") {
        fetchAdminConfig();
      }
    }
  }, [user]);

  const fetchSettings = async () => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/reader/settings/privacy`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const json = await res.json();
        setHideActivity(json.data?.hide_reading_activity || false);
        setHideLibrary(json.data?.hide_library || false);
      }
    } catch (err) {
      console.error("Lỗi tải cài đặt:", err);
    }
  };

  const fetchAdminConfig = async () => {
    const token = getToken();
    try {
      const maintenanceRes = await fetch(`${API_URL}/admin/maintenance`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (maintenanceRes.ok) {
        const json = await maintenanceRes.json();
        setMaintenanceMode(json.data?.enabled || false);
      }

      const configRes = await fetch(`${API_URL}/admin/config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (configRes.ok) {
        const json = await configRes.json();
        setRegistrationEnabled(json.data?.registration_enabled ?? true);
      }
    } catch (err) {
      console.error("Lỗi tải cấu hình quản trị viên:", err);
    }
  };

  const updateGeneralSettings = async (newSettings: any) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_URL}/reader/settings`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ settings: newSettings }),
      });
      if (res.ok) {
        refreshUser?.();
        return true;
      }
    } catch (err) {
      console.error("Lỗi cập nhật cài đặt:", err);
    }
    return false;
  };

  const handleToggleMaintenance = async () => {
    const token = getToken();
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/maintenance`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled: !maintenanceMode, message: "Hệ thống đang bảo trì." }),
      });
      if (res.ok) {
        setMaintenanceMode(!maintenanceMode);
        setNotification({ type: "success", text: `Đã ${!maintenanceMode ? "bật" : "tắt"} chế độ bảo trì.` });
      }
    } catch (err) {
      setNotification({ type: "error", text: "Không thể cập nhật chế độ bảo trì." });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRegistration = async () => {
    const token = getToken();
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/config`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ registration_enabled: !registrationEnabled }),
      });
      if (res.ok) {
        setRegistrationEnabled(!registrationEnabled);
        setNotification({ type: "success", text: `Đã ${!registrationEnabled ? "mở" : "đóng"} cổng đăng ký.` });
      }
    } catch (err) {
      setNotification({ type: "error", text: "Không thể cập nhật cấu hình đăng ký." });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTypography = async () => {
    setLoading(true);
    setNotification(null);
    try {
      const res = await fetch(`${API_URL}/reader/settings/typography`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${getToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          font_family: fontFamily,
          font_size: fontSize,
          line_height: lineHeight,
        }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã cập nhật tùy chỉnh hiển thị thành công." });
      }
    } catch (err) {
      setNotification({ type: "error", text: "Lỗi hệ thống khi cập nhật." });
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrivacy = async () => {
    setLoading(true);
    setNotification(null);
    try {
      const res = await fetch(`${API_URL}/reader/settings/privacy`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${getToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          hide_reading_activity: hideActivity,
          hide_library: hideLibrary,
        }),
      });
      if (res.ok) {
        setNotification({ type: "success", text: "Đã cập nhật cài đặt quyền riêng tư." });
      }
    } catch (err) {
      setNotification({ type: "error", text: "Lỗi hệ thống khi cập nhật." });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation) {
        setNotification({ type: "error", text: "Vui lòng nhập lý do ứng tuyển." });
        return;
    }
    setLoading(true);
    try {
        const res = await fetch(`${API_URL}/reader/apply-author`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${getToken()}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ motivation, portfolio }),
        });
        if (res.ok) {
            setNotification({ type: "success", text: "Đã gửi đơn ứng tuyển thành công. Vui lòng chờ phê duyệt." });
            setMotivation("");
            setPortfolio("");
            refreshUser?.();
        } else {
            const err = await res.json();
            setNotification({ type: "error", text: err.detail || "Không thể gửi đơn ứng tuyển." });
        }
    } catch (err) {
        setNotification({ type: "error", text: "Lỗi kết nối máy chủ." });
    } finally {
        setLoading(false);
    }
  };

  const CustomSwitch = ({ active, onToggle, color = "black" }: { active: boolean, onToggle: () => void, color?: string }) => (
    <button 
      onClick={onToggle}
      className={`w-16 h-9 transition-all relative rounded-none shrink-0 border border-zinc-100 ${active ? (color === "red" ? "bg-red-600 border-red-600" : "bg-black border-black") : "bg-zinc-200"}`}
    >
      <div className={`absolute top-1 w-7 h-7 bg-white transition-all shadow-sm ${active ? "left-8" : "left-1"}`} />
    </button>
  );

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-200" />
      </div>
    );
  }

  const sections = [
    { id: "appearance", label: "Hiển thị & Kiểu chữ", icon: Type, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "privacy", label: "Quyền riêng tư", icon: Shield, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "notifications", label: "Thông báo", icon: Bell, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "account", label: "Tài khoản & Bảo mật", icon: Lock, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    ...(user?.role === "reader" || (user?.author_status === "pending" || user?.author_status === "none") ? [{ id: "apply_author", label: "Đăng ký Tác giả", icon: UserPlus, roles: ["reader"] }] : []),
    { id: "author", label: "Cấu hình Tác giả", icon: PenTool, roles: ["author", "admin"] },
    { id: "moderator", label: "Kiểm duyệt viên", icon: ShieldCheck, roles: ["moderator", "admin"] },
    { id: "admin", label: "Quản trị viên", icon: Zap, roles: ["admin"] },
  ].filter(s => !user || s.roles.includes(user.role));

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      {notification && (
        <div className="fixed top-24 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {/* Header */}
      <header 
        className="mb-10 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)" }}
      >
        <div>
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black mb-3">
            Cài đặt
          </h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Preferences & Control Center <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
      </header>

      <div className="grid lg:grid-cols-12 gap-12">
        {/* Navigation Sidebar */}
        <aside 
          className="lg:col-span-4 space-y-8 transition-all duration-700 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="text-[11px] font-bold text-black uppercase tracking-[0.3em] px-1 flex items-center gap-2">
                <Settings className="w-4 h-4 text-zinc-300" /> Tùy chỉnh cá nhân
            </div>
            <nav className="flex flex-col gap-1">
                {sections.map((section) => (
                    <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id as TabKey)}
                        className={`flex items-center justify-between px-6 py-5 text-[11px] font-bold uppercase tracking-widest transition-all border ${
                            activeSection === section.id
                            ? "bg-black text-white border-black shadow-lg shadow-black/5"
                            : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                        }`}
                    >
                        <div className="flex items-center gap-4">
                            <section.icon className="w-4.5 h-4.5" /> {section.label}
                        </div>
                        <ChevronRight className={`w-3.5 h-3.5 transition-transform ${activeSection === section.id ? "rotate-90" : ""}`} />
                    </button>
                ))}
            </nav>
          </div>

          <div className="p-8 border border-zinc-100 bg-zinc-50/50 space-y-4">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest mb-2">Quyền hạn tài khoản</div>
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-black flex items-center justify-center text-white text-[10px] font-bold uppercase italic">
                    {user?.role?.slice(0, 3)}
                </div>
                <div className="flex flex-col">
                    <span className="text-xs font-bold text-black uppercase">{user?.role}</span>
                    <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest italic">Identity Verified</span>
                </div>
             </div>
          </div>
        </aside>

        {/* Content Area */}
        <main 
          className="lg:col-span-8 transition-all duration-700 delay-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="bg-white border border-zinc-100 p-10 lg:p-16 min-h-[600px] animate-in fade-in slide-in-from-bottom-4 duration-500 shadow-2xl shadow-black/[0.02]">
            {activeSection === "appearance" && (
              <div className="space-y-12">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold tracking-tighter">Hiển thị & Kiểu chữ</h2>
                  <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tùy biến môi trường tiếp nhận tri thức</p>
                </div>

                <div className="space-y-12">
                  <div className="space-y-6">
                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Hệ phông chữ ưu tiên</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {["Inter", "Roboto", "Outfit", "Noto Sans", "Source Sans"].map((font) => (
                        <button
                          key={font}
                          onClick={() => setFontFamily(font)}
                          className={`h-16 border text-xs font-bold transition-all flex items-center justify-center ${
                            fontFamily === font ? "bg-black text-white border-black shadow-lg" : "bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black"
                          }`}
                          style={{ fontFamily: font }}
                        >
                          {font}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-10">
                    <div className="space-y-4">
                      <label className="text-[11px] font-bold text-black uppercase tracking-widest">Cỡ chữ văn bản (px)</label>
                      <input
                        type="number"
                        value={fontSize}
                        onChange={(e) => setFontSize(parseInt(e.target.value))}
                        className="w-full h-14 px-6 border border-zinc-100 focus:border-black bg-zinc-50/30 text-sm font-bold transition-all outline-none"
                      />
                    </div>
                    <div className="space-y-4">
                      <label className="text-[11px] font-bold text-black uppercase tracking-widest">Độ giãn dòng</label>
                      <input
                        type="number"
                        step="0.1"
                        value={lineHeight}
                        onChange={(e) => setLineHeight(parseFloat(e.target.value))}
                        className="w-full h-14 px-6 border border-zinc-100 focus:border-black bg-zinc-50/30 text-sm font-bold transition-all outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-12 border-t border-zinc-50 flex justify-end">
                   <Button 
                    onClick={handleSaveTypography}
                    disabled={loading}
                    className="h-14 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-none hover:bg-zinc-800 transition-all active:scale-95 shadow-xl shadow-black/10"
                   >
                     {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Lưu tùy chỉnh"}
                   </Button>
                </div>
              </div>
            )}

            {activeSection === "apply_author" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold tracking-tighter">Đăng ký Tác giả</h2>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Trở thành một phần của cộng đồng tri thức chuyên sâu</p>
                    </div>

                    {user?.author_status === "pending" ? (
                        <div className="py-20 text-center space-y-6">
                            <div className="w-20 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center mx-auto">
                                <Clock className="w-8 h-8 text-zinc-200" />
                            </div>
                            <div className="space-y-2">
                                <h4 className="text-xl font-bold tracking-tight">Đang chờ phê duyệt</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm mx-auto leading-relaxed">
                                    Hồ sơ của bạn đang được đội ngũ **Kiểm duyệt viên** đánh giá. Quá trình này thường mất từ 24-48h.
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            <div className="p-10 border border-zinc-100 bg-zinc-50/30 space-y-6">
                                <div className="flex items-center gap-4 text-black mb-4">
                                    <Award className="w-6 h-6" />
                                    <h4 className="text-sm font-bold uppercase tracking-widest">Lợi ích khi trở thành Tác giả</h4>
                                </div>
                                <ul className="space-y-4">
                                    {[
                                        "Sở hữu trang hồ sơ chuyên nghiệp với huy hiệu Tác giả.",
                                        "Xuất bản và quản lý kho tri thức của riêng bạn.",
                                        "Nhận nhuận bút từ lượt xem và đóng góp của độc giả.",
                                        "Tham gia cộng đồng sáng tạo và phản biện chuyên sâu."
                                    ].map((item, i) => (
                                        <li key={i} className="flex items-start gap-4 text-xs font-medium text-zinc-500">
                                            <Sparkles className="w-3.5 h-3.5 text-black shrink-0" />
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-4">
                                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Mục tiêu sáng tác & Giới thiệu bản thân</label>
                                    <textarea 
                                        value={motivation}
                                        onChange={(e) => setMotivation(e.target.value)}
                                        className="w-full min-h-[160px] p-6 border border-zinc-100 focus:border-black bg-white text-sm font-medium transition-all outline-none leading-relaxed"
                                        placeholder=""
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Portfolio / Link tham khảo (Nếu có)</label>
                                    <input 
                                        type="text"
                                        value={portfolio}
                                        onChange={(e) => setPortfolio(e.target.value)}
                                        className="w-full h-14 px-6 border border-zinc-100 focus:border-black bg-white text-sm font-bold transition-all outline-none"
                                        placeholder=""
                                    />
                                </div>
                            </div>

                            <div className="pt-8 border-t border-zinc-50">
                                <Button 
                                    onClick={handleApplyAuthor}
                                    disabled={loading}
                                    className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-none hover:bg-zinc-800 transition-all shadow-xl shadow-black/10 flex items-center gap-4"
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <UserPlus className="w-5 h-5" />}
                                    Gửi đơn ứng tuyển Tác giả
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {activeSection === "privacy" && (
              <div className="space-y-12">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold tracking-tighter">Quyền riêng tư</h2>
                  <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Quản lý tính minh bạch của tài khoản</p>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between p-10 border border-zinc-100 bg-zinc-50/30 group hover:border-black transition-all duration-500">
                    <div className="space-y-2">
                       <h4 className="text-base font-bold tracking-tight">Chế độ đọc ẩn danh</h4>
                       <p className="text-[11px] font-medium text-zinc-400 max-w-sm leading-relaxed">Không công khai lịch sử và tài liệu bạn đang tiếp nhận trên các luồng xã hội.</p>
                    </div>
                    <CustomSwitch active={hideActivity} onToggle={() => setHideActivity(!hideActivity)} />
                  </div>

                  <div className="flex items-center justify-between p-10 border border-zinc-100 bg-zinc-50/30 group hover:border-black transition-all duration-500">
                    <div className="space-y-2">
                       <h4 className="text-base font-bold tracking-tight">Thư viện nội bộ</h4>
                       <p className="text-[11px] font-medium text-zinc-400 max-w-sm leading-relaxed">Giới hạn quyền truy cập bộ sưu tập cá nhân, chỉ mình bạn có quyền xem.</p>
                    </div>
                    <CustomSwitch active={hideLibrary} onToggle={() => setHideLibrary(!hideLibrary)} />
                  </div>
                </div>

                <div className="pt-12 border-t border-zinc-50 flex justify-end">
                   <Button 
                    onClick={handleSavePrivacy}
                    disabled={loading}
                    className="h-14 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-none hover:bg-zinc-800 transition-all active:scale-95 shadow-xl shadow-black/10"
                   >
                     {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Cập nhật riêng tư"}
                   </Button>
                </div>
              </div>
            )}

            {activeSection === "author" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold tracking-tighter">Cấu hình Tác giả</h2>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tối ưu hóa quy trình sáng tác tri thức</p>
                    </div>

                    <div className="space-y-8">
                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all">
                            <div className="space-y-2">
                                <h4 className="text-base font-bold tracking-tight">Tự động lưu bản nháp</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm">Hệ thống tự động sao lưu nội dung mỗi 30 giây trong IDE.</p>
                            </div>
                            <CustomSwitch 
                                active={autoSave} 
                                onToggle={async () => {
                                    const success = await updateGeneralSettings({ auto_save: !autoSave });
                                    if (success) setAutoSave(!autoSave);
                                }} 
                            />
                        </div>

                        <div className="space-y-4">
                            <label className="text-[11px] font-bold text-black uppercase tracking-widest">Chế độ hiển thị mặc định</label>
                            <div className="grid grid-cols-2 gap-4">
                                {["public", "private"].map((mode) => (
                                    <button
                                        key={mode}
                                        onClick={async () => {
                                            const success = await updateGeneralSettings({ default_visibility: mode });
                                            if (success) setDefaultVisibility(mode);
                                        }}
                                        className={`h-14 border text-[11px] font-bold uppercase tracking-widest transition-all ${
                                            defaultVisibility === mode ? "bg-black text-white border-black" : "bg-white text-zinc-400 border-zinc-100 hover:border-black hover:text-black"
                                        }`}
                                    >
                                        {mode === "public" ? "Công khai" : "Riêng tư"}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <label className="text-[11px] font-bold text-black uppercase tracking-widest">Thông tin thụ hưởng (Bank Info)</label>
                            <textarea
                                value={payoutInfo}
                                onChange={(e) => setPayoutInfo(e.target.value)}
                                placeholder=""
                                className="w-full min-h-[120px] p-6 border border-zinc-100 focus:border-black bg-zinc-50/30 text-sm font-medium transition-all outline-none leading-relaxed"
                            />
                        </div>
                    </div>

                    <div className="pt-12 border-t border-zinc-50 flex justify-end">
                        <Button className="h-14 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-none shadow-xl shadow-black/10">Lưu cấu hình sáng tác</Button>
                    </div>
                </div>
            )}

            {activeSection === "moderator" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold tracking-tighter">Kiểm duyệt viên</h2>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Quản lý hiệu suất kiểm soát nội dung</p>
                    </div>

                    <div className="space-y-8">
                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all">
                            <div className="space-y-2">
                                <h4 className="text-base font-bold tracking-tight">Thông báo báo cáo vi phạm</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm">Nhận thông báo ngay lập tức khi có người dùng gửi báo cáo mới.</p>
                            </div>
                            <CustomSwitch 
                                active={modNotifs} 
                                onToggle={async () => {
                                    const success = await updateGeneralSettings({ mod_notifs: !modNotifs });
                                    if (success) {
                                        setModNotifs(!modNotifs);
                                        setNotification({ type: "success", text: `Đã ${!modNotifs ? "bật" : "tắt"} thông báo báo cáo.` });
                                    }
                                }} 
                            />
                        </div>

                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all">
                            <div className="space-y-2">
                                <h4 className="text-base font-bold tracking-tight">Tự động làm mới hàng chờ</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm">Cập nhật danh sách tài liệu chờ duyệt mỗi 60 giây.</p>
                            </div>
                            <CustomSwitch 
                                active={autoRefresh} 
                                onToggle={async () => {
                                    const success = await updateGeneralSettings({ auto_refresh: !autoRefresh });
                                    if (success) {
                                        setAutoRefresh(!autoRefresh);
                                        setNotification({ type: "success", text: `Đã ${!autoRefresh ? "bật" : "tắt"} tự động làm mới.` });
                                    }
                                }} 
                            />
                        </div>
                    </div>
                </div>
            )}

            {activeSection === "admin" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold tracking-tighter">Quản trị viên</h2>
                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Thiết lập vận hành toàn cầu</p>
                    </div>

                    <div className="grid gap-6">
                        <div className="p-10 border border-zinc-100 bg-zinc-50/50 flex items-center justify-between group hover:border-black transition-all duration-500">
                            <div className="space-y-2">
                                <h4 className="text-base font-bold tracking-tight text-red-600">Chế độ bảo trì (Maintenance)</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm">Chặn tất cả các thao tác ghi dữ liệu từ phía người dùng.</p>
                            </div>
                            <CustomSwitch active={maintenanceMode} onToggle={handleToggleMaintenance} color="red" />
                        </div>

                        <div className="p-10 border border-zinc-100 bg-white flex items-center justify-between group hover:border-black transition-all duration-500">
                            <div className="space-y-2">
                                <h4 className="text-base font-bold tracking-tight">Đăng ký người dùng mới</h4>
                                <p className="text-[11px] font-medium text-zinc-400 max-w-sm">Mở hoặc đóng cổng đăng ký tài khoản mới.</p>
                            </div>
                            <CustomSwitch active={registrationEnabled} onToggle={handleToggleRegistration} />
                        </div>
                    </div>
                </div>
            )}

            {activeSection === "notifications" && (
              <div className="space-y-12 flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                <div className="w-20 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center mb-6">
                  <Bell className="w-8 h-8 text-zinc-200 stroke-[1]" />
                </div>
                <div className="space-y-2">
                   <h3 className="text-xl font-bold tracking-tighter">Trung tâm thông báo</h3>
                   <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest max-w-xs leading-relaxed">
                     Hệ thống thông báo đẩy đang được đồng bộ hóa.
                   </p>
                </div>
              </div>
            )}

            {activeSection === "account" && (
              <div className="space-y-12">
                <div className="space-y-2">
                  <h2 className="text-3xl font-bold tracking-tighter">Tài khoản & Bảo mật</h2>
                  <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Lớp phòng thủ định danh cuối cùng</p>
                </div>

                <div className="space-y-6">
                   <div className="p-10 border border-zinc-100 flex items-center justify-between hover:border-black transition-all duration-500">
                      <div className="space-y-1">
                         <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Trạng thái xác minh</span>
                         <div className="text-sm font-bold flex items-center gap-2">
                            <div className="w-2 h-2 bg-black" /> Tài khoản đã định danh cấp cao
                         </div>
                      </div>
                      <Button variant="outline" className="text-[10px] font-bold uppercase tracking-widest border-zinc-100 rounded-none h-14 px-8 hover:border-black transition-all">Đổi mật khẩu</Button>
                   </div>

                   <div className="p-10 border border-zinc-100 flex items-center justify-between hover:border-black transition-all duration-500">
                      <div className="space-y-1">
                         <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">Địa chỉ Email</span>
                         <div className="text-sm font-bold">{user?.email || "Chưa cập nhật"}</div>
                      </div>
                      <Button variant="outline" className="text-[10px] font-bold uppercase tracking-widest border-zinc-100 rounded-none h-14 px-8 hover:border-black transition-all">Cập nhật</Button>
                   </div>
                </div>

                <div className="pt-20 border-t border-zinc-50">
                   <p className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest leading-relaxed max-w-2xl">
                     * Bạn đang quản lý các thiết lập bảo mật cấp cao. Mọi thay đổi quan trọng sẽ yêu cầu xác thực 2 lớp qua email đã đăng ký.
                   </p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
