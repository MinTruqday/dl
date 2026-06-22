"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { forgotPasswordAPI } from "@/features/auth/services/user_authentication.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Mail } from "lucide-react";

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
          <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-xl p-8 sm:p-10 transition-all duration-300">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold tracking-tight text-black">
                Quên mật khẩu
              </h1>
              <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Nhập email của bạn để nhận mã xác thực khôi phục mật khẩu.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="email"
                  className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setEmail(e.target.value)
                    }
                    className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-4 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
                    placeholder="name@example.com"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 h-12 text-xs font-bold text-white bg-black rounded-3xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
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
