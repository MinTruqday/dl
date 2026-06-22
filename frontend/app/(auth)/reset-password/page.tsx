"use client";

import { ChangeEvent, FormEvent, useState, useEffect, Suspense } from "react";
import { resetPasswordAPI } from "@/features/auth/services/user_authentication.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Eye, EyeOff } from "lucide-react";

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
      router.replace("/forgot-password");
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
      setTimeout(() => router.push("/login"), 1500);
    } catch (err: any) {
      showToast(err.message || "Đặt lại mật khẩu thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
      <div className="w-full max-w-[420px]">
        <div className="bg-white/90 backdrop-blur-xl border border-zinc-200/50 rounded-[2rem] shadow-[0_8px_40px_rgb(0,0,0,0.04)] p-8 sm:p-10">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold tracking-[-0.02em] text-black">
              Mật khẩu mới
            </h1>
            <p className="mt-2 text-xs font-medium text-zinc-500">
              Thiết lập mật khẩu mới cho tài khoản của bạn
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="new-password"
                className="block text-xs font-bold text-zinc-700 uppercase tracking-widest mb-2 ml-1"
              >
                Mật khẩu mới
              </label>
              <div className="relative">
                <input
                  id="new-password"
                  name="new-password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={newPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setNewPassword(e.target.value)
                  }
                  className="appearance-none block w-full px-4 py-3.5 bg-zinc-50/50 border border-zinc-200/80 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/5 focus:border-black text-sm text-black transition-all pr-12"
                  placeholder="Tối thiểu 6 ký tự"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-black transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-2 h-12 text-sm font-bold text-white bg-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
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
