"use client";

import { ChangeEvent, FormEvent, useState, useEffect, Suspense } from "react";
import {
  verifyCodeAPI,
  forgotPasswordAPI,
} from "@/features/authentication/services/session.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import AuthLayout from "@/features/authentication/components/AuthLayout";

function VerifyCodeContent() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [resending, setResending] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleResend = async () => {
    if (!email) return;
    try {
      setResending(true);
      await forgotPasswordAPI(email);
      showToast("Hoàn tất tái khởi tạo luồng phân phối mã", "success");
      setCountdown(60);
    } catch (err: any) {
      showToast(err.message || "Lỗi tái khởi tạo luồng phân phối mã", "error");
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!token.trim()) {
      showToast("Lỗi thiếu hụt chuỗi dữ liệu mã xác thực", "error");
      return;
    }

    try {
      setLoading(true);
      await verifyCodeAPI(token.trim());
      showToast("Xác thực chuỗi dữ liệu OTP hợp lệ", "success");
      setTimeout(() => {
        router.push(
          `/dat-lai-mat-khau?token=${encodeURIComponent(token.trim())}`,
        );
      }, 1200);
    } catch (err: any) {
      showToast(err.message || "Lỗi sai lệch chuỗi dữ liệu định danh OTP", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Xác thực mã"
      footer={
        <div className="flex flex-col gap-4">
            {countdown > 0 ? (
              <p className="text-[13px] text-[var(--ink-muted)]">
                Gửi lại mã xác thực sau{" "}
                <span className="font-semibold text-[var(--ink)]">
                  {countdown}s
                </span>
              </p>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="text-[13px] font-medium text-[var(--brand)] hover:text-[var(--brand-hover)]"
              >
                {resending ? "Đang gửi" : "Gửi lại mã xác thực"}
              </button>
            )}
            <button
              type="button"
              onClick={() => router.back()}
              className="text-[13px] font-medium text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors"
            >
              Quay lại bước trước
            </button>
          </div>
      }
    >
      <p className="mb-6 text-[14px] text-[var(--ink-muted)]">
        Mã gồm 6 số đã gửi tới{" "}
        <strong className="font-medium text-[var(--ink)]">{email}</strong>
      </p>
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <label
            htmlFor="token"
            className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]"
          >
            Mã xác thực
          </label>
          <input
            id="token"
            name="token"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={token}
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              setToken(event.target.value.replace(/\D/g, "").slice(0, 6))
            }
            className="field-control w-full text-center text-2xl font-semibold tracking-[0.3em]"
            maxLength={6}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="pill-button w-full disabled:opacity-50"
        >
          {loading ? "Đang kiểm tra" : "Xác nhận mã"}
        </button>
      </form>
    </AuthLayout>
  );
}

export default function VerifyCodePage() {
  return (
    <Suspense fallback={<div className="min-h-[100dvh] bg-[var(--canvas)]" />}>
        <VerifyCodeContent />
    </Suspense>
  );
}
