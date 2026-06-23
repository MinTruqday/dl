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
      showToast(data.message || "Mã xác thực đã được gửi tới email của bạn", "success");
      setTimeout(() => {
        window.location.href = `/verify?email=${encodeURIComponent(email)}`;
      }, 1500);
    } catch (err: any) {
      showToast(err.message || "Không thể gửi mã khôi phục", "error");
    } finally {
      loading && setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] font-sans selection:bg-[#0071E3] selection:text-white flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-16">
        <div className="w-full max-w-[400px]">
          <div className="bg-white rounded-[28px] p-8 sm:p-10 transition-all duration-300">
            <div className="text-center mb-10">
              <h1 className="text-[26px] font-bold tracking-tight text-[#1D1D1F]">
                Quên mật khẩu
              </h1>
              <p className="mt-2 text-sm text-[#6E6E73]">
                Nhập email của bạn để nhận mã xác thực khôi phục mật khẩu.
              </p>
            </div>

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label htmlFor="email" className="block text-xs font-medium text-[#6E6E73] px-1">
                  Địa chỉ email
                </label>
                <div className="relative">
                  <Mail className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6E6E73]" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                    className="w-full bg-[#F5F5F7] border-none rounded-full pl-12 pr-5 py-3.5 text-sm font-normal text-[#1D1D1F] focus:bg-white focus:ring-2 focus:ring-[#0071E3] focus:outline-none placeholder:text-[#AEAEB2] transition-all duration-200"
                    placeholder="name@example.com"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 h-12 text-sm font-medium text-white bg-[#0071E3] hover:bg-[#0055C6] rounded-full transition-all duration-200 disabled:bg-[#AEAEB2] disabled:cursor-not-allowed"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {loading ? "Đang xử lý" : "Gửi yêu cầu khôi phục"}
                </button>
              </div>
            </form>

            <div className="mt-10 text-center border-t border-[#F5F5F7] pt-6 flex flex-col gap-3">
              <span className="text-xs font-medium text-[#6E6E73]">
                Đã có mã xác thực?{" "}
                <a href="/verify" className="font-medium text-[#0071E3] hover:underline ml-1">
                  Nhập mã ngay
                </a>
              </span>
              <a
                href="/login"
                className="text-xs font-medium text-[#6E6E73] hover:text-[#1D1D1F] hover:underline mt-2"
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