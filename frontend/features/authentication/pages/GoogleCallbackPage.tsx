"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import Passkey from "@/features/authentication/components/Passkey";
import AuthLayout from "@/features/authentication/components/AuthLayout";
import { finishGoogleLoginAPI } from "@/features/authentication/services/session.service";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loginState } = useAuth();
  const [error, setError] = useState("");
  const [pendingPasskeyEmail, setPendingPasskeyEmail] = useState<string | null>(
    null,
  );

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    if (code && state) {
      const handleCallback = async () => {
        try {
          const authData = await finishGoogleLoginAPI(code, state);

          if (authData.access_token) {
            await loginState(authData.access_token);
            if (!authData.user?.has_passkey) {
              setPendingPasskeyEmail(authData.user?.email);
            } else {
              router.push("/");
            }
          } else {
            setError(authData.detail || "Không thể xác thực Google");
          }
        } catch (err) {
          setError("Lỗi kết nối hệ thống dịch vụ");
        }
      };
      handleCallback();
    } else {
      setError("Thiếu thông tin xác thực Google");
    }
  }, [searchParams, loginState, router]);

  if (pendingPasskeyEmail) {
    return (
      <div className="min-h-[100dvh] bg-[var(--canvas)]">
        <Passkey
          email={pendingPasskeyEmail}
          onClose={() => router.push("/")}
          onSuccess={() => router.push("/")}
        />
      </div>
    );
  }

  if (error) {
    return (
      <AuthLayout title="Không thể đăng nhập">
          <p className="mt-2 text-[15px] text-[var(--danger)]">{error}</p>
          <button
            onClick={() => router.push("/dang-nhap")}
            className="pill-button w-full mt-6"
          >
            Quay lại đăng nhập
          </button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Đăng nhập bằng Google">
        <p className="text-[15px] font-medium text-[var(--ink)]">
          Đang xác thực
        </p>
    </AuthLayout>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[100dvh] bg-[var(--canvas)]" />
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
