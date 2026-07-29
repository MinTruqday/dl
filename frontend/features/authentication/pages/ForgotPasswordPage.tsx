"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { forgotPasswordAPI } from "@/features/authentication/services/session.service";
import { useToast } from "@/shared/contexts/ToastContext";
import AuthLayout from "@/features/authentication/components/AuthLayout";

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
    <AuthLayout
      title="Quên mật khẩu"
      footer={
        <div className="flex flex-col gap-3">
          <a
            href="/xac-thuc"
            className="font-medium text-[var(--brand)] hover:text-[var(--brand-hover)]"
          >
            Nhập mã xác thực
          </a>
          <a
            href="/dang-nhap"
            className="font-medium text-[var(--ink-muted)] hover:text-[var(--ink)]"
          >
            Quay lại đăng nhập
          </a>
        </div>
      }
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <label
            htmlFor="email"
            className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]"
          >
            Địa chỉ email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              setEmail(event.target.value)
            }
            className="field-control w-full"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="pill-button w-full disabled:opacity-50"
        >
          {loading ? "Đang xử lý" : "Gửi mã xác thực"}
        </button>
      </form>
    </AuthLayout>
  );
}
