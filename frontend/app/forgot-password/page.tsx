"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import Navbar from "@/app/components/Navbar";
import { forgotPasswordAPI } from "@/app/lib/api";
import { Notification } from "@/app/components/NotificationToast";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!email || !email.includes("@")) {
      setError("Vui lòng nhập email hợp lệ.");
      return;
    }

    try {
      setLoading(true);
      const data = await forgotPasswordAPI(email);
      setInfo(data.message || "Nếu email tồn tại, liên kết reset đã được gửi.");
    } catch (err: any) {
      setError(err.message || "Không thể gửi mã khôi phục.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navbar />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-extrabold text-foreground font-bold">Quên mật khẩu</h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">Nhập email để gửi yêu cầu đặt lại mật khẩu.</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-8 px-4 shadow sm: sm:px-10 border border-border">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {info && <Notification type="success" message={info} />}
            {error && <Notification type="error" message={error} />}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Địa chỉ Email</label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4  text-sm font-medium text-white bg-black hover:bg-zinc-800 disabled:opacity-50 tracking-widest"
            >
              {loading ? "ĐANG GỬI" : "GỬI YÊU CẦU KHÔI PHỤC"}
            </button>
          </form>

          <div className="mt-4 text-sm text-center">
            <a href="/reset-password" className="text-black hover:underline font-bold text-[12px] tracking-widest">Đã có mã xác thực? Đặt lại mật khẩu</a>
          </div>
        </div>
      </div>
    </div>
  );
}
