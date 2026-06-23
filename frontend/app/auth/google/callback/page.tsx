"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { Loader2 } from "lucide-react";
import Passkey from "@/features/auth/components/Passkey";

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
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/auth/google/feedback?code=${code}`,
          );
          const data = await res.json();
          const authData = data.data || data;

          if (authData.access_token) {
            await loginState(authData.access_token);
            if (!authData.user?.has_passkey) {
              setPendingPasskeyEmail(authData.user?.email);
            } else {
              router.push("/");
            }
          } else {
            setError(data.message || authData.detail || "Xác thực thất bại.");
          }
        } catch (err) {
          setError("Lỗi kết nối với hệ thống.");
        }
      };
      handleCallback();
    }
  }, [searchParams, loginState, router]);

  if (pendingPasskeyEmail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50">
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
      <div className="min-h-screen flex items-center justify-center bg-zinc-50 font-sans">
        <div className="bg-white/90 backdrop-blur-md p-8 border border-zinc-100 shadow-xl max-w-md w-full text-center rounded-3xl transition-all duration-300">
          <h2 className="text-xl font-bold text-black tracking-tight">
            Lỗi xác thực
          </h2>
          <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{error}</p>
          <button
            onClick={() => router.push("/dang-nhap")}
            className="mt-6 w-full flex justify-center items-center h-11 text-xs font-bold text-white bg-black rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md"
          >
            Quay lại đăng nhập
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 font-sans">
      <div className="text-center flex flex-col items-center justify-center gap-4 bg-white/90 backdrop-blur-md p-8 border border-zinc-100 shadow-xl rounded-3xl">
        <Loader2 className="h-8 w-8 animate-spin text-black" />
        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
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
        <div className="min-h-screen flex items-center justify-center bg-zinc-50 font-sans">
          <Loader2 className="h-10 w-10 animate-spin text-black" />
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
