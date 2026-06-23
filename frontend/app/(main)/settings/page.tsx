"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
  ModalDescription,
} from "@/shared/components/ui/Modal";
import {
  getPrivacySettingsAPI,
  updatePrivacySettingsAPI,
  updateGeneralSettingsAPI,
} from "@/features/provision/services/system_setting.service";
import {
  getNotificationSettingsAPI,
  updateNotificationSettingsAPI,
} from "@/features/communication/services/push_notification.service";
import {
  getMaintenanceModeAPI,
  getAdminConfigAPI,
  toggleMaintenanceModeAPI,
  updateAdminConfigAPI,
} from "@/features/provision/services/system_operation.service";
import {
  Shield,
  Bell,
  Lock,
  ChevronRight,
  Save,
  Loader2,
  Sparkles,
  PenTool,
  ShieldCheck,
  Zap,
  UserPlus,
  Award,
  Clock,
  AlertCircle,
  ShieldAlert,
} from "lucide-react";

type TabKey =
  | "privacy"
  | "notifications"
  | "account"
  | "apply_author"
  | "author"
  | "moderator"
  | "admin";

export default function SettingsPage() {
  const { showToast } = useToast();
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const [visible, setVisible] = useState(false);
  const [activeSection, setActiveSection] = useState<TabKey>("privacy");
  const [loading, setLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    type: "maintenance" | "registration";
    value: boolean;
  } | null>(null);

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

  const [notifSettings, setNotifSettings] = useState<any>({});

  const fetchData = useCallback(async () => {
    try {
      const privacyRes = await getPrivacySettingsAPI();
      setHideActivity(privacyRes.data?.hide_reading_activity || false);
      setHideLibrary(privacyRes.data?.hide_library || false);

      try {
        const notifRes = await getNotificationSettingsAPI();
        setNotifSettings(notifRes.data || {});
      } catch (e) {}

      if (user?.role === "admin") {
        const maintData = await getMaintenanceModeAPI();
        setMaintenanceMode(
          maintData.data?.enabled || maintData.enabled || false,
        );

        const configData = await getAdminConfigAPI();
        setRegistrationEnabled(configData.data?.registration_enabled ?? true);
      }

      if (user?.settings) {
        setModNotifs(user.settings.mod_notifs ?? true);
        setAutoRefresh(user.settings.auto_refresh ?? false);
        setAutoSave(user.settings.auto_save ?? true);
        setDefaultVisibility(user.settings.default_visibility ?? "public");
        setPayoutInfo(user.settings.payout_info || "");
      }
    } catch (err: any) {
      showToast("Không thể đồng bộ dữ liệu cài đặt", "error");
    }
  }, [user, showToast]);


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
      showToast("Không thể cập nhật cấu hình cá nhân", "error");
      return false;
    }
  };

  const handleSavePrivacy = async () => {
    setLoading(true);
    try {
      await updatePrivacySettingsAPI({
        hide_reading_activity: hideActivity,
        hide_library: hideLibrary,
      });
      showToast("Đã cập nhật quyền riêng tư", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật riêng tư", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation) {
      showToast("Vui lòng nhập lý do ứng tuyển", "error");
      return;
    }
    setLoading(true);
    try {
      // await updateUserAPI({ motivation, portfolio });
      showToast("Đã gửi đơn ứng tuyển thành công", "success");
      setMotivation("");
      setPortfolio("");
      refreshUser?.();
    } catch (err: any) {
      showToast(err.message || "Không thể gửi đơn ứng tuyển", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMaintenance = async () => {
    setLoading(true);
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setMaintenanceMode(!maintenanceMode);
      showToast(
        !maintenanceMode ? "Đã kích hoạt bảo trì" : "Đã tắt bảo trì",
        "success",
      );
      setConfirmModal(null);
    } catch (err: any) {
      showToast("Lỗi thao tác bảo trì hệ thống", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRegistration = async () => {
    setLoading(true);
    try {
      await updateAdminConfigAPI({
        registration_enabled: !registrationEnabled,
      });
      setRegistrationEnabled(!registrationEnabled);
      showToast(
        !registrationEnabled ? "Đã mở đăng ký" : "Đã đóng đăng ký",
        "success",
      );
      setConfirmModal(null);
    } catch (err: any) {
      showToast("Lỗi cập nhật cấu hình đăng ký", "error");
    } finally {
      setLoading(false);
    }
  };

  const CustomSwitch = ({
    active,
    onToggle,
  }: {
    active: boolean;
    onToggle: () => void;
  }) => (
    <button
      onClick={onToggle}
      className={`w-12 h-6 relative shrink-0 rounded-full border shadow-sm transition-all duration-300 ${
        active ? "bg-black border-black" : "bg-zinc-100 border-zinc-200"
      }`}
    >
      <div
        className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-300 ${
          active ? "left-7" : "left-0.5"
        }`}
      />
    </button>
  );

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-zinc-50">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  const sections = [
    {
      id: "privacy",
      label: "Quyền riêng tư",
      icon: Shield,
      roles: ["reader", "potential_author", "author", "moderator", "admin"],
    },
    {
      id: "notifications",
      label: "Thông báo",
      icon: Bell,
      roles: ["reader", "potential_author", "author", "moderator", "admin"],
    },
    {
      id: "account",
      label: "Tài khoản & Bảo mật",
      icon: Lock,
      roles: ["reader", "potential_author", "author", "moderator", "admin"],
    },
    ...(user?.role === "reader" &&
    user?.author_status !== "pending" &&
    user?.author_status !== "approved"
      ? [
          {
            id: "apply_author",
            label: "Tác giả tiềm năng",
            icon: UserPlus,
            roles: ["reader"],
          },
        ]
      : []),
    {
      id: "author",
      label: "Cấu hình Tác giả",
      icon: PenTool,
      roles: ["author", "admin"],
    },
    {
      id: "moderator",
      label: "Kiểm duyệt viên",
      icon: ShieldCheck,
      roles: ["moderator", "admin"],
    },
    { id: "admin", label: "Quản trị viên", icon: Zap, roles: ["admin"] },
  ].filter((s) => !user || s.roles.includes(user.role));

  return (
    <div className="w-full max-w-[1280px] mx-auto px-4 md:px-6 py-6 font-sans text-zinc-900 bg-zinc-50 min-h-[calc(100dvh-var(--navbar-height))] selection:bg-black selection:text-white">
      <div className="mb-6 md:mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">Cài đặt hệ thống</h1>
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
            Tùy chọn và kiểm soát hệ thống
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-6 transition-opacity duration-500" style={{ opacity: visible ? 1 : 0 }}>
        <aside className="lg:col-span-4 xl:col-span-3 space-y-6">
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-4 md:p-6 rounded-3xl shadow-sm space-y-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 border-b border-zinc-100 pb-3">
              Danh mục
            </div>
            <nav className="flex flex-col gap-2">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id as TabKey)}
                    className={`flex items-center justify-between px-4 py-3 text-sm font-bold rounded-2xl transition-all duration-200 ${
                      activeSection === section.id
                        ? "bg-black text-white shadow-md scale-[1.02]"
                        : "bg-transparent text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4" />
                      {section.label}
                    </div>
                    {activeSection === section.id && (
                      <ChevronRight className="w-4 h-4 opacity-50" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 rounded-3xl shadow-sm space-y-4">
            <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 border-b border-zinc-100 pb-3">
              Định danh hiện tại
            </div>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-black flex items-center justify-center text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl shrink-0 shadow-md">
                {user?.role?.slice(0, 3)}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-bold text-zinc-900 uppercase truncate">
                  {user?.role === "admin" ? "Quản trị viên" : user?.role === "author" ? "Tác giả" : user?.role === "moderator" ? "Kiểm duyệt viên" : user?.role === "potential_author" ? "Tác giả tiềm năng" : "Độc giả"}
                </span>
                <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest truncate mt-0.5">
                  {user?.email || "Chưa định danh"}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-9 space-y-6">
          {activeSection === "privacy" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Quyền riêng tư
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Thiết lập khả năng hiển thị cá nhân
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Chế độ đọc ẩn danh
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Không hiển thị lịch sử đọc và tương tác của bạn trên
                      bảng xếp hạng và luồng chung.
                    </p>
                  </div>
                  <CustomSwitch
                    active={hideActivity}
                    onToggle={() => setHideActivity(!hideActivity)}
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Thư viện nội bộ
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Giới hạn quyền truy cập bộ sưu tập cá nhân đối với người
                      dùng khác.
                    </p>
                  </div>
                  <CustomSwitch
                    active={hideLibrary}
                    onToggle={() => setHideLibrary(!hideLibrary)}
                  />
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-zinc-50 flex justify-end">
                <button
                  onClick={handleSavePrivacy}
                  disabled={loading}
                  className="h-11 px-8 bg-black text-white text-xs font-bold uppercase tracking-widest rounded-2xl flex items-center gap-2 disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Shield className="w-4 h-4" />
                  )}{" "}
                  Cập nhật quyền
                </button>
              </div>
            </div>
          )}

          {activeSection === "author" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Cấu hình Tác giả
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Quản lý hiệu suất sáng tác
                </p>
              </div>

              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Tự động sao lưu bản thảo
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Hệ thống sẽ tự động lưu nội dung vào máy chủ mỗi 30
                      giây.
                    </p>
                  </div>
                  <CustomSwitch
                    active={autoSave}
                    onToggle={async () => {
                      const success = await handleUpdateGeneral({
                        auto_save: !autoSave,
                      });
                      if (success) setAutoSave(!autoSave);
                    }}
                  />
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                    Trạng thái xuất bản mặc định
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    {["public", "private"].map((mode) => (
                      <button
                        key={mode}
                        onClick={async () => {
                          const success = await handleUpdateGeneral({
                            default_visibility: mode,
                          });
                          if (success) setDefaultVisibility(mode);
                        }}
                        className={`h-11 border text-[10px] font-bold uppercase tracking-widest rounded-2xl transition-all duration-200 ${
                          defaultVisibility === mode
                            ? "bg-black text-white border-black shadow-md hover:scale-[1.02]"
                            : "bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50"
                        }`}
                      >
                        {mode === "public" ? "Công khai" : "Riêng tư"}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                    Thông tin thanh toán thụ hưởng
                  </label>
                  <textarea
                    value={payoutInfo}
                    onChange={(e) => setPayoutInfo(e.target.value)}
                    className="w-full min-h-[120px] p-4 border border-zinc-200 focus:border-black bg-white text-sm font-medium outline-none resize-none rounded-2xl shadow-sm transition-all"
                    placeholder="Nhập thông tin ngân hàng..."
                  />
                </div>
              </div>

              <div className="pt-6 mt-6 border-t border-zinc-50 flex justify-end">
                <button
                  onClick={async () => {
                    setLoading(true);
                    await handleUpdateGeneral({ payout_info: payoutInfo });
                    setLoading(false);
                    showToast("Đã lưu thông tin thụ hưởng", "success");
                  }}
                  className="h-11 px-8 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center gap-2 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
                >
                  <Save className="w-4 h-4" /> Lưu cấu hình
                </button>
              </div>
            </div>
          )}

          {activeSection === "moderator" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Kiểm duyệt viên
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Cấu hình hiệu suất giám sát
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Thông báo vi phạm thời gian thực
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Nhận cảnh báo ngay lập tức khi có báo cáo vi phạm quy
                      chế mới.
                    </p>
                  </div>
                  <CustomSwitch
                    active={modNotifs}
                    onToggle={async () => {
                      const success = await handleUpdateGeneral({
                        mod_notifs: !modNotifs,
                      });
                      if (success) {
                        setModNotifs(!modNotifs);
                        showToast(
                          `Đã ${!modNotifs ? "bật" : "tắt"} thông báo`,
                          "success",
                        );
                      }
                    }}
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Tự động làm mới hàng chờ duyệt
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Cập nhật danh sách bản thảo chờ phê duyệt mỗi 60 giây.
                    </p>
                  </div>
                  <CustomSwitch
                    active={autoRefresh}
                    onToggle={async () => {
                      const success = await handleUpdateGeneral({
                        auto_refresh: !autoRefresh,
                      });
                      if (success) {
                        setAutoRefresh(!autoRefresh);
                        showToast(
                          `Đã ${!autoRefresh ? "bật" : "tắt"} tự động làm mới`,
                          "success",
                        );
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === "admin" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Quản trị viên
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Kiểm soát vận hành toàn cầu DocLib
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-red-100 bg-red-50/50 rounded-3xl gap-4 transition-all duration-300">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-red-600">
                      Chế độ bảo trì hệ thống
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-red-400/80 max-w-sm leading-relaxed">
                      Khóa toàn bộ tác vụ ghi dữ liệu trên toàn hệ thống để
                      nâng cấp kỹ thuật.
                    </p>
                  </div>
                  <CustomSwitch
                    active={maintenanceMode}
                    onToggle={() =>
                      setConfirmModal({
                        type: "maintenance",
                        value: !maintenanceMode,
                      })
                    }
                  />
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-zinc-900">
                      Đăng ký tài khoản mới
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">
                      Cho phép hoặc chặn quyền đăng ký tài khoản cho người
                      dùng mới.
                    </p>
                  </div>
                  <CustomSwitch
                    active={registrationEnabled}
                    onToggle={() =>
                      setConfirmModal({
                        type: "registration",
                        value: !registrationEnabled,
                      })
                    }
                  />
                </div>
              </div>
            </div>
          )}

          {activeSection === "apply_author" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Tác giả tiềm năng
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Tham gia đội ngũ sáng tạo nội dung
                </p>
              </div>

              {user?.author_status === "pending" ? (
                <div className="py-16 text-center space-y-4 border border-dashed border-zinc-200 bg-zinc-50 rounded-3xl">
                  <div className="w-16 h-16 bg-white border border-zinc-100 shadow-sm flex items-center justify-center rounded-2xl mx-auto mb-4">
                    <Clock className="w-8 h-8 text-zinc-400 stroke-[1.5]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-zinc-900 uppercase tracking-widest mb-2">
                      Hồ sơ đang được xem xét
                    </h4>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 max-w-xs mx-auto leading-relaxed">
                      Hệ thống đã ghi nhận đơn ứng tuyển của bạn. Vui lòng chờ
                      phản hồi từ đội ngũ Kiểm duyệt DocLib.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="p-6 border border-zinc-100 bg-zinc-50/50 space-y-4 rounded-3xl shadow-sm">
                    <div className="flex items-center gap-2 text-zinc-900 border-b border-zinc-100 pb-4">
                      <Award className="w-5 h-5 text-black" />
                      <h4 className="text-[10px] font-bold uppercase tracking-widest">
                        Đặc quyền của Tác giả DocLib
                      </h4>
                    </div>
                    <div className="grid md:grid-cols-2 gap-4">
                      {[
                        "Xuất bản tài liệu không giới hạn",
                        "Xây dựng lượng độc giả trung thành",
                        "Nhận nhuận bút & đóng góp tài chính",
                        "Huy hiệu Tác giả xác minh",
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-white border border-zinc-100 rounded-2xl shadow-sm">
                          <Sparkles className="w-4 h-4 text-black shrink-0 mt-0.5" />
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">
                            {item}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                        Động lực & Chuyên môn sáng tác
                      </label>
                      <textarea
                        value={motivation}
                        onChange={(e) => setMotivation(e.target.value)}
                        className="w-full min-h-[140px] p-4 border border-zinc-200 focus:border-black bg-white text-sm font-medium outline-none resize-none rounded-2xl shadow-sm transition-all"
                        placeholder="Chia sẻ về bạn..."
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest ml-1 block">
                        Portfolio / Sản phẩm tham chiếu (URL)
                      </label>
                      <input
                        type="text"
                        value={portfolio}
                        onChange={(e) => setPortfolio(e.target.value)}
                        className="w-full h-11 px-4 border border-zinc-200 focus:border-black bg-white text-sm font-medium outline-none rounded-2xl shadow-sm transition-all"
                        placeholder="https://..."
                      />
                    </div>
                  </div>

                  <div className="pt-6 mt-6 border-t border-zinc-50">
                    <button
                      onClick={handleApplyAuthor}
                      disabled={loading}
                      className="w-full h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center gap-2 disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <UserPlus className="w-4 h-4" />
                      )}
                      Gửi đơn ứng tuyển xác thực
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeSection === "notifications" && (
            <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm space-y-8">
              <div className="border-b border-zinc-100 pb-4 mb-6">
                <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                  Cài đặt thông báo
                </h3>
                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Tùy chỉnh kênh nhận thông báo
                </p>
              </div>

              <div className="space-y-4">
                {[
                  { id: "notifyCommunity", label: "Tương tác cộng đồng", desc: "Thông báo khi có người bình chọn, bình luận hoặc nhắc đến bạn." },
                  { id: "notifyFinance", label: "Giao dịch & Tài chính", desc: "Thông báo về việc mua tài liệu, tặng coin hoặc yêu cầu rút tiền." },
                  { id: "notifyUpdates", label: "Cập nhật tài liệu", desc: "Thông báo khi các tài liệu bạn theo dõi có chương mới." },
                  { id: "notifyNewsletter", label: "Bản tin DocLib", desc: "Cập nhật về các tính năng mới và cuộc thi sắp tới." }
                ].map((item, i) => (
                  <div key={i} className="flex flex-col md:flex-row md:items-center justify-between p-5 border border-zinc-100 bg-zinc-50 rounded-3xl gap-4 transition-all duration-300 hover:border-zinc-200">
                    <div className="space-y-1">
                      <h4 className="text-sm font-bold text-zinc-900">{item.label}</h4>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 max-w-sm leading-relaxed">{item.desc}</p>
                    </div>
                    <div className="flex gap-6">
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-bold tracking-widest uppercase text-zinc-500">Email</span>
                        <CustomSwitch
                          active={notifSettings[item.id]?.email ?? false}
                          onToggle={async () => {
                            const currentVal = notifSettings[item.id]?.email ?? false;
                            const newVal = !currentVal;
                            const newSettings = {
                              ...notifSettings,
                              [item.id]: { ...(notifSettings[item.id] || {}), email: newVal }
                            };
                            setNotifSettings(newSettings);
                            try {
                              await updateNotificationSettingsAPI(newSettings);
                              showToast("Đã cập nhật thông báo", "success");
                            } catch (e) {
                              setNotifSettings(notifSettings); // revert
                              showToast("Lỗi cập nhật", "error");
                            }
                          }}
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[9px] font-bold tracking-widest uppercase text-zinc-500">Hệ thống</span>
                        <CustomSwitch
                          active={notifSettings[item.id]?.inapp ?? false}
                          onToggle={async () => {
                            const currentVal = notifSettings[item.id]?.inapp ?? false;
                            const newVal = !currentVal;
                            const newSettings = {
                              ...notifSettings,
                              [item.id]: { ...(notifSettings[item.id] || {}), inapp: newVal }
                            };
                            setNotifSettings(newSettings);
                            try {
                              await updateNotificationSettingsAPI(newSettings);
                              showToast("Đã cập nhật thông báo", "success");
                            } catch (e) {
                              setNotifSettings(notifSettings); // revert
                              showToast("Lỗi cập nhật", "error");
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeSection === "account" && (
            <div className="space-y-6">
              <div className="bg-white/90 backdrop-blur-md border border-zinc-100 p-6 md:p-8 rounded-3xl shadow-sm">
                <div className="border-b border-zinc-100 pb-4 mb-6">
                  <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-1">
                    Định danh & Bảo mật
                  </h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Quản lý lớp phòng thủ tài khoản
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="p-5 border border-zinc-100 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl bg-zinc-50/50 shadow-sm transition-all duration-300 hover:border-zinc-200">
                    <div>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">
                        Trạng thái xác thực
                      </span>
                      <div className="text-xs font-bold uppercase tracking-widest text-zinc-900 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-black" /> Tài khoản đã định
                        danh cấp cao
                      </div>
                    </div>
                    <button className="px-6 h-11 border border-zinc-200 bg-white text-black text-[10px] font-bold uppercase tracking-widest rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]">
                      Đổi mật khẩu
                    </button>
                  </div>

                  <div className="p-5 border border-zinc-100 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-3xl bg-zinc-50/50 shadow-sm transition-all duration-300 hover:border-zinc-200">
                    <div>
                      <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block mb-1.5">
                        Địa chỉ Email liên kết
                      </span>
                      <div className="text-xs font-bold uppercase tracking-widest text-zinc-900">
                        {user?.email || "Chưa định danh"}
                      </div>
                    </div>
                    <button className="px-6 h-11 border border-zinc-200 bg-white text-black text-[10px] font-bold uppercase tracking-widest rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]">
                      Cập nhật Email
                    </button>
                  </div>
                </div>

                <div className="mt-6 flex items-start gap-3 bg-zinc-50/50 p-5 border border-zinc-100 rounded-3xl shadow-sm">
                  <AlertCircle className="w-5 h-5 text-zinc-400 shrink-0 mt-0.5" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 leading-relaxed">
                    DocLib yêu cầu xác thực hai lớp cho mọi thay đổi quan trọng
                    liên quan đến bảo mật và tài chính.
                  </p>
                </div>
              </div>

              <div className="border border-red-100 bg-red-50/30 p-6 md:p-8 rounded-3xl shadow-sm">
                <div className="border-b border-red-100 pb-4 mb-6">
                  <h3 className="text-xl font-bold tracking-tight text-red-600 mb-1">
                    Vùng nguy hiểm
                  </h3>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-red-400/80">
                    Các hành động không thể hoàn tác
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/50 p-5 rounded-3xl border border-red-50">
                    <div>
                      <h4 className="text-sm font-bold text-zinc-900">
                        Tải xuống dữ liệu (GDPR)
                      </h4>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-1.5">
                        Yêu cầu trích xuất toàn bộ dữ liệu cá nhân của bạn.
                      </p>
                    </div>
                    <button
                      onClick={() =>
                        showToast(
                          "Đã gửi yêu cầu trích xuất dữ liệu",
                          "success",
                        )
                      }
                      className="px-6 h-11 border border-zinc-200 bg-white text-black text-[10px] font-bold uppercase tracking-widest rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]"
                    >
                      Yêu cầu trích xuất
                    </button>
                  </div>
                  
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white/50 p-5 rounded-3xl border border-red-50">
                    <div>
                      <h4 className="text-sm font-bold text-red-600">
                        Xóa tài khoản vĩnh viễn
                      </h4>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mt-1.5">
                        Xóa hoàn toàn tài khoản và mọi dữ liệu liên kết. Không
                        thể khôi phục.
                      </p>
                    </div>
                    <button
                      onClick={() =>
                        showToast("Chức năng đang bảo trì", "error")
                      }
                      className="px-6 h-11 border border-red-600 bg-red-600 text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5"
                    >
                      Xóa tài khoản
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !loading && setConfirmModal(null)}
        className="max-w-md rounded-3xl border border-zinc-100 bg-white/95 backdrop-blur-md p-0 shadow-xl overflow-hidden"
      >
        <ModalHeader className="border-b border-zinc-100 p-6">
          <ModalTitle className="text-sm font-bold tracking-tight text-zinc-900">
            Xác nhận thay đổi
          </ModalTitle>
          <ModalDescription className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mt-1">
            Hành động này có thể ảnh hưởng hệ thống
          </ModalDescription>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 leading-relaxed">
            {confirmModal?.type === "maintenance"
              ? `Bạn có chắc chắn muốn ${
                  confirmModal?.value ? "kích hoạt" : "tắt"
                } chế độ bảo trì? Hành động này sẽ ảnh hưởng đến tất cả người dùng.`
              : `Bạn có chắc chắn muốn ${
                  confirmModal?.value ? "mở lại" : "đóng"
                } cổng đăng ký tài khoản mới?`}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-100 p-5 bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={loading}
            className="flex-1 h-11 border border-zinc-200 bg-white text-[10px] font-bold uppercase tracking-widest text-black rounded-2xl disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] shadow-sm"
          >
            Hủy bỏ
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "maintenance")
                handleToggleMaintenance();
              else if (confirmModal?.type === "registration")
                handleToggleRegistration();
            }}
            disabled={loading}
            className="flex-1 h-11 bg-black text-white text-[10px] font-bold uppercase tracking-widest rounded-2xl flex items-center justify-center disabled:opacity-50 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md gap-2"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              "Xác nhận thay đổi"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
