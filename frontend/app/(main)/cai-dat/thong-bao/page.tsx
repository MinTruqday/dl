"use client";

import React, { useState, useEffect } from "react";
import {
  getAnnouncementSettingsAPI,
  updateAnnouncementSettingsAPI,
} from "@/features/notification/services/announcement.service";
import PageLoader from "@/shared/components/common/PageLoader";
import { useToast } from "@/shared/contexts/ToastContext";

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

export default function AnnouncementsSettingsPage() {
  const { showToast } = useToast();
  const [notifSettings, setNotifSettings] = useState<any>({});
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await getAnnouncementSettingsAPI();
        setNotifSettings(res || {});
      } catch (error) {
        showToast("Không thể tải cài đặt thông báo", "error");
      } finally {
        setInitialLoading(false);
      }
    };
    fetchSettings();
  }, [showToast]);

  if (initialLoading) return <PageLoader />;

  return (
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
  );
}
