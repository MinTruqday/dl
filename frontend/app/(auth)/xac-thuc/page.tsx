"use client";

import { ChangeEvent, FormEvent, useState, useEffect, Suspense } from "react";
import {
  verifyCodeAPI,
  forgotPasswordAPI,
} from "@/features/authentication/services/session.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/ToastContext";
import { Loader2 } from "lucide-react";

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
    <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
      <div className="w-full max-w-[420px]">
        <div className="auth-panel">
          <div className="text-center mb-8">
            <h1 className="text-[28px] font-semibold tracking-tight text-ink">
              Xác thực mã
            </h1>
            <p className="mt-2 text-[15px] text-ink-muted">
              Mã xác nhận 6 số đã được gửi tới email
              <br />
              <strong className="text-ink font-medium">{email}</strong>
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="token"
                className="block text-[13px] font-medium text-ink-muted mb-2 ml-1 text-center"
              >
                Nhập mã OTP
              </label>
              <input
                id="token"
                name="token"
                type="text"
                required
                value={token}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setToken(e.target.value)
                }
                className="apple-input w-full text-center text-2xl tracking-[0.3em] font-bold text-ink uppercase"
                placeholder=""
                maxLength={6}
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="pill-button w-full flex justify-center items-center gap-2 disabled:opacity-50"
              >
                {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                {loading ? "Đang kiểm tra" : "Xác nhận mã"}
              </button>
            </div>
          </form>

          <div className="mt-8 text-center border-t border-border pt-6 flex flex-col gap-4">
            {countdown > 0 ? (
              <p className="text-[13px] text-ink-muted">
                Gửi lại mã xác thực sau{" "}
                <span className="font-semibold text-ink">
                  {countdown}s
                </span>
              </p>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="text-[13px] font-medium text-brand hover:text-brand-hover"
              >
                {resending ? "Đang gửi" : "Gửi lại mã xác thực"}
              </button>
            )}
            <button
              type="button"
              onClick={() => router.back()}
              className="text-[13px] font-medium text-ink-muted hover:text-ink transition-colors"
            >
              Quay lại bước trước
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function VerifyCodePage() {
  return (
    <div className="min-h-screen bg-white font-sans flex flex-col">
      <Suspense fallback={<div className="flex-1 min-h-screen" />}>
        <VerifyCodeContent />
      </Suspense>
    </div>
  );
}
