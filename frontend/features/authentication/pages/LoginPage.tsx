"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import InlineState from "@/shared/components/common/InlineState";
import { Button } from "@/shared/components/ui/Button";
import AuthField from "../components/AuthField";
import AuthFrame from "../components/AuthFrame";
import PasswordField from "../components/PasswordField";
import { useLogin } from "../hooks/useLogin";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordOpen, setPasswordOpen] = useState(false);
  const { submitting, error, passwordLogin, passkeyLogin, googleLogin } =
    useLogin();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    passwordLogin(email, password);
  };

  return (
    <AuthFrame
      title="Đăng nhập"
      footer={
        <p>
          Chưa có tài khoản?{" "}
          <Link
            href="/dang-ky"
            className="font-semibold text-brand hover:text-brand-hover"
          >
            Đăng ký
          </Link>
        </p>
      }
    >
      {error && (
        <div className="mb-5">
          <InlineState
            title="Không thể đăng nhập"
            detail={error}
            tone="danger"
          />
        </div>
      )}
      <AuthField
        id="login-email"
        name="email"
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      {passwordOpen && (
        <form className="mt-5 space-y-5" onSubmit={submit}>
          <PasswordField
            id="login-password"
            name="password"
            label="Mật khẩu"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <div className="flex justify-end">
            <Link
              href="/quen-mat-khau"
              className="text-[13px] font-semibold text-brand hover:text-brand-hover"
            >
              Quên mật khẩu
            </Link>
          </div>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Đang xử lý" : "Đăng nhập"}
          </Button>
        </form>
      )}
      {!passwordOpen && (
        <Button
          type="button"
          className="mt-5 w-full"
          disabled={submitting}
          onClick={() => passkeyLogin(email)}
        >
          {submitting ? "Đang xử lý" : "Đăng nhập bằng passkey"}
        </Button>
      )}
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          className="flex min-h-11 items-center justify-center rounded-control border border-border px-4 py-2 text-[14px] font-semibold text-ink hover:bg-surface-quiet"
          aria-expanded={passwordOpen}
          onClick={() => setPasswordOpen((value) => !value)}
        >
          {passwordOpen ? "Ẩn mật khẩu" : "Mật khẩu"}
        </button>
        <Button type="button" variant="secondary" disabled={submitting} onClick={googleLogin}>
          Đăng nhập bằng Google
        </Button>
      </div>
    </AuthFrame>
  );
}
