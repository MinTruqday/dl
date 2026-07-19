"use client";

import React from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";

export default function AccountSettingsPage() {
  const { user } = useAuth() as any;

  return (
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
  );
}
