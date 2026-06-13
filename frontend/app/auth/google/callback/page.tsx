"use client";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/auth/contexts/Auth";
import { Loader2 } from "lucide-react";
import Passkey from "@/features/auth/components/Passkey";

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loginState } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      const handleCallback = async () => {
        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/xac-thuc/google/phan-hoi?code=${code}`
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

  const [pendingPasskeyEmail, setPendingPasskeyEmail] = useState<string | null>(
    null,
  );

  if (pendingPasskeyEmail) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
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
      <div className="min-h-screen flex items-center justify-center bg-white font-sans">
        <div className="bg-white p-12 border border-zinc-200 max-w-md w-full text-center rounded-2xl animate-in fade-in slide-in-from-bottom-8 duration-300">
          <h2 className="text-2xl font-bold text-black tracking-tight">
            Lỗi xác thực
          </h2>
          <p className="mt-3 text-base text-zinc-500">{error}</p>
          <button
            onClick={() => router.push("/dang-nhap")}
            className="mt-8 w-full py-3 bg-black text-white font-bold text-sm active:scale-95 rounded-2xl hover:bg-zinc-800 transition-colors"
          >
            Quay lại đăng nhập
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white font-sans">
      <div className="text-center animate-in fade-in slide-in-from-bottom-8 duration-300">
        <Loader2 className="h-10 w-10 animate-spin text-black mx-auto" />
        <p className="mt-6 text-base font-bold text-black">
          Đang xử lý đăng nhập bằng Google
        </p>
      </div>
    </div>
  );
}
