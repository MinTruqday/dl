"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { forgotPasswordAPI } from "@/features/auth/services/user_authentication.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2 } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!email || !email.includes("@")) {
      showToast("Vui lòng nhập email hợp lệ", "error");
      return;
    }

    try {
      setLoading(true);
      const data = await forgotPasswordAPI(email);
      showToast(
        data.message || "Mã xác thực đã được gửi tới email của bạn",
        "success",
      );
      setTimeout(() => {
        window.location.href = `/verify?email=${encodeURIComponent(email)}`;
      }, 1500);
    } catch (err: any) {
      showToast(err.message || "Không thể gửi mã khôi phục", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 font-sans selection:bg-zinc-900 selection:text-white flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-[420px]">
          <div className="bg-white/90 backdrop-blur-xl border border-zinc-200/50 rounded-[2rem] shadow-[0_8px_40px_rgb(0,0,0,0.04)] p-8 sm:p-10">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold tracking-[-0.02em] text-black">
                Quên mật khẩu
              </h1>
              <p className="mt-2 text-xs font-medium text-zinc-500">
                Nhập email của bạn để nhận mã xác thực khôi phục mật khẩu.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-bold text-zinc-700 uppercase tracking-widest mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setEmail(e.target.value)
                  }
                  className="appearance-none block w-full px-4 py-3.5 bg-zinc-50/50 border border-zinc-200/80 rounded-2xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/5 focus:border-black text-sm text-black transition-all"
                  placeholder="name@example.com"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 h-12 text-sm font-bold text-white bg-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {loading ? "Đang xử lý" : "Gửi yêu cầu khôi phục"}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center border-t border-zinc-100 pt-6 flex flex-col gap-3">
              <span className="text-xs font-medium text-zinc-500">
                Đã có mã xác thực?{" "}
                <a href="/verify" className="font-bold text-black transition-colors hover:text-zinc-600 hover:underline">
                  Nhập mã ngay
                </a>
              </span>
              <a
                href="/login"
                className="text-xs font-medium text-zinc-500 transition-colors hover:text-black hover:underline"
              >
                Quay lại màn hình đăng nhập
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
