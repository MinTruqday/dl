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
            <h1 className="text-2xl font-bold tracking-tight text-black">
              Mật khẩu mới
            </h1>
            <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
              Thiết lập mật khẩu mới cho tài khoản của bạn
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="new-password"
                className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
              >
                Mật khẩu mới
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <input
                  id="new-password"
                  name="new-password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={newPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setNewPassword(e.target.value)
                  }
                  className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-12 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm"
                  placeholder="Tối thiểu 6 ký tự"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                 type="submit"
                 disabled={loading}
                 className="w-full flex justify-center items-center gap-2 h-12 text-xs font-bold text-white bg-black rounded-3xl shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
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
    <div className="min-h-screen bg-zinc-50 font-sans selection:bg-zinc-900 selection:text-white flex flex-col">
      <Suspense fallback={<div className="flex-1 min-h-screen" />}>
        <ResetPasswordContent />
      </Suspense>
    </div>
  );
}
