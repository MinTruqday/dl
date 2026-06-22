"use client";

import { ChangeEvent, FormEvent, useState, useEffect, Suspense } from "react";
import {
  verifyCodeAPI,
  forgotPasswordAPI,
} from "@/features/auth/services/user_authentication.service";
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
      showToast("Đã gửi lại mã xác thực", "success");
      setCountdown(60);
    } catch (err: any) {
      showToast(err.message || "Không thể gửi lại mã", "error");
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!token.trim()) {
      showToast("Vui lòng nhập mã xác thực", "error");
      return;
    }

    try {
      setLoading(true);
      await verifyCodeAPI(token.trim());
      showToast("Mã xác thực hợp lệ", "success");
      setTimeout(() => {
        router.push(
          `/reset-password?token=${encodeURIComponent(token.trim())}`,
        );
      }, 1200);
    } catch (err: any) {
      showToast(err.message || "Mã xác thực không hợp lệ", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
      <div className="w-full max-w-[420px]">
        <div className="bg-white/90 backdrop-blur-md border border-zinc-100 rounded-3xl shadow-xl p-8 sm:p-10 transition-all duration-300">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold tracking-tight text-black">
              Xác thực mã
            </h1>
            <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
              Mã xác nhận 6 số đã được gửi tới email<br />
              <strong className="text-zinc-600">{email}</strong>
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="token"
                className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1 text-center"
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
                className="w-full bg-white border border-zinc-200 rounded-3xl px-4 py-4 focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all text-center text-2xl tracking-[0.3em] font-bold text-black uppercase"
                placeholder="------"
                maxLength={6}
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-2 h-12 text-xs font-bold text-white bg-black rounded-3xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Đang kiểm tra" : "Xác nhận mã"}
              </button>
            </div>
          </form>

          <div className="mt-8 text-center border-t border-zinc-100 pt-6 flex flex-col gap-4">
            {countdown > 0 ? (
              <p className="text-xs font-medium text-zinc-500">
                Gửi lại mã xác thực sau <span className="font-bold text-black">{countdown}s</span>
              </p>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={resending}
                className="text-xs font-bold text-black transition-colors hover:text-zinc-600"
              >
                {resending ? "Đang gửi..." : "Gửi lại mã xác thực"}
              </button>
            )}
            <button
              type="button"
              onClick={() => router.back()}
              className="text-xs font-medium text-zinc-500 transition-colors hover:text-black"
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
    <div className="min-h-screen bg-zinc-50 font-sans selection:bg-zinc-900 selection:text-white flex flex-col">
      <Suspense fallback={<div className="flex-1 min-h-screen" />}>
        <VerifyCodeContent />
      </Suspense>
    </div>
  );
}
