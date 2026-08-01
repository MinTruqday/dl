"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { Loader2 } from "lucide-react";
import Passkey from "@/features/authentication/components/Passkey";
import { completeGoogleLoginAPI } from "@/features/authentication/services/session.service";

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
    if (code) {
      const handleCallback = async () => {
        try {
          const authData = await completeGoogleLoginAPI(code);

          if (authData.access_token) {
            await loginState(authData.access_token);
            if (!authData.user?.has_passkey) {
              setPendingPasskeyEmail(authData.user?.email);
            } else {
              router.push("/");
            }
          } else {
            setError(authData.detail || "Xác thực không thành công");
          }
        } catch (err) {
          setError("Lỗi kết nối hệ thống dịch vụ");
        }
      };
      handleCallback();
    }
  }, [searchParams, loginState, router]);

  if (pendingPasskeyEmail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white font-sans">
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
      <div className="min-h-screen flex items-center justify-center bg-white font-sans px-4">
        <div className="auth-panel max-w-md w-full text-center">
          <h2 className="text-[20px] font-semibold text-ink tracking-tight">
            Lỗi xác thực
          </h2>
          <p className="mt-2 text-[15px] text-danger">{error}</p>
          <button
            onClick={() => router.push("/dang-nhap")}
            className="pill-button w-full mt-6"
          >
            Quay lại đăng nhập
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white font-sans px-4">
      <div className="auth-panel flex flex-col items-center justify-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-brand" />
        <p className="text-[15px] font-medium text-ink">
          Đang xử lý đăng nhập bằng Google
        </p>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-white font-sans px-4">
          <Loader2 className="h-10 w-10 animate-spin text-brand" />
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
