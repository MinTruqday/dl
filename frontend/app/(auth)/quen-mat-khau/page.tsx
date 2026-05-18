"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import Navigation from "@/components/Navigation";
import { forgotPasswordAPI } from "@/services/authentication.service";
import { useToast } from "@/contexts/Toast";
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
        window.location.href = `/xac-thuc-ma?email=${encodeURIComponent(email)}`;
      }, 1500);
    } catch (err: any) {
      showToast(err.message || "Không thể gửi mã khôi phục", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navigation />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-bold tracking-tight text-black">
          Quên mật khẩu
        </h2>
        <p className="mt-2 text-center text-sm text-zinc-500">
          Nhập email để gửi yêu cầu đặt lại mật khẩu
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-none">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-black"
              >
                Địa chỉ email
              </label>
              <div className="mt-2">
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setEmail(e.target.value)
                  }
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-black text-sm text-black"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-3 h-12 text-sm font-medium text-white bg-black disabled:bg-zinc-200 disabled:text-zinc-500 rounded-none"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? "Đang xử lý" : "Gửi yêu cầu khôi phục"}
            </button>
          </form>

          <div className="mt-8 text-sm text-center flex flex-col gap-3">
            <a
              href="/xac-thuc-ma"
              className="text-black font-medium underline"
            >
              Đã có mã xác thực? Xác thực ngay
            </a>
            <a
              href="/dang-nhap"
              className="text-zinc-500 font-medium underline"
            >
              Quay lại đăng nhập
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
