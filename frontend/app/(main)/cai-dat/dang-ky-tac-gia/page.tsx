"use client";

import React, { useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Clock } from "lucide-react";
import { redirect } from "next/navigation";

export default function ApplyAuthorPage() {
  const { user, isLoading: authLoading, refreshUser } = useAuth() as any;
  const { showToast } = useToast();
  
  const [motivation, setMotivation] = useState("");
  const [portfolio, setPortfolio] = useState("");
  const [loading, setLoading] = useState(false);

  if (authLoading) return null;
  if (user?.role === "author") {
    redirect("/cai-dat/tac-gia");
  }

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

  return (
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
  );
}
