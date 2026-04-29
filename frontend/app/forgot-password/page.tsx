"use client";

import { ChangeEvent, FormEvent, useState, useEffect } from "react";
import Navbar from "@/app/components/Navbar";
import { forgotPasswordAPI } from "@/app/lib/api";
import { useToast } from "@/app/contexts/ToastContext";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
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
        window.location.href = `/verify-code?email=${encodeURIComponent(email)}`;
      }, 1500);
    } catch (err: any) {
      showToast(err.message || "Không thể gửi mã khôi phục", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navbar />
      <div
        className="sm:mx-auto sm:w-full sm:max-w-md mt-16 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <h2 className="text-center text-4xl font-bold tracking-tight text-black">Quên mật khẩu</h2>
        <p className="mt-3 text-center text-base text-zinc-500">Nhập email để gửi yêu cầu đặt lại mật khẩu</p>
      </div>

      <div
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md transition-all duration-300 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className="bg-white py-8 px-4 sm:px-10 border border-zinc-200 rounded-sm">
          <form className="space-y-6" onSubmit={handleSubmit}>

            <div>
              <label htmlFor="email" className="block text-base font-bold text-black">Địa chỉ email</label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all placeholder-zinc-400"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 text-base font-bold text-white bg-black hover:bg-zinc-800 disabled:opacity-50 transition-all active:scale-95 rounded-sm"
            >
              {loading ? "Đang gửi" : "Gửi yêu cầu khôi phục"}
            </button>
          </form>

          <div className="mt-4 text-sm text-center flex flex-col gap-2">
            <a href="/verify-code" className="text-black hover:underline font-bold text-[12px] active:scale-95 inline-block transition-transform">
              Đã có mã xác thực? Xác thực ngay
            </a>
            <a href="/login" className="text-zinc-400 hover:text-black font-medium text-[12px] active:scale-95 inline-block transition-transform">
              Quay lại đăng nhập
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
