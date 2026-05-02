"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  getPrivacySettingsAPI,
  updatePrivacySettingsAPI,
  updateTypographyAPI,
  updateGeneralSettingsAPI,
} from "@/services/settings.service";
import { applyAuthorAPI } from "@/services/settings.service";
import { getMaintenanceModeAPI, getAdminConfigAPI, toggleMaintenanceModeAPI, updateAdminConfigAPI } from "@/services/administration.service";
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
  Clock,
  ArrowRight,
  AlertCircle
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";

type TabKey = "appearance" | "privacy" | "notifications" | "account" | "apply_author" | "author" | "moderator" | "admin";

export default function SettingsPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const [visible, setVisible] = useState(false);
  const [activeSection, setActiveSection] = useState<TabKey>("appearance");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [fontFamily, setFontFamily] = useState("Inter");
  const [fontSize, setFontSize] = useState(16);
  const [lineHeight, setLineHeight] = useState(1.8);

  const [hideActivity, setHideActivity] = useState(false);
  const [hideLibrary, setHideLibrary] = useState(false);

  const [motivation, setMotivation] = useState("");
  const [portfolio, setPortfolio] = useState("");

  const [autoSave, setAutoSave] = useState(true);
  const [defaultVisibility, setDefaultVisibility] = useState("public");
  const [payoutInfo, setPayoutInfo] = useState("");

  const [modNotifs, setModNotifs] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [registrationEnabled, setRegistrationEnabled] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const privacyRes = await getPrivacySettingsAPI();
      setHideActivity(privacyRes.data?.hide_reading_activity || false);
      setHideLibrary(privacyRes.data?.hide_library || false);

      if (user?.role === "admin") {
        const maintData = await getMaintenanceModeAPI();
        setMaintenanceMode(maintData.data?.enabled || maintData.enabled || false);
        
        const configData = await getAdminConfigAPI();
        setRegistrationEnabled(configData.data?.registration_enabled ?? true);
      }

      if (user?.settings) {
        setModNotifs(user.settings.mod_notifs ?? true);
        setAutoRefresh(user.settings.auto_refresh ?? false);
        setAutoSave(user.settings.auto_save ?? true);
        setDefaultVisibility(user.settings.default_visibility ?? "public");
      }
    } catch (err: any) {
      showToast("Không thể đồng bộ dữ liệu cài đặt.", "error");
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      requestAnimationFrame(() => setVisible(true));
      fetchData();
    }
  }, [user, fetchData]);

  const handleUpdateGeneral = async (newSettings: any) => {
    try {
      await updateGeneralSettingsAPI(newSettings);
      refreshUser?.();
      return true;
    } catch (err: any) {
      showToast("Không thể cập nhật cấu hình cá nhân.", "error");
      return false;
    }
  };

  const handleSaveTypography = async () => {
    setLoading(true);
    try {
      await updateTypographyAPI({
        font_family: fontFamily,
        font_size: fontSize,
        line_height: lineHeight,
      });
      showToast("Đã lưu tùy chỉnh hiển thị.", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật hiển thị.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrivacy = async () => {
    setLoading(true);
    try {
      await updatePrivacySettingsAPI({
        hide_reading_activity: hideActivity,
        hide_library: hideLibrary,
      });
      showToast("Đã cập nhật quyền riêng tư.", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật riêng tư.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation) {
        showToast("Vui lòng nhập lý do ứng tuyển.", "error");
        return;
    }
    setLoading(true);
    try {
        await applyAuthorAPI(motivation);
        showToast("Đã gửi đơn ứng tuyển thành công. Vui lòng chờ phê duyệt.", "success");
        setMotivation("");
        setPortfolio("");
        refreshUser?.();
    } catch (err: any) {
        showToast(err.message || "Không thể gửi đơn ứng tuyển.", "error");
    } finally {
        setLoading(false);
    }
  };

  const handleToggleMaintenance = async () => {
    setLoading(true);
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setMaintenanceMode(!maintenanceMode);
      showToast(!maintenanceMode ? "Đã kích hoạt bảo trì." : "Đã tắt bảo trì.", "success");
    } catch (err: any) {
      showToast("Lỗi thao tác bảo trì hệ thống.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRegistration = async () => {
    setLoading(true);
    try {
      await updateAdminConfigAPI({ registration_enabled: !registrationEnabled });
      setRegistrationEnabled(!registrationEnabled);
      showToast(!registrationEnabled ? "Đã mở đăng ký." : "Đã đóng đăng ký.", "success");
    } catch (err: any) {
      showToast("Lỗi cập nhật cấu hình đăng ký.", "error");
    } finally {
      setLoading(false);
    }
  };

  const CustomSwitch = ({ active, onToggle, color = "black" }: { active: boolean, onToggle: () => void, color?: string }) => (
    <button 
      onClick={onToggle}
      className={`w-16 h-9 transition-all relative shrink-0 rounded-sm border ${active ? (color === "red" ? "bg-red-600 border-red-600" : "bg-black border-black") : "bg-zinc-100 border-zinc-200"}`}
    >
      <div className={`absolute top-1 w-7 h-7 bg-white transition-all rounded-sm ${active ? "left-8" : "left-1"}`} />
    </button>
  );

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-10 h-10 animate-spin text-zinc-100" />
      </div>
    );
  }

  const sections = [
    { id: "appearance", label: "Hiển thị & Kiểu chữ", icon: Type, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "privacy", label: "Quyền riêng tư", icon: Shield, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "notifications", label: "Thông báo", icon: Bell, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "account", label: "Tài khoản & Bảo mật", icon: Lock, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    ...(user?.role === "reader" && user?.author_status !== "pending" && user?.author_status !== "approved" ? [{ id: "apply_author", label: "Đăng ký Tác giả", icon: UserPlus, roles: ["reader"] }] : []),
    { id: "author", label: "Cấu hình Tác giả", icon: PenTool, roles: ["author", "admin"] },
    { id: "moderator", label: "Kiểm duyệt viên", icon: ShieldCheck, roles: ["moderator", "admin"] },
    { id: "admin", label: "Quản trị viên", icon: Zap, roles: ["admin"] },
  ].filter(s => !user || s.roles.includes(user.role));

  return (
    <div className="w-full max-w-[1440px] mx-auto px-6 md:px-12 py-12 font-sans text-black selection:bg-black selection:text-white">
      

      <header 
        className="mb-12 border-b border-zinc-100 pb-10 flex flex-col md:flex-row md:items-end justify-between gap-8 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
      >
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tighter leading-none text-black">Cài đặt</h1>
          <p className="text-zinc-400 text-sm font-bold uppercase tracking-widest flex items-center gap-2">
            Tùy chọn & Kiểm soát hệ thống <Sparkles className="w-3.5 h-3.5 text-zinc-100" />
          </p>
        </div>
      </header>

      <div className="grid lg:grid-cols-12 gap-12">
        <aside 
          className="lg:col-span-4 space-y-8 transition-all duration-300 delay-75"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="space-y-6">
            <div className="text-[11px] font-bold text-black uppercase tracking-[0.3em] px-1 flex items-center gap-2">
                <Settings className="w-4 h-4 text-zinc-300" /> Tùy chỉnh cá nhân
            </div>
            <nav className="flex flex-col gap-2">
                {sections.map((section) => (
                    <button
                        key={section.id}
                        onClick={() => setActiveSection(section.id as TabKey)}
                        className={`flex items-center justify-between px-8 py-5 text-[11px] font-bold uppercase tracking-widest transition-all rounded-sm border ${
                            activeSection === section.id
                            ? "bg-black text-white border-black"
                            : "bg-white text-zinc-400 border-zinc-100 hover:bg-zinc-50 hover:text-black"
                        }`}
                    >
                        <div className="flex items-center gap-4">
                            <section.icon className="w-4.5 h-4.5" /> {section.label}
                        </div>
                        <ChevronRight className={`w-3.5 h-3.5 transition-transform duration-300 ${activeSection === section.id ? "rotate-90" : ""}`} />
                    </button>
                ))}
            </nav>
          </div>

          <div className="p-10 border border-zinc-100 bg-zinc-50/30 space-y-6 rounded-sm">
             <div className="text-[10px] font-bold text-black uppercase tracking-widest">Định danh hiện tại</div>
             <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-black flex items-center justify-center text-white text-[11px] font-bold uppercase italic rounded-sm">
                    {user?.role?.slice(0, 3)}
                </div>
                <div className="flex flex-col gap-1">
                    <span className="text-xs font-bold text-black uppercase tracking-tighter">{user?.role}</span>
                    <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest italic">Xác minh danh tính</span>
                </div>
             </div>
          </div>
        </aside>

        <main 
          className="lg:col-span-8 transition-all duration-300 delay-150"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)" }}
        >
          <div className="bg-white border border-zinc-100 p-10 lg:p-16 min-h-[600px] animate-in fade-in slide-in-from-bottom-4 duration-300 rounded-sm">
            {activeSection === "appearance" && (
              <div className="space-y-12">
                <div className="space-y-3">
                  <h2 className="text-4xl font-bold tracking-tighter">Hiển thị & Kiểu chữ</h2>
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Tùy biến không gian tiếp nhận tri thức</p>
                </div>

                <div className="space-y-12">
                  <div className="space-y-6">
                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Hệ phông chữ ưu tiên</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {["Inter", "Roboto", "Outfit", "Noto Sans", "Source Sans Pro"].map((font) => (
                        <button
                          key={font}
                          onClick={() => setFontFamily(font)}
                          className={`h-16 border text-[11px] font-bold uppercase tracking-widest transition-all flex items-center justify-center rounded-sm ${
                            fontFamily === font ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
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
                        className="w-full h-16 px-8 border border-zinc-100 focus:border-black bg-zinc-50/20 text-lg font-bold tracking-tight transition-all outline-none rounded-sm"
                      />
                    </div>
                    <div className="space-y-4">
                      <label className="text-[11px] font-bold text-black uppercase tracking-widest">Độ giãn dòng</label>
                      <input
                        type="number"
                        step="0.1"
                        value={lineHeight}
                        onChange={(e) => setLineHeight(parseFloat(e.target.value))}
                        className="w-full h-16 px-8 border border-zinc-100 focus:border-black bg-zinc-50/20 text-lg font-bold tracking-tight transition-all outline-none rounded-sm"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-12 border-t border-zinc-50 flex justify-end">
                   <button 
                    onClick={handleSaveTypography}
                    disabled={loading}
                    className="h-16 px-20 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-sm hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-4 disabled:opacity-50"
                   >
                     {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                     Lưu tùy chỉnh
                   </button>
                </div>
              </div>
            )}

            {activeSection === "apply_author" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="space-y-3">
                        <h2 className="text-4xl font-bold tracking-tighter">Đăng ký Tác giả</h2>
                        <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Tham gia đội ngũ sáng tạo nội dung tri thức</p>
                    </div>

                    {user?.author_status === "pending" ? (
                        <div className="py-24 text-center space-y-8 border border-dashed border-zinc-200 bg-zinc-50/10 rounded-sm">
                            <Clock className="w-16 h-16 text-zinc-100 mx-auto stroke-[1]" />
                            <div className="space-y-3">
                                <h4 className="text-2xl font-bold tracking-tight">Hồ sơ đang được xem xét</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm mx-auto leading-relaxed">
                                    Hệ thống đã ghi nhận đơn ứng tuyển của bạn. Vui lòng chờ phản hồi từ đội ngũ Kiểm duyệt DocLib.
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-10">
                            <div className="p-10 border border-zinc-100 bg-zinc-50/20 space-y-8 rounded-sm">
                                <div className="flex items-center gap-4 text-black border-b border-zinc-50 pb-6">
                                    <Award className="w-6 h-6" />
                                    <h4 className="text-[11px] font-bold uppercase tracking-[0.2em]">Đặc quyền của Tác giả DocLib</h4>
                                </div>
                                <div className="grid md:grid-cols-2 gap-8">
                                    {[
                                        "Xuất bản tài liệu không giới hạn",
                                        "Xây dựng cộng đồng độc giả riêng",
                                        "Nhận nhuận bút & đóng góp tài chính",
                                        "Huy hiệu Tác giả xác minh"
                                    ].map((item, i) => (
                                        <div key={i} className="flex items-start gap-3">
                                            <Sparkles className="w-3.5 h-3.5 text-black shrink-0" />
                                            <span className="text-[12px] font-medium text-zinc-500 leading-tight">{item}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Động lực & Chuyên môn sáng tác</label>
                                    <textarea 
                                        value={motivation}
                                        onChange={(e) => setMotivation(e.target.value)}
                                        className="w-full min-h-[200px] p-8 border border-zinc-100 focus:border-black bg-white text-[13px] font-medium transition-all outline-none leading-relaxed rounded-sm"
                                        placeholder="Hãy chia sẻ về lĩnh vực bạn muốn viết và kinh nghiệm của bạn"
                                    />
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[11px] font-bold text-black uppercase tracking-widest">Portfolio / Sản phẩm tham chiếu (URL)</label>
                                    <input 
                                        type="text"
                                        value={portfolio}
                                        onChange={(e) => setPortfolio(e.target.value)}
                                        className="w-full h-16 px-8 border border-zinc-100 focus:border-black bg-white text-[13px] font-bold transition-all outline-none rounded-sm"
                                        placeholder="https://"
                                    />
                                </div>
                            </div>

                            <div className="pt-8 border-t border-zinc-50">
                                <button 
                                    onClick={handleApplyAuthor}
                                    disabled={loading}
                                    className="w-full h-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-sm hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-4 disabled:opacity-50"
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <UserPlus className="w-5 h-5" />}
                                    Gửi đơn ứng tuyển xác thực
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {activeSection === "privacy" && (
              <div className="space-y-12">
                <div className="space-y-3">
                  <h2 className="text-4xl font-bold tracking-tighter">Quyền riêng tư</h2>
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Thiết lập khả năng hiển thị cá nhân</p>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between p-10 border border-zinc-100 bg-zinc-50/10 group hover:border-black transition-all duration-300 rounded-sm">
                    <div className="space-y-2">
                       <h4 className="text-lg font-bold tracking-tight">Chế độ đọc ẩn danh</h4>
                       <p className="text-[12px] font-medium text-zinc-400 max-w-sm leading-relaxed">Không hiển thị lịch sử đọc và tương tác của bạn trên luồng cộng đồng.</p>
                    </div>
                    <CustomSwitch active={hideActivity} onToggle={() => setHideActivity(!hideActivity)} />
                  </div>

                  <div className="flex items-center justify-between p-10 border border-zinc-100 bg-zinc-50/10 group hover:border-black transition-all duration-300 rounded-sm">
                    <div className="space-y-2">
                       <h4 className="text-lg font-bold tracking-tight">Thư viện nội bộ</h4>
                       <p className="text-[12px] font-medium text-zinc-400 max-w-sm leading-relaxed">Giới hạn quyền truy cập bộ sưu tập tri thức cá nhân đối với người dùng khác.</p>
                    </div>
                    <CustomSwitch active={hideLibrary} onToggle={() => setHideLibrary(!hideLibrary)} />
                  </div>
                </div>

                <div className="pt-12 border-t border-zinc-50 flex justify-end">
                   <button 
                    onClick={handleSavePrivacy}
                    disabled={loading}
                    className="h-16 px-20 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-sm hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center gap-4"
                   >
                     {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Shield className="w-5 h-5" />}
                     Cập nhật quyền
                   </button>
                </div>
              </div>
            )}

            {activeSection === "author" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="space-y-3">
                        <h2 className="text-4xl font-bold tracking-tighter">Cấu hình Tác giả</h2>
                        <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Quản lý hiệu suất sáng tác</p>
                    </div>

                    <div className="space-y-8">
                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all rounded-sm">
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold tracking-tight">Tự động sao lưu bản thảo</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm italic leading-relaxed">Hệ thống sẽ tự động lưu nội dung vào máy chủ mỗi 30 giây trong quá trình soạn thảo.</p>
                            </div>
                            <CustomSwitch 
                                active={autoSave} 
                                onToggle={async () => {
                                    const success = await handleUpdateGeneral({ auto_save: !autoSave });
                                    if (success) setAutoSave(!autoSave);
                                }} 
                            />
                        </div>

                        <div className="space-y-4">
                            <label className="text-[11px] font-bold text-black uppercase tracking-widest">Trạng thái xuất bản mặc định</label>
                            <div className="grid grid-cols-2 gap-4">
                                {["public", "private"].map((mode) => (
                                    <button
                                        key={mode}
                                        onClick={async () => {
                                            const success = await handleUpdateGeneral({ default_visibility: mode });
                                            if (success) setDefaultVisibility(mode);
                                        }}
                                        className={`h-16 border text-[11px] font-bold uppercase tracking-widest transition-all rounded-sm ${
                                            defaultVisibility === mode ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
                                        }`}
                                    >
                                        {mode === "public" ? "Công khai" : "Riêng tư"}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <label className="text-[11px] font-bold text-black uppercase tracking-widest">Thông tin thanh toán thụ hưởng</label>
                            <textarea
                                value={payoutInfo}
                                onChange={(e) => setPayoutInfo(e.target.value)}
                                placeholder="STK, Ngân hàng, Tên chủ tài khoản"
                                className="w-full min-h-[140px] p-8 border border-zinc-100 focus:border-black bg-zinc-50/10 text-[13px] font-medium transition-all outline-none leading-relaxed rounded-sm"
                            />
                        </div>
                    </div>

                    <div className="pt-12 border-t border-zinc-50 flex justify-end">
                        <button className="h-16 px-20 bg-black text-white text-[11px] font-bold uppercase tracking-[0.2em] rounded-sm hover:bg-zinc-800 transition-all flex items-center gap-4">
                            <Save className="w-5 h-5" /> Lưu cấu hình
                        </button>
                    </div>
                </div>
            )}

            {activeSection === "moderator" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="space-y-3">
                        <h2 className="text-4xl font-bold tracking-tighter">Điều hành viên</h2>
                        <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Cấu hình hiệu suất giám sát</p>
                    </div>

                    <div className="space-y-8">
                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all rounded-sm">
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold tracking-tight">Thông báo vi phạm thời gian thực</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm">Nhận cảnh báo ngay lập tức khi có báo cáo vi phạm cộng đồng mới.</p>
                            </div>
                            <CustomSwitch 
                                active={modNotifs} 
                                onToggle={async () => {
                                    const success = await handleUpdateGeneral({ mod_notifs: !modNotifs });
                                    if (success) {
                                        setModNotifs(!modNotifs);
                                        showToast(`Đã ${!modNotifs ? "bật" : "tắt"} thông báo.`, "success");
                                    }
                                }} 
                            />
                        </div>

                        <div className="flex items-center justify-between p-10 border border-zinc-100 bg-white group hover:border-black transition-all rounded-sm">
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold tracking-tight">Tự động làm mới hàng chờ duyệt</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm italic leading-relaxed">Cập nhật danh sách bản thảo chờ phê duyệt mỗi 60 giây.</p>
                            </div>
                            <CustomSwitch 
                                active={autoRefresh} 
                                onToggle={async () => {
                                    const success = await handleUpdateGeneral({ auto_refresh: !autoRefresh });
                                    if (success) {
                                        setAutoRefresh(!autoRefresh);
                                        showToast(`Đã ${!autoRefresh ? "bật" : "tắt"} tự động làm mới.`, "success");
                                    }
                                }} 
                            />
                        </div>
                    </div>
                </div>
            )}

            {activeSection === "admin" && (
                <div className="space-y-12 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="space-y-3">
                        <h2 className="text-4xl font-bold tracking-tighter">Quản trị cấp cao</h2>
                        <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Kiểm soát vận hành toàn cầu DocLib</p>
                    </div>

                    <div className="grid gap-6">
                        <div className="p-10 border border-zinc-100 bg-zinc-50/30 flex items-center justify-between group hover:border-black transition-all duration-300 rounded-sm">
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold tracking-tight text-red-600">Chế độ bảo trì hệ thống</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm leading-relaxed italic">Khóa toàn bộ tác vụ ghi dữ liệu trên toàn hệ thống để nâng cấp kỹ thuật.</p>
                            </div>
                            <CustomSwitch active={maintenanceMode} onToggle={handleToggleMaintenance} color="red" />
                        </div>

                        <div className="p-10 border border-zinc-100 bg-white flex items-center justify-between group hover:border-black transition-all duration-300 rounded-sm">
                            <div className="space-y-2">
                                <h4 className="text-lg font-bold tracking-tight">Đăng ký tài khoản mới</h4>
                                <p className="text-[12px] font-medium text-zinc-400 max-w-sm">Cho phép hoặc chặn quyền đăng ký tài khoản cho người dùng mới.</p>
                            </div>
                            <CustomSwitch active={registrationEnabled} onToggle={handleToggleRegistration} />
                        </div>
                    </div>
                </div>
            )}

            {activeSection === "notifications" && (
              <div className="flex flex-col items-center justify-center min-h-[400px] text-center space-y-8 animate-in fade-in duration-300">
                <div className="w-20 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center rounded-sm">
                  <Bell className="w-10 h-10 text-zinc-100 stroke-[1]" />
                </div>
                <div className="space-y-3">
                   <h3 className="text-2xl font-bold tracking-tighter">Trung tâm thông báo</h3>
                   <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest max-w-[280px] mx-auto leading-relaxed">
                     Hệ thống đồng bộ thông báo đang được thiết lập cho tài khoản của bạn.
                   </p>
                </div>
              </div>
            )}

            {activeSection === "account" && (
              <div className="space-y-12 animate-in fade-in duration-300">
                <div className="space-y-3">
                  <h2 className="text-4xl font-bold tracking-tighter">Định danh & Bảo mật</h2>
                  <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest italic">Quản lý lớp phòng thủ tài khoản</p>
                </div>

                <div className="space-y-6">
                   <div className="p-10 border border-zinc-100 flex items-center justify-between hover:border-black transition-all duration-300 rounded-sm group">
                      <div className="space-y-2">
                         <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">Trạng thái xác thực</span>
                         <div className="text-base font-bold flex items-center gap-3">
                            <ShieldCheck className="w-5 h-5 text-black" /> Tài khoản đã định danh cấp cao
                         </div>
                      </div>
                      <button className="h-14 px-10 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all rounded-sm">Đổi mật khẩu</button>
                   </div>

                   <div className="p-10 border border-zinc-100 flex items-center justify-between hover:border-black transition-all duration-300 rounded-sm group">
                      <div className="space-y-2">
                         <span className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest">Địa chỉ Email liên kết</span>
                         <div className="text-base font-bold tracking-tight">{user?.email || "Chưa định danh"}</div>
                      </div>
                      <button className="h-14 px-10 border border-zinc-100 text-[10px] font-bold uppercase tracking-widest hover:border-black transition-all rounded-sm">Cập nhật Email</button>
                   </div>
                </div>

                <div className="pt-20 border-t border-zinc-50 flex items-center gap-4">
                   <AlertCircle className="w-5 h-5 text-zinc-100 shrink-0" />
                   <p className="text-[10px] font-bold text-zinc-200 uppercase tracking-widest leading-relaxed italic">
                     DocLib yêu cầu xác thực hai lớp cho mọi thay đổi quan trọng liên quan đến bảo mật và tài chính.
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
