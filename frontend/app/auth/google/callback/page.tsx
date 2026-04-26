"use client";
import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/app/contexts/AuthContext";

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
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google/callback?code=${code}`);
          const data = await res.json();
          if (data.access_token) {
            await loginState(data.access_token);
            router.push("/");
          } else {
            setError(data.detail || "Xác thực thất bại.");
          }
        } catch (err) {
          setError("Lỗi kết nối với hệ thống.");
        }
      };
      handleCallback();
    }
  }, [searchParams, loginState, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="bg-card p-8 border border-border   max-w-sm w-full">
          <h2 className="text-xl font-bold text-foreground">Lỗi xác thực</h2>
          <p className="mt-2 text-sm text-muted-foreground">{error}</p>
          <button 
            onClick={() => router.push("/login")}
            className="mt-4 w-full py-2 bg-black text-white  hover:bg-gray-800"
          >
            Quay lại đăng nhập
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="h-8 w-8 animate-spin rounded-none border-4 border-black border-t-transparent mx-auto"></div>
        <p className="mt-4 text-sm font-medium text-foreground">Đang xử lý đăng nhập bằng Google</p>
      </div>
    </div>
  );
}
