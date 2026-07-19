"use client";

import React, { useState, useEffect } from "react";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2 } from "lucide-react";
import {
  updateGeneralSettingsAPI,
} from "@/features/management/services/setting.service";
import PageLoader from "@/shared/components/common/PageLoader";
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

export default function AuthorSettingsPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const { showToast } = useToast();
  
  const [autoSave, setAutoSave] = useState(true);
  const [defaultVisibility, setDefaultVisibility] = useState("public");
  const [payoutInfo, setPayoutInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (user?.role !== "author") {
      redirect("/cai-dat/dang-ky-tac-gia");
    }
    
    setAutoSave(user?.settings?.auto_save ?? true);
    setDefaultVisibility(user?.settings?.default_visibility || "public");
    setPayoutInfo(user?.settings?.payout_info || "");
    setInitialLoading(false);
  }, [authLoading, user]);

  const handleUpdateGeneral = async (payload: any) => {
    try {
      await updateGeneralSettingsAPI(payload);
      refreshUser();
      return true;
    } catch (error: any) {
      showToast(error.message || "Lỗi lưu cấu hình", "error");
      return false;
    }
  };

  const handleSavePayout = async () => {
    setLoading(true);
    const success = await handleUpdateGeneral({ payout_info: payoutInfo });
    if (success) {
      showToast("Đã lưu thông tin", "success");
    }
    setLoading(false);
  };

  if (initialLoading || authLoading) return <PageLoader />;

  return (
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
          onClick={handleSavePayout}
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
