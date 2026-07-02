"use client";

import { ChangeEvent, FormEvent, useState, useEffect, Suspense } from "react";
import { resetPasswordAPI } from "@/features/auth/services/user_authentication.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Eye, EyeOff, Lock } from "lucide-react";

function ResetPasswordContent() {
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  useEffect(() => {
    if (!token) {
      router.replace("/quen-mat-khau");
    }
  }, [token, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!newPassword || newPassword.length < 6) {
      showToast("Mật khẩu mới tối thiểu 6 ký tự", "error");
      return;
    }

    try {
      setLoading(true);
      const data = await resetPasswordAPI(token, newPassword);
      showToast(data.message || "Đã đặt lại mật khẩu thành công", "success");
      setTimeout(() => router.push("/dang-nhap"), 1500);
    } catch (err: any) {
      showToast(err.message || "Đặt lại mật khẩu thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
      <div className="w-full max-w-[420px]">
        <div className="auth-panel">
          <div className="text-center mb-8">
            <h1 className="text-[28px] font-semibold tracking-tight text-[#1D1D1F]">
              Mật khẩu mới
            </h1>
            <p className="mt-2 text-[15px] text-[#6E6E73]">
              Thiết lập mật khẩu mới cho tài khoản của bạn
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="new-password"
                className="block text-[13px] font-medium text-[#6E6E73] mb-2 ml-1"
              >
                Mật khẩu mới
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
                <input
                  id="new-password"
                  name="new-password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={newPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setNewPassword(e.target.value)
                  }
                  className="apple-input w-full pl-11 pr-12"
                  placeholder=""
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6E6E73]"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="pill-button w-full flex justify-center items-center gap-2 disabled:opacity-50"
              >
                {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                {loading ? "Đang xử lý" : "Cập nhật mật khẩu"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-white font-sans flex flex-col">
      <Suspense fallback={<div className="flex-1 min-h-screen" />}>
        <ResetPasswordContent />
      </Suspense>
    </div>
  );
}
