"use client";

import React, { useState, useEffect } from "react";
import {
  getMaintenanceModeAPI,
  getAdminConfigAPI,
  toggleMaintenanceModeAPI,
  updateAdminConfigAPI,
} from "@/features/management/services/health.service";
import PageLoader from "@/shared/components/common/PageLoader";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { redirect } from "next/navigation";

const CustomSwitch = ({
  active,
  onToggle,
}: {
  active: boolean;
  onToggle: () => void;
}) => (
  <button
    type="button"
    onClick={onToggle}
    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out ${
      active ? "bg-[#34C759]" : "bg-[#E8E8ED]"
    }`}
  >
    <span
      className={`inline-block h-5 w-5 transform rounded-full bg-white transition duration-200 ease-in-out shadow-sm ${
        active ? "translate-x-5" : "translate-x-1"
      }`}
    />
  </button>
);

export default function AdminSettingsPage() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const { showToast } = useToast();
  
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [registrationEnabled, setRegistrationEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  
  const [confirmModal, setConfirmModal] = useState<{
    type: "maintenance" | "registration";
    value: boolean;
  } | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (user?.role !== "admin") {
      redirect("/cai-dat/tai-khoan");
    }

    const fetchAdminSettings = async () => {
      try {
        const [maintenanceRes, configRes] = await Promise.all([
          getMaintenanceModeAPI(),
          getAdminConfigAPI(),
        ]);
        setMaintenanceMode(maintenanceRes.active);
        setRegistrationEnabled(configRes.registration_enabled ?? true);
      } catch (error) {
        showToast("Lỗi tải thông tin quản trị", "error");
      } finally {
        setInitialLoading(false);
      }
    };

    fetchAdminSettings();
  }, [authLoading, user, showToast]);

  const handleToggleMaintenance = async () => {
    if (!confirmModal) return;
    setLoading(true);
    try {
      const res = await toggleMaintenanceModeAPI();
      setMaintenanceMode(res.active);
      showToast(
        res.active ? "Đã BẬT bảo trì" : "Đã TẮT bảo trì",
        "success"
      );
    } catch (error: any) {
      showToast(error.message || "Lỗi chuyển trạng thái", "error");
    } finally {
      setLoading(false);
      setConfirmModal(null);
    }
  };

  const handleToggleRegistration = async () => {
    if (!confirmModal) return;
    setLoading(true);
    try {
      const newValue = confirmModal.value;
      const res = await updateAdminConfigAPI({ registration_enabled: newValue });
      setRegistrationEnabled(res.registration_enabled);
      showToast(
        res.registration_enabled ? "Đã BẬT đăng ký" : "Đã TẮT đăng ký",
        "success"
      );
    } catch (error: any) {
      showToast(error.message || "Lỗi lưu cấu hình", "error");
    } finally {
      setLoading(false);
      setConfirmModal(null);
    }
  };

  if (initialLoading || authLoading) return <PageLoader />;

  return (
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

      <Modal
        isOpen={!!confirmModal}
        onClose={() => !loading && setConfirmModal(null)}
        className="max-w-sm"
      >
        <ModalHeader>
          <ModalTitle>Xác nhận</ModalTitle>
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
