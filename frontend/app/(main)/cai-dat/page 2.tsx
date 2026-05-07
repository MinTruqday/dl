"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";
import {
  getPrivacySettingsAPI,
  updatePrivacySettingsAPI,
  updateTypographyAPI,
  updateGeneralSettingsAPI,
  applyAuthorAPI,
  updateProfileAPI,
} from "@/services/setting.service";
import {
  getMaintenanceModeAPI,
  getAdminConfigAPI,
  toggleMaintenanceModeAPI,
  updateAdminConfigAPI,
} from "@/services/operation.service";
import {
  Settings,
  Type,
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
  | "appearance"
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
  const [activeSection, setActiveSection] = useState<TabKey>("appearance");
  const [loading, setLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    type: "maintenance" | "registration";
    value: boolean;
  } | null>(null);

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

  const handleSaveTypography = async () => {
    setLoading(true);
    try {
      await updateTypographyAPI({
        font_family: fontFamily,
        font_size: fontSize,
        line_height: lineHeight,
      });
      showToast("Đã lưu tùy chỉnh hiển thị", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật hiển thị", "error");
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
      await applyAuthorAPI({ motivation, portfolio });
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
      className={`w-10 h-5 relative shrink-0 rounded-none border border-zinc-200 ${active ? "bg-black border-black" : "bg-zinc-100"
        }`}
    >
      <div
        className={`absolute top-0 w-4 h-4 bg-white border border-zinc-200 ${active ? "left-5 border-black" : "left-0"
          }`}
      />
    </button>
  );

  if (authLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-white">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  const sections = [
    {
      id: "appearance",
      label: "Hiển thị & Kiểu chữ",
      icon: Type,
      roles: ["reader", "potential_author", "author", "moderator", "admin"],
    },
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
          label: "Đăng ký Tác giả",
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
    <div className="w-full max-w-[1300px] mx-auto px-6 md:px-12 pt-6 pb-12 font-sans text-black selection:bg-black selection:text-white">
      <div
        className="mb-8 border-b border-zinc-200 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-black">Cài đặt</h1>
          <p className="text-zinc-500 text-sm font-medium">
            Tùy chọn và kiểm soát hệ thống
          </p>
        </div>
      </div>

      <div
        className="grid lg:grid-cols-12 gap-12"
      >
        <aside className="lg:col-span-3 space-y-12">
          <div className="space-y-4">
            <div className="text-sm font-semibold text-black border-b border-zinc-200 pb-2">
              Cài đặt
            </div>
            <nav className="flex flex-col gap-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id as TabKey)}
                  className={`flex items-center justify-between px-3 py-2 text-sm font-medium border rounded-none ${activeSection === section.id
                      ? "bg-zinc-100 text-black border-zinc-300"
                      : "bg-white text-zinc-500 border-transparent"
                    }`}
                >
                  {section.label}
                  {activeSection === section.id && <ChevronRight className="w-4 h-4" />}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6 border border-zinc-200 bg-white space-y-4">
            <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest">
              Định danh hiện tại
            </div>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-black flex items-center justify-center text-white text-xs font-bold uppercase rounded-none shrink-0">
                {user?.role?.slice(0, 3)}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-semibold text-black uppercase truncate">
                  {user?.role}
                </span>
                <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest truncate">
                  {user?.email || "Chưa định danh"}
                </span>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-9 space-y-6">
          {activeSection === "appearance" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Hiển thị & Kiểu chữ
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Tùy biến không gian hiển thị
                  </p>
                </div>

                <div className="mb-8 p-6 border border-zinc-200 bg-zinc-50">
                  <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest mb-4">
                    Bản xem trước
                  </div>
                  <div
                    className="bg-white border border-zinc-200 p-6 text-black"
                    style={{ fontFamily, fontSize: `${fontSize}px`, lineHeight }}
                  >
                    Kiến trúc thông tin (Information Architecture) là nền tảng cốt
                    lõi của mọi hệ thống tương tác số. Việc cấu trúc dữ liệu minh
                    bạch giúp giảm thiểu tải lượng nhận thức cho người dùng.
                  </div>
                </div>

                <div className="space-y-6">
                  <div className="space-y-3">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Hệ phông chữ ưu tiên
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
                      {[
                        "Inter",
                        "Roboto",
                        "Outfit",
                        "Noto Sans",
                        "Source Sans Pro",
                      ].map((font) => (
                        <button
                          key={font}
                          onClick={() => setFontFamily(font)}
                          className={`py-3 px-2 border text-[10px] font-semibold uppercase tracking-widest text-center rounded-none truncate ${fontFamily === font
                              ? "bg-black text-white border-black"
                              : "bg-white text-zinc-500 border-zinc-200"
                            }`}
                          style={{ fontFamily: font }}
                        >
                          {font}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                        Cỡ chữ (px)
                      </label>
                      <input
                        type="number"
                        value={fontSize}
                        onChange={(e) => setFontSize(parseInt(e.target.value))}
                        className="w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none rounded-none"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                        Độ giãn dòng
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={lineHeight}
                        onChange={(e) =>
                          setLineHeight(parseFloat(e.target.value))
                        }
                        className="w-full h-10 px-3 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-semibold outline-none rounded-none"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-6 mt-6 border-t border-zinc-200 flex justify-end">
                  <button
                    onClick={handleSaveTypography}
                    disabled={loading}
                    className="h-10 px-6 bg-black text-white text-xs font-medium rounded-none flex items-center gap-2 disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}{" "}
                    Lưu tùy chỉnh
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === "privacy" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Quyền riêng tư
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Thiết lập khả năng hiển thị cá nhân
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Chế độ đọc ẩn danh
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Không hiển thị lịch sử đọc và tương tác của bạn trên luồng
                        cộng đồng.
                      </p>
                    </div>
                    <CustomSwitch
                      active={hideActivity}
                      onToggle={() => setHideActivity(!hideActivity)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Thư viện nội bộ
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Giới hạn quyền truy cập bộ sưu tập cá nhân đối với
                        người dùng khác.
                      </p>
                    </div>
                    <CustomSwitch
                      active={hideLibrary}
                      onToggle={() => setHideLibrary(!hideLibrary)}
                    />
                  </div>
                </div>

                <div className="pt-6 mt-6 border-t border-zinc-200 flex justify-end">
                  <button
                    onClick={handleSavePrivacy}
                    disabled={loading}
                    className="h-10 px-6 bg-black text-white text-xs font-medium rounded-none flex items-center gap-2 disabled:opacity-50"
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
            </div>
          )}

          {activeSection === "author" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Cấu hình Tác giả
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Quản lý hiệu suất sáng tác
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Tự động sao lưu bản thảo
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Hệ thống sẽ tự động lưu nội dung vào máy chủ mỗi 30 giây.
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
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
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
                          className={`h-10 border text-[10px] font-semibold uppercase tracking-widest rounded-none ${defaultVisibility === mode
                              ? "bg-black text-white border-black"
                              : "bg-zinc-50 text-zinc-500 border-zinc-200"
                            }`}
                        >
                          {mode === "public" ? "Công khai" : "Riêng tư"}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                      Thông tin thanh toán thụ hưởng
                    </label>
                    <textarea
                      value={payoutInfo}
                      onChange={(e) => setPayoutInfo(e.target.value)}
                      className="w-full min-h-[120px] p-4 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-medium outline-none resize-none rounded-none"
                    />
                  </div>
                </div>

                <div className="pt-6 mt-6 border-t border-zinc-200 flex justify-end">
                  <button
                    onClick={async () => {
                      setLoading(true);
                      await handleUpdateGeneral({ payout_info: payoutInfo });
                      setLoading(false);
                      showToast("Đã lưu thông tin thụ hưởng", "success");
                    }}
                    className="h-10 px-6 bg-black text-white text-xs font-medium rounded-none flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" /> Lưu cấu hình
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeSection === "moderator" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Kiểm duyệt viên
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Cấu hình hiệu suất giám sát
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Thông báo vi phạm thời gian thực
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Nhận cảnh báo ngay lập tức khi có báo cáo vi phạm cộng đồng
                        mới.
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

                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Tự động làm mới hàng chờ duyệt
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
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
            </div>
          )}

          {activeSection === "admin" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Quản trị viên
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Kiểm soát vận hành toàn cầu DocLib
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-red-600">
                        Chế độ bảo trì hệ thống
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Khóa toàn bộ tác vụ ghi dữ liệu trên toàn hệ thống để nâng
                        cấp kỹ thuật.
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

                  <div className="flex items-center justify-between p-4 border border-zinc-200 bg-zinc-50 rounded-none">
                    <div className="space-y-1">
                      <h4 className="text-xs font-semibold text-black">
                        Đăng ký tài khoản mới
                      </h4>
                      <p className="text-[10px] font-medium text-zinc-500 max-w-sm">
                        Cho phép hoặc chặn quyền đăng ký tài khoản cho người dùng
                        mới.
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
            </div>
          )}

          {activeSection === "apply_author" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Đăng ký Tác giả
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Tham gia đội ngũ sáng tạo nội dung
                  </p>
                </div>

                {user?.author_status === "pending" ? (
                  <div className="py-16 text-center space-y-4 border border-dashed border-zinc-200 bg-zinc-50 rounded-none">
                    <Clock className="w-8 h-8 text-zinc-400 mx-auto" />
                    <div>
                      <h4 className="text-sm font-semibold text-black">
                        Hồ sơ đang được xem xét
                      </h4>
                      <p className="text-xs font-medium text-zinc-500 mt-1 max-w-xs mx-auto">
                        Hệ thống đã ghi nhận đơn ứng tuyển của bạn. Vui lòng chờ
                        phản hồi từ đội ngũ Kiểm duyệt DocLib.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="p-6 border border-zinc-200 bg-zinc-50 space-y-4 rounded-none">
                      <div className="flex items-center gap-2 text-black border-b border-zinc-200 pb-3">
                        <Award className="w-4 h-4" />
                        <h4 className="text-[10px] font-semibold uppercase tracking-widest">
                          Đặc quyền của Tác giả DocLib
                        </h4>
                      </div>
                      <div className="grid md:grid-cols-2 gap-4">
                        {[
                          "Xuất bản tài liệu không giới hạn",
                          "Xây dựng cộng đồng độc giả riêng",
                          "Nhận nhuận bút & đóng góp tài chính",
                          "Huy hiệu Tác giả xác minh",
                        ].map((item, i) => (
                          <div key={i} className="flex items-start gap-2">
                            <Sparkles className="w-3.5 h-3.5 text-black shrink-0 mt-0.5" />
                            <span className="text-xs font-medium text-zinc-600">
                              {item}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-6">
                      <div className="space-y-2">
                        <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                          Động lực & Chuyên môn sáng tác
                        </label>
                        <textarea
                          value={motivation}
                          onChange={(e) => setMotivation(e.target.value)}
                          className="w-full min-h-[140px] p-4 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-medium outline-none resize-none transition-colors rounded-none"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-semibold text-black uppercase tracking-widest">
                          Portfolio / Sản phẩm tham chiếu (URL)
                        </label>
                        <input
                          type="text"
                          value={portfolio}
                          onChange={(e) => setPortfolio(e.target.value)}
                          className="w-full h-10 px-4 border border-zinc-200 focus:border-black bg-zinc-50 text-xs font-medium outline-none transition-colors rounded-none"
                        />
                      </div>
                    </div>

                    <div className="pt-6 mt-6 border-t border-zinc-200">
                      <button
                        onClick={handleApplyAuthor}
                        disabled={loading}
                        className="w-full h-10 bg-black text-white text-xs font-medium uppercase tracking-widest rounded-none flex items-center justify-center gap-2 disabled:opacity-50"
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
            </div>
          )}

          {activeSection === "notifications" && (
            <div className="border border-zinc-200 bg-white flex flex-col items-center justify-center min-h-[400px] text-center p-8">
              <Bell className="w-6 h-6 text-zinc-400 mb-4" />
              <h3 className="text-sm font-semibold text-black mb-1">
                Trung tâm thông báo
              </h3>
              <p className="text-xs font-medium text-zinc-500 max-w-xs leading-relaxed">
                Hệ thống đồng bộ thông báo đang được thiết lập cho tài khoản của bạn.
              </p>
            </div>
          )}

          {activeSection === "account" && (
            <div className="space-y-8">
              <div className="border border-zinc-200 bg-white p-8">
                <div className="border-b border-zinc-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-black">
                    Định danh & Bảo mật
                  </h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Quản lý lớp phòng thủ tài khoản
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="p-4 border border-zinc-200 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-none bg-zinc-50">
                    <div>
                      <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest block mb-1">
                        Trạng thái xác thực
                      </span>
                      <div className="text-xs font-semibold text-black flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4" /> Tài khoản đã định
                        danh cấp cao
                      </div>
                    </div>
                    <button className="px-6 py-2 border border-zinc-200 bg-white text-black text-xs font-medium rounded-none">
                      Đổi mật khẩu
                    </button>
                  </div>

                  <div className="p-4 border border-zinc-200 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-none bg-zinc-50">
                    <div>
                      <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-widest block mb-1">
                        Địa chỉ Email liên kết
                      </span>
                      <div className="text-xs font-semibold text-black">
                        {user?.email || "Chưa định danh"}
                      </div>
                    </div>
                    <button className="px-6 py-2 border border-zinc-200 bg-white text-black text-xs font-medium rounded-none">
                      Cập nhật Email
                    </button>
                  </div>
                </div>

                <div className="mt-6 flex items-start gap-3 bg-zinc-50 p-4 border border-zinc-200">
                  <AlertCircle className="w-4 h-4 text-black shrink-0 mt-0.5" />
                  <p className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest leading-relaxed">
                    DocLib yêu cầu xác thực hai lớp cho mọi thay đổi quan trọng
                    liên quan đến bảo mật và tài chính.
                  </p>
                </div>
              </div>

              <div className="border border-red-200 bg-red-50/20 p-8">
                <div className="border-b border-red-200 pb-4 mb-6">
                  <h3 className="text-sm font-semibold text-red-600">
                    Vùng nguy hiểm (Danger Zone)
                  </h3>
                  <p className="text-xs text-red-500/80 mt-1">
                    Các hành động không thể hoàn tác liên quan đến dữ liệu và
                    tài khoản
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <h4 className="text-xs font-semibold text-black">
                        Tải xuống dữ liệu (GDPR)
                      </h4>
                      <p className="text-[10px] text-zinc-500 mt-1">
                        Yêu cầu trích xuất toàn bộ dữ liệu cá nhân của bạn.
                      </p>
                    </div>
                    <button
                      onClick={() =>
                        showToast("Đã gửi yêu cầu trích xuất dữ liệu", "success")
                      }
                      className="px-6 py-2 border border-zinc-200 bg-white text-black text-xs font-medium rounded-none"
                    >
                      Yêu cầu trích xuất
                    </button>
                  </div>
                  <div className="h-px bg-zinc-200 w-full" />
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <h4 className="text-xs font-semibold text-black">
                        Xóa tài khoản vĩnh viễn
                      </h4>
                      <p className="text-[10px] text-zinc-500 mt-1">
                        Xóa hoàn toàn tài khoản và mọi dữ liệu liên kết. Không
                        thể khôi phục.
                      </p>
                    </div>
                    <button
                      onClick={() => showToast("Chức năng đang bảo trì", "error")}
                      className="px-6 py-2 border border-red-600 bg-black text-white text-xs font-medium rounded-none"
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
        className="max-w-md rounded-none border border-zinc-200 bg-white p-0"
      >
        <ModalHeader className="border-b border-zinc-200 p-6">
          <ModalTitle className="text-sm font-semibold text-black">
            Xác nhận thay đổi
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="p-6">
          <p className="text-xs font-medium text-zinc-500 leading-relaxed">
            {confirmModal?.type === "maintenance"
              ? `Bạn có chắc chắn muốn ${confirmModal?.value ? "kích hoạt" : "tắt"
              } chế độ bảo trì? Hành động này sẽ ảnh hưởng đến tất cả người dùng.`
              : `Bạn có chắc chắn muốn ${confirmModal?.value ? "mở lại" : "đóng"
              } cổng đăng ký tài khoản mới?`}
          </p>
        </ModalContent>
        <ModalFooter className="flex gap-3 border-t border-zinc-200 p-4 bg-zinc-50">
          <button
            onClick={() => setConfirmModal(null)}
            disabled={loading}
            className="flex-1 py-2 border border-zinc-200 bg-white text-xs font-medium text-black rounded-none disabled:opacity-50"
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
            className="flex-1 py-2 bg-black border border-black text-white text-xs font-medium rounded-none flex items-center justify-center disabled:opacity-50"
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
