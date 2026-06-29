"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalFooter } from "@/shared/components/ui/Modal";
import { getPrivacySettingsAPI, updatePrivacySettingsAPI, updateGeneralSettingsAPI } from "@/features/provision/services/system_setting.service";
import { getNotificationSettingsAPI, updateNotificationSettingsAPI } from "@/features/communication/services/push_notification.service";
import { getMaintenanceModeAPI, getAdminConfigAPI, toggleMaintenanceModeAPI, updateAdminConfigAPI } from "@/features/provision/services/system_operation.service";
import { Shield, Bell, Lock, ChevronRight, Save, Loader2, Sparkles, PenTool, ShieldCheck, Zap, UserPlus, Award, Clock, AlertCircle, ShieldAlert } from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";

type TabKey = "privacy" | "notifications" | "account" | "apply_author" | "author" | "moderator" | "admin";

export default function SettingsPage() {
  const { showToast } = useToast();
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const [visible, setVisible] = useState(false);
  const [activeSection, setActiveSection] = useState<TabKey>("privacy");
  const [loading, setLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{ type: "maintenance" | "registration"; value: boolean } | null>(null);

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

      try { const notifRes = await getNotificationSettingsAPI(); setNotifSettings(notifRes.data || {}); } catch (e) {}

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
        setPayoutInfo(user.settings.payout_info || "");
      }
    } catch (err: any) { showToast("Lỗi đồng bộ", "error"); }
  }, [user, showToast]);

  useEffect(() => { if (user) { requestAnimationFrame(() => setVisible(true)); fetchData(); } }, [user, fetchData]);

  const handleUpdateGeneral = async (newSettings: any) => {
    try { await updateGeneralSettingsAPI(newSettings); refreshUser?.(); return true; } catch (err: any) { showToast("Lỗi cập nhật", "error"); return false; }
  };

  const handleSavePrivacy = async () => {
    setLoading(true);
    try {
      await updatePrivacySettingsAPI({ hide_reading_activity: hideActivity, hide_library: hideLibrary });
      showToast("Đã cập nhật quyền riêng tư", "success");
    } catch (err: any) { showToast("Lỗi cập nhật riêng tư", "error"); } finally { setLoading(false); }
  };

  const handleApplyAuthor = async () => {
    if (!motivation) return showToast("Nhập lý do", "error");
    setLoading(true);
    try { showToast("Gửi thành công", "success"); setMotivation(""); setPortfolio(""); refreshUser?.(); } catch (err: any) { showToast("Lỗi gửi đơn", "error"); } finally { setLoading(false); }
  };

  const handleToggleMaintenance = async () => {
    setLoading(true);
    try {
      await toggleMaintenanceModeAPI(!maintenanceMode);
      setMaintenanceMode(!maintenanceMode);
      showToast(!maintenanceMode ? "Đã bật bảo trì" : "Đã tắt bảo trì", "success");
      setConfirmModal(null);
    } catch (err: any) { showToast("Lỗi thao tác", "error"); } finally { setLoading(false); }
  };

  const handleToggleRegistration = async () => {
    setLoading(true);
    try {
      await updateAdminConfigAPI({ registration_enabled: !registrationEnabled });
      setRegistrationEnabled(!registrationEnabled);
      showToast(!registrationEnabled ? "Đã mở đăng ký" : "Đã đóng đăng ký", "success");
      setConfirmModal(null);
    } catch (err: any) { showToast("Lỗi thao tác", "error"); } finally { setLoading(false); }
  };

  const CustomSwitch = ({ active, onToggle }: { active: boolean; onToggle: () => void }) => (
    <button onClick={onToggle} className={`w-[50px] h-[30px] rounded-full relative shrink-0 transition-colors duration-300 ${active ? "bg-[#34C759]" : "bg-[#E8E8ED]"}`}>
      <div className={`absolute top-[2px] w-[26px] h-[26px] bg-white rounded-full shadow-sm transition-transform duration-300 ${active ? "translate-x-[22px]" : "translate-x-[2px]"}`} />
    </button>
  );

  if (authLoading) return <PageLoader />;

  const sections = [
    { id: "privacy", label: "Quyền riêng tư", icon: Shield, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "notifications", label: "Thông báo", icon: Bell, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    { id: "account", label: "Tài khoản & Bảo mật", icon: Lock, roles: ["reader", "potential_author", "author", "moderator", "admin"] },
    ...(user?.role === "reader" && user?.author_status !== "pending" && user?.author_status !== "approved" ? [{ id: "apply_author", label: "Tác giả tiềm năng", icon: UserPlus, roles: ["reader"] }] : []),
    { id: "author", label: "Cấu hình Tác giả", icon: PenTool, roles: ["author", "admin"] },
    { id: "moderator", label: "Kiểm duyệt viên", icon: ShieldCheck, roles: ["moderator", "admin"] },
    { id: "admin", label: "Quản trị viên", icon: Zap, roles: ["admin"] }
  ].filter((s) => !user || s.roles.includes(user.role));

  return (
    <div className="w-full max-w-[1200px] mx-auto px-6 py-8 min-h-[calc(100dvh-56px)] font-sans text-[#1D1D1F]">


      <div className={`grid lg:grid-cols-12 gap-8 transition-opacity duration-500 ${visible ? "opacity-100" : "opacity-0"}`} style={{ transitionDelay: "100ms" }}>
        <aside className="lg:col-span-4 xl:col-span-4 space-y-6">
          <div className="bg-[#F5F5F7] rounded-[24px] p-6 space-y-4">
            <div className="text-[13px] font-medium text-[#6E6E73] mb-2 px-2">Danh mục</div>
            <nav className="flex flex-col gap-1">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <button key={section.id} onClick={() => setActiveSection(section.id as TabKey)} className={`flex items-center justify-between px-4 py-3 rounded-[14px] transition-colors ${activeSection === section.id ? "bg-[#0071E3] text-white" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`}>
                    <div className="flex items-center gap-3 font-medium text-[15px]"><Icon className="w-5 h-5" /> {section.label}</div>
                  </button>
                );
              })}
            </nav>
          </div>
          <div className="bg-[#F5F5F7] rounded-[24px] p-6">
            <div className="text-[13px] font-medium text-[#6E6E73] mb-4">Định danh hiện tại</div>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white rounded-[14px] flex items-center justify-center text-[15px] font-semibold text-[#1D1D1F] shadow-sm uppercase">{user?.role?.slice(0, 3)}</div>
              <div>
                <p className="text-[15px] font-medium text-[#1D1D1F]">{user?.role === "admin" ? "Quản trị viên" : user?.role === "author" ? "Tác giả" : user?.role === "moderator" ? "Kiểm duyệt viên" : user?.role === "potential_author" ? "Tác giả tiềm năng" : "Độc giả"}</p>
                <p className="text-[13px] text-[#6E6E73] mt-0.5">{user?.email || "Chưa định danh"}</p>
              </div>
            </div>
          </div>
        </aside>

        <main className="lg:col-span-8 xl:col-span-8">
          <div className="bg-[#F5F5F7] rounded-[24px] p-8 min-h-[600px]">
            {activeSection === "privacy" && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-[20px] font-semibold text-[#1D1D1F]">Quyền riêng tư</h2>
                  <p className="text-[15px] text-[#6E6E73]">Thiết lập khả năng hiển thị cá nhân</p>
                </div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">Chế độ đọc ẩn danh</h4>
                      <p className="text-[14px] text-[#6E6E73] mt-1">Không hiển thị lịch sử đọc trên bảng xếp hạng.</p>
                    </div>
                    <CustomSwitch active={hideActivity} onToggle={() => setHideActivity(!hideActivity)} />
                  </div>
                  <div className="p-5 flex items-center justify-between">
                    <div>
                      <h4 className="text-[17px] font-medium text-[#1D1D1F]">Thư viện nội bộ</h4>
                      <p className="text-[14px] text-[#6E6E73] mt-1">Giới hạn truy cập bộ sưu tập cá nhân.</p>
                    </div>
                    <CustomSwitch active={hideLibrary} onToggle={() => setHideLibrary(!hideLibrary)} />
                  </div>
                </div>
                <div className="flex justify-end pt-4"><button onClick={handleSavePrivacy} disabled={loading} className="pill-button">{loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Lưu thay đổi"}</button></div>
              </div>
            )}

            {activeSection === "author" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Cấu hình Tác giả</h2><p className="text-[15px] text-[#6E6E73]">Quản lý sáng tác</p></div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  <div className="p-5 flex items-center justify-between">
                    <div><h4 className="text-[17px] font-medium text-[#1D1D1F]">Tự động sao lưu</h4><p className="text-[14px] text-[#6E6E73]">Sao lưu 30 giây.</p></div>
                    <CustomSwitch active={autoSave} onToggle={async () => { const s = await handleUpdateGeneral({ auto_save: !autoSave }); if(s) setAutoSave(!autoSave); }} />
                  </div>
                  <div className="p-5 space-y-3">
                    <h4 className="text-[17px] font-medium text-[#1D1D1F]">Trạng thái xuất bản mặc định</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {["public", "private"].map((m) => (
                        <button key={m} onClick={async () => { const s = await handleUpdateGeneral({ default_visibility: m }); if(s) setDefaultVisibility(m); }} className={`py-3 rounded-[14px] font-medium transition-colors ${defaultVisibility === m ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] text-[#1D1D1F]"}`}>{m === "public" ? "Công khai" : "Riêng tư"}</button>
                      ))}
                    </div>
                  </div>
                  <div className="p-5 space-y-3">
                    <h4 className="text-[17px] font-medium text-[#1D1D1F]">Thông tin thụ hưởng</h4>
                    <textarea value={payoutInfo} onChange={(e) => setPayoutInfo(e.target.value)} className="apple-input w-full min-h-[100px] resize-none py-3" placeholder="Ngân hàng..."></textarea>
                  </div>
                </div>
                <div className="flex justify-end pt-4"><button onClick={async () => { setLoading(true); await handleUpdateGeneral({ payout_info: payoutInfo }); setLoading(false); showToast("Đã lưu", "success"); }} className="pill-button">Lưu cấu hình</button></div>
              </div>
            )}

            {activeSection === "moderator" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Kiểm duyệt viên</h2></div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  <div className="p-5 flex items-center justify-between">
                    <div><h4 className="text-[17px] font-medium text-[#1D1D1F]">Thông báo vi phạm</h4></div>
                    <CustomSwitch active={modNotifs} onToggle={async () => { const s = await handleUpdateGeneral({ mod_notifs: !modNotifs }); if(s) setModNotifs(!modNotifs); }} />
                  </div>
                  <div className="p-5 flex items-center justify-between">
                    <div><h4 className="text-[17px] font-medium text-[#1D1D1F]">Tự động làm mới</h4></div>
                    <CustomSwitch active={autoRefresh} onToggle={async () => { const s = await handleUpdateGeneral({ auto_refresh: !autoRefresh }); if(s) setAutoRefresh(!autoRefresh); }} />
                  </div>
                </div>
              </div>
            )}

            {activeSection === "admin" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Quản trị viên</h2></div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  <div className="p-5 flex items-center justify-between bg-[#FFF0F0] rounded-t-[18px]">
                    <div><h4 className="text-[17px] font-medium text-[#FF3B30]">Bảo trì hệ thống</h4><p className="text-[14px] text-[#FF6961]">Khóa ghi dữ liệu.</p></div>
                    <CustomSwitch active={maintenanceMode} onToggle={() => setConfirmModal({ type: "maintenance", value: !maintenanceMode })} />
                  </div>
                  <div className="p-5 flex items-center justify-between">
                    <div><h4 className="text-[17px] font-medium text-[#1D1D1F]">Đăng ký mới</h4></div>
                    <CustomSwitch active={registrationEnabled} onToggle={() => setConfirmModal({ type: "registration", value: !registrationEnabled })} />
                  </div>
                </div>
              </div>
            )}

            {activeSection === "apply_author" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Tác giả tiềm năng</h2></div>
                {user?.author_status === "pending" ? (
                  <div className="py-12 text-center bg-white rounded-[18px]"><Clock className="w-12 h-12 text-[#6E6E73] mx-auto mb-4" /><p className="text-[15px] font-medium text-[#1D1D1F]">Đang xem xét</p></div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-white p-6 rounded-[18px] shadow-sm space-y-4">
                      <div className="space-y-2"><label className="text-[13px] font-medium text-[#6E6E73]">Lý do</label><textarea value={motivation} onChange={(e) => setMotivation(e.target.value)} className="apple-input w-full min-h-[100px] resize-none" /></div>
                      <div className="space-y-2"><label className="text-[13px] font-medium text-[#6E6E73]">Portfolio</label><input type="text" value={portfolio} onChange={(e) => setPortfolio(e.target.value)} className="apple-input w-full" /></div>
                    </div>
                    <button onClick={handleApplyAuthor} disabled={loading} className="pill-button w-full">{loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Ứng tuyển"}</button>
                  </div>
                )}
              </div>
            )}

            {activeSection === "notifications" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Thông báo</h2></div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  {[{ id: "notifyCommunity", label: "Cộng đồng" }, { id: "notifyFinance", label: "Tài chính" }, { id: "notifyUpdates", label: "Cập nhật" }].map((item, i) => (
                    <div key={i} className="p-5 flex items-center justify-between">
                      <div><h4 className="text-[17px] font-medium text-[#1D1D1F]">{item.label}</h4></div>
                      <div className="flex gap-6">
                        <div className="flex items-center gap-2"><span className="text-[13px] text-[#6E6E73]">Email</span><CustomSwitch active={notifSettings[item.id]?.email ?? false} onToggle={() => {}} /></div>
                        <div className="flex items-center gap-2"><span className="text-[13px] text-[#6E6E73]">App</span><CustomSwitch active={notifSettings[item.id]?.inapp ?? false} onToggle={() => {}} /></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeSection === "account" && (
              <div className="space-y-8">
                <div><h2 className="text-[20px] font-semibold text-[#1D1D1F]">Tài khoản</h2></div>
                <div className="bg-white rounded-[18px] divide-y divide-[#E8E8ED] shadow-sm">
                  <div className="p-5 flex items-center justify-between">
                    <div><h4 className="text-[15px] font-medium text-[#1D1D1F]">Email</h4><p className="text-[14px] text-[#6E6E73]">{user?.email}</p></div>
                  </div>
                </div>
                <div className="bg-[#FFF0F0] rounded-[18px] p-6 mt-8">
                  <h3 className="text-[17px] font-medium text-[#FF3B30] mb-4">Vùng nguy hiểm</h3>
                  <button className="py-2 px-4 bg-[#FF3B30] text-white rounded-[14px] text-[15px] font-medium">Xóa tài khoản</button>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      <Modal isOpen={!!confirmModal} onClose={() => !loading && setConfirmModal(null)} className="max-w-sm rounded-[24px] bg-[#F5F5F7] p-0 border-none shadow-2xl">
        <ModalHeader className="p-6"><ModalTitle className="text-[20px] font-semibold text-[#1D1D1F]">Xác nhận</ModalTitle></ModalHeader>
        <ModalContent className="p-6 pt-0"><p className="text-[15px] text-[#6E6E73]">Bạn chắc chắn thay đổi hệ thống?</p></ModalContent>
        <ModalFooter className="p-4 flex justify-end gap-3 bg-white rounded-b-[24px]">
          <button onClick={() => setConfirmModal(null)} disabled={loading} className="px-4 py-2 text-[#0071E3] font-medium rounded-full hover:bg-[#F5F5F7]">Hủy</button>
          <button onClick={() => { if(confirmModal?.type === "maintenance") handleToggleMaintenance(); else handleToggleRegistration(); }} disabled={loading} className="pill-button">{loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Xác nhận"}</button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
