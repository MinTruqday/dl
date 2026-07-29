"use client";

import { FormEvent, useState, useEffect, Suspense } from "react";
import { resetPasswordAPI } from "@/features/authentication/services/session.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import AuthLayout from "@/features/authentication/components/AuthLayout";
import PasswordInput from "@/features/authentication/components/PasswordInput";

function ResetPasswordContent() {
  const [newPassword, setNewPassword] = useState("");
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
      showToast("Lỗi sai lệch quy tắc định dạng mật khẩu tối thiểu", "error");
      return;
    }

    try {
      setLoading(true);
      const data = await resetPasswordAPI(token, newPassword);
      showToast(data.message || "Cập nhật cấu trúc mật khẩu hoàn tất", "success");
      setTimeout(() => router.push("/dang-nhap"), 1500);
    } catch (err: any) {
      showToast(err.message || "Lỗi cập nhật cấu trúc mật khẩu mới", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Mật khẩu mới">
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <label
            htmlFor="new-password"
            className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]"
          >
            Mật khẩu mới
          </label>
          <PasswordInput
            id="new-password"
            autoComplete="new-password"
            required
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="pill-button w-full disabled:opacity-50"
        >
          {loading ? "Đang xử lý" : "Cập nhật mật khẩu"}
        </button>
      </form>
    </AuthLayout>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-[100dvh] bg-[var(--canvas)]" />}>
        <ResetPasswordContent />
    </Suspense>
  );
}
