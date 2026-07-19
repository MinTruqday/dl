"use client";

import React, { useState, useEffect } from "react";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2 } from "lucide-react";
import {
  getPrivacySettingsAPI,
  updatePrivacySettingsAPI,
} from "@/features/management/services/setting.service";
import PageLoader from "@/shared/components/common/PageLoader";

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

export default function PrivacySettingsPage() {
  const { showToast } = useToast();
  const [hideActivity, setHideActivity] = useState(false);
  const [hideLibrary, setHideLibrary] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await getPrivacySettingsAPI();
        setHideActivity(res.hide_activity || false);
        setHideLibrary(res.hide_library || false);
      } catch (error) {
        showToast("Không thể tải cài đặt riêng tư", "error");
      } finally {
        setInitialLoading(false);
      }
    };
    fetchSettings();
  }, [showToast]);

  const handleSavePrivacy = async () => {
    setLoading(true);
    try {
      await updatePrivacySettingsAPI({
        hide_activity: hideActivity,
        hide_library: hideLibrary,
      });
      showToast("Đã lưu thiết lập riêng tư", "success");
    } catch (error: any) {
      showToast(error.message || "Lỗi lưu thiết lập", "error");
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) return <PageLoader />;

  return (
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
  );
}
