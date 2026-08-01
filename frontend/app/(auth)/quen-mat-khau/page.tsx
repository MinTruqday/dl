"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import InlineState from "@/app/_components/InlineState";
import { Button } from "@/shared/components/ui/Button";
import AuthField from "../_components/AuthField";
import AuthFrame from "../_components/AuthFrame";
import { useForgotPassword } from "../_hooks/usePasswordRecovery";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const { submitting, error, submit } = useForgotPassword();

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit(email);
  };

  return (
    <AuthFrame
      title="Khôi phục mật khẩu"
      description="Nhập email để nhận mã xác thực"
      footer={
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          <Link
            href="/xac-thuc"
            className="font-semibold text-brand hover:text-brand-hover"
          >
            Nhập mã
          </Link>
          <Link
            href="/dang-nhap"
            className="font-semibold text-ink hover:text-brand"
          >
            Quay lại đăng nhập
          </Link>
        </div>
      }
    >
      {error && (
        <div className="mb-5">
          <InlineState title="Không thể gửi mã" detail={error} tone="danger" />
        </div>
      )}
      <form className="space-y-5" onSubmit={handleSubmit}>
        <AuthField
          id="recovery-email"
          name="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? "Đang gửi" : "Gửi mã"}
        </Button>
      </form>
    </AuthFrame>
  );
}
