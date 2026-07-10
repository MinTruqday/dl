"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { forgotPasswordAPI } from "@/features/authentication/services/session.service";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2, Mail } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!email || !email.includes("@")) {
      showToast("Lỗi sai lệch định dạng chuẩn email", "error");
      return;
    }

    try {
      setLoading(true);
      const data = await forgotPasswordAPI(email);
      showToast(
        data.message || "Hoàn tất khởi tạo luồng khôi phục dữ liệu",
        "success",
      );
      setTimeout(() => {
        window.location.href = `/xac-thuc?email=${encodeURIComponent(email)}`;
      }, 1500);
    } catch (err: any) {
      showToast(err.message || "Lỗi khởi tạo luồng phân phối mã xác thực", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-[420px]">
          <div className="auth-panel">
            <div className="text-center mb-8">
              <h1 className="text-[28px] font-semibold tracking-tight text-[#1D1D1F]">
                Quên mật khẩu
              </h1>
              <p className="mt-2 text-[15px] text-[#6E6E73]">
                Nhập email của bạn để nhận mã xác thực khôi phục mật khẩu.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="email"
                  className="block text-[13px] font-medium text-[#6E6E73] mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6E6E73]" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setEmail(e.target.value)
                    }
                    className="apple-input w-full pl-11"
                    placeholder=""
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="pill-button w-full flex justify-center items-center gap-2 disabled:opacity-50"
                >
                  {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                  {loading ? "Đang xử lý" : "Gửi yêu cầu khôi phục"}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center border-t border-[#D2D2D7] pt-6 flex flex-col gap-3">
              <span className="text-[15px] text-[#6E6E73]">
                Đã có mã xác thực?{" "}
                <a
                  href="/xac-thuc"
                  className="font-medium text-[#0071E3] hover:text-[#0055C6]"
                >
                  Nhập mã ngay
                </a>
              </span>
              <a
                href="/dang-nhap"
                className="text-[13px] font-medium text-[#6E6E73] hover:text-[#1D1D1F] transition-colors"
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
