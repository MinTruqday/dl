"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import {
  getPrivacySettingsAPI,
  updatePrivacySettingsAPI,
  updateGeneralSettingsAPI,
} from "@/features/management/services/setting.service";
import {
  getAnnouncementSettingsAPI,
  updateAnnouncementSettingsAPI,
} from "@/features/notification/services/announcement.service";
import {
  getMaintenanceModeAPI,
  getAdminConfigAPI,
  toggleMaintenanceModeAPI,
  updateAdminConfigAPI,
} from "@/features/management/services/health.service";
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
import PageLoader from "@/shared/components/common/PageLoader";

type TabKey =
  | "privacy"
  | "announcements"
  | "account"
  | "apply_author"
  | "author"
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
        const notifRes = await getAnnouncementSettingsAPI();
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
      showToast("Lỗi đồng bộ dữ liệu cấu hình", "error");
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
      showToast("Lỗi cập nhật thay đổi cấu hình", "error");
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
      showToast("Cập nhật thiết lập quyền riêng tư hoàn tất", "success");
    } catch (err: any) {
      showToast("Lỗi cập nhật thiết lập quyền riêng tư", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAuthor = async () => {
    if (!motivation) return showToast("Dữ liệu lý do ứng tuyển không được để trống", "error");
    setLoading(true);
    try {
      const { API_URL, getToken } = await import("@/features/authentication/services/session.service");
      const res = await fetch(`${API_URL}/ho-so/tac-gia/ung-tuyen`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ motivation, portfolio })
      });
      if (!res.ok) throw new Error("Lỗi gửi yêu cầu ứng tuyển tác giả");
      showToast("Gửi yêu cầu ứng tuyển hoàn tất", "success");
      setMotivation("");
      setPortfolio("");
      refreshUser?.();
    } catch (err: any) {
      showToast("Lỗi gửi yêu cầu ứng tuyển tác giả", "error");
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
        !maintenanceMode ? "Kích hoạt chế độ bảo trì hệ thống hoàn tất" : "Tắt chế độ bảo trì hệ thống hoàn tất",
        "success",
      );
      setConfirmModal(null);
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái bảo trì", "error");
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
        !registrationEnabled ? "Kích hoạt đăng ký tài khoản hoàn tất" : "Vô hiệu hóa đăng ký tài khoản hoàn tất",
        "success",
      );
      setConfirmModal(null);
    } catch (err: any) {
      showToast("Lỗi cập nhật trạng thái đăng ký", "error");
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
      className={`w-[50px] h-[30px] rounded-full relative shrink-0 transition-colors duration-300 ${active ? "bg-[#34C759]" : "bg-[#E8E8ED]"}`}
    >
      <div
        className={`absolute top-[2px] w-[26px] h-[26px] bg-white rounded-full transition-transform duration-300 ${active ? "translate-x-[22px]" : "translate-x-[2px]"}`}
      />
    </button>
  );

  if (authLoading) return <PageLoader />;

  const sections = [
    {
      id: "privacy",
      label: "Quyền riêng tư",
      icon: Shield,
      roles: ["reader", "potential_author", "author", "admin"],
    },
    {
      id: "announcements",
      label: "Thông báo",
      icon: Bell,
      roles: ["reader", "potential_author", "author", "admin"],
    },
    {
      id: "account",
      label: "Tài khoản & Bảo mật",
      icon: Lock,
      roles: ["reader", "potential_author", "author", "admin"],
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

    { id: "admin", label: "Cấu hình hệ thống", icon: Zap, roles: ["admin"] },
  ].filter((s) => !user || s.roles.includes(user.role));

  return (
    <div className="w-full h-full flex flex-col font-sans text-[#1D1D1F]">
      <div
        className={`flex flex-col md:flex-row gap-6 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{ transitionDelay: "100ms" }}
      >
        <aside className="w-full md:w-[320px] shrink-0 space-y-6 sticky top-0 h-fit">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
            <p className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Danh mục
            </p>
            <nav className="flex flex-col gap-1.5">
              {sections.map((section) => {
                const active = activeSection === section.id;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id as TabKey)}
                    className={`flex items-center justify-between px-4 py-3 text-[15px] rounded-[10px] transition-colors ${active ? "bg-white text-[#0071E3] font-medium" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}
                  >
                    <span className="truncate text-left">{section.label}</span>
                    {active && <ChevronRight className="w-4 h-4 shrink-0" />}
                  </button>
                );
              })}
            </nav>
          </div>
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6">
            <div className="text-[13px] font-medium text-[#6E6E73] mb-4">
              Định danh hiện tại
            </div>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white rounded-[10px] flex items-center justify-center text-[15px] font-semibold text-[#1D1D1F] uppercase">
                {user?.role?.slice(0, 3)}
              </div>
              <div>
                <p className="text-[15px] font-medium text-[#1D1D1F]">
                  {user?.role === "admin"
                    ? "Quản trị viên"
                    : user?.role === "author"
                      ? "Tác giả"
                      : user?.role === "potential_author"
                          ? "Tác giả tiềm năng"
                          : "Độc giả"}
                </p>
                <p className="text-[13px] text-[#6E6E73] mt-0.5">
                  {user?.email || "Chưa định danh"}
                </p>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 xl:col-span-8">
          <div className="bg-[#F5F5F7] md:bg-transparent rounded-[18px] md:rounded-none p-6 md:p-0 md:pt-6 min-h-[600px]">
            {activeSection === "privacy" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-1">
                    Quyền riêng tư
                  </h2>
                  <p className="text-[15px] text-[#6E6E73]">
                    Thiết lập khả năng hiển thị cá nhân
                  </p>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED]">
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                        Chế độ đọc ẩn danh
                      </h4>
                      <p className="text-[14px] text-[#6E6E73] mt-1">
                        Không hiển thị lịch sử đọc trên bảng xếp hạng.
                      </p>
                    </div>
                    <CustomSwitch
                      active={hideActivity}
                      onToggle={() => setHideActivity(!hideActivity)}
                    />
                  </div>
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                        Thư viện nội bộ
                      </h4>
                      <p className="text-[14px] text-[#6E6E73] mt-1">
                        Giới hạn truy cập bộ sưu tập cá nhân.
                      </p>
                    </div>
                    <CustomSwitch
                      active={hideLibrary}
                      onToggle={() => setHideLibrary(!hideLibrary)}
                    />
                  </div>
                </div>
                <div className="flex justify-end pt-4">
                  <button
                    onClick={handleSavePrivacy}
                    disabled={loading}
                    className="pill-button"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "Lưu thay đổi"
                    )}
                  </button>
                </div>
              </div>
            )}

            {activeSection === "author" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-1">
                    Cấu hình Tác giả
                  </h2>
                  <p className="text-[15px] text-[#6E6E73]">Quản lý sáng tác</p>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED]">
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                        Tự động sao lưu
                      </h4>
                      <p className="text-[14px] text-[#6E6E73]">
                        Sao lưu 30 giây.
                      </p>
                    </div>
                    <CustomSwitch
                      active={autoSave}
                      onToggle={async () => {
                        const s = await handleUpdateGeneral({
                          auto_save: !autoSave,
                        });
                        if (s) setAutoSave(!autoSave);
                      }}
                    />
                  </div>
                  <div className="p-5 space-y-3">
                    <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                      Trạng thái xuất bản mặc định
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      {["public", "private"].map((m) => (
                        <button
                          key={m}
                          onClick={async () => {
                            const s = await handleUpdateGeneral({
                              default_visibility: m,
                            });
                            if (s) setDefaultVisibility(m);
                          }}
                          className={`py-3 rounded-[10px] font-medium transition-colors ${defaultVisibility === m ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#1D1D1F]"}`}
                        >
                          {m === "public" ? "Công khai" : "Riêng tư"}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="p-5 space-y-3">
                    <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                      Thông tin thụ hưởng
                    </h4>
                    <textarea
                      value={payoutInfo}
                      onChange={(e) => setPayoutInfo(e.target.value)}
                      className="apple-input w-full min-h-[100px] resize-none py-3"
                      placeholder=""
                    ></textarea>
                  </div>
                </div>
                <div className="flex justify-end pt-4">
                  <button
                    onClick={async () => {
                      setLoading(true);
                      await handleUpdateGeneral({ payout_info: payoutInfo });
                      setLoading(false);
                      showToast("Lưu cấu hình hệ thống hoàn tất", "success");
                    }}
                    className="pill-button"
                  >
                    Lưu cấu hình
                  </button>
                </div>
              </div>
            )}



            {activeSection === "admin" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                    Cấu hình hệ thống
                  </h2>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED]">
                  <div className="p-5 flex items-center justify-between bg-[#FFF0F0] rounded-t-[18px]">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#FF3B30]">
                        Bảo trì hệ thống
                      </h4>
                      <p className="text-[14px] text-[#FF6961]">
                        Khóa ghi dữ liệu.
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
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                        Đăng ký mới
                      </h4>
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
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                    Tác giả tiềm năng
                  </h2>
                </div>
                {user?.author_status === "pending" ? (
                  <div className="py-12 text-center bg-white rounded-[18px]">
                    <Clock className="w-12 h-12 text-[#6E6E73] mx-auto mb-4" />
                    <p className="text-[15px] font-medium text-[#1D1D1F]">
                      Đang xem xét
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-white p-6 rounded-[18px] space-y-4">
                      <div className="space-y-2">
                        <label className="text-[13px] font-medium text-[#6E6E73]">
                          Lý do
                        </label>
                        <textarea
                          value={motivation}
                          onChange={(e) => setMotivation(e.target.value)}
                          className="apple-input w-full min-h-[100px] resize-none"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[13px] font-medium text-[#6E6E73]">
                          Portfolio
                        </label>
                        <input
                          type="text"
                          value={portfolio}
                          onChange={(e) => setPortfolio(e.target.value)}
                          className="apple-input w-full"
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleApplyAuthor}
                      disabled={loading}
                      className="pill-button w-full"
                    >
                      {loading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        "Ứng tuyển"
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeSection === "announcements" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                    Thông báo
                  </h2>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED]">
                  {[
                    { id: "notifyCommunity", label: "Cộng đồng" },
                    { id: "notifyFinance", label: "Tài chính" },
                    { id: "notifyUpdates", label: "Cập nhật" },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="p-5 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="text-[17px] font-medium text-[#1D1D1F]">
                          {item.label}
                        </h4>
                      </div>
                      <div className="flex gap-6">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] text-[#6E6E73]">
                            Email
                          </span>
                          <CustomSwitch
                            active={notifSettings[item.id]?.email ?? false}
                            onToggle={async () => {
                              const newSettings = { ...notifSettings, [item.id]: { ...notifSettings[item.id], email: !(notifSettings[item.id]?.email ?? false) } };
                              setNotifSettings(newSettings);
                              try {
                                await updateAnnouncementSettingsAPI(newSettings);
                              } catch(e) {}
                            }}
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] text-[#6E6E73]">
                            App
                          </span>
                          <CustomSwitch
                            active={notifSettings[item.id]?.inapp ?? false}
                            onToggle={async () => {
                              const newSettings = { ...notifSettings, [item.id]: { ...notifSettings[item.id], inapp: !(notifSettings[item.id]?.inapp ?? false) } };
                              setNotifSettings(newSettings);
                              try {
                                await updateAnnouncementSettingsAPI(newSettings);
                              } catch(e) {}
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
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-4">
                    Tài khoản
                  </h2>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED]">
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[15px] font-medium text-[#1D1D1F]">
                        Email
                      </h4>
                      <p className="text-[14px] text-[#6E6E73]">
                        {user?.email}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="bg-[#FFF0F0] rounded-[18px] p-6 mt-8">
                  <h3 className="text-[17px] font-medium text-[#FF3B30] mb-4">
                    Vùng nguy hiểm
                  </h3>
                  <button 
                    onClick={async () => {
                      if (!confirm("Bạn có chắc chắn muốn xóa tài khoản vĩnh viễn?")) return;
                      const { API_URL, getToken, removeToken } = await import("@/features/authentication/services/session.service");
                      try {
                        const res = await fetch(`${API_URL}/ho-so/xoa-tai-khoan`, { method: "DELETE", headers: { Authorization: `Bearer ${getToken()}` } });
                        if (res.ok) {
                          removeToken();
                          window.location.href = "/dang-nhap";
                        }
                      } catch(e) {}
                    }}
                    className="py-2 px-4 bg-[#FF3B30] text-white rounded-[10px] text-[15px] font-medium"
                  >
                    Xóa tài khoản
                  </button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !loading && setConfirmModal(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>
            Xác nhận
          </ModalTitle>
        </ModalHeader>
        <ModalContent>
          <p className="text-[15px] text-[#6E6E73]">
            Bạn chắc chắn thay đổi hệ thống?
          </p>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => setConfirmModal(null)}
            disabled={loading}
            className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7]"
          >
            Hủy
          </button>
          <button
            onClick={() => {
              if (confirmModal?.type === "maintenance")
                handleToggleMaintenance();
              else handleToggleRegistration();
            }}
            disabled={loading}
            className="pill-button"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "Xác nhận"
            )}
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
