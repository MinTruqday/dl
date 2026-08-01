"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { completeGoogleLoginAPI } from "@/features/authentication/services/session.service";

export function useGoogleCallback() {
  const router = useRouter();
  const params = useSearchParams();
  const { loginState } = useAuth() as any;
  const [emailForPasskey, setEmailForPasskey] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const code = params.get("code");
    if (!code) {
      setError("Thiếu mã xác thực từ Google");
      return;
    }
    let active = true;
    const complete = async () => {
      try {
        const data = await completeGoogleLoginAPI(code);
        if (!data.access_token)
          throw new Error("Không nhận được quyền truy cập");
        await loginState(data.access_token);
        if (!active) return;
        if (!data.user?.has_passkey && data.user?.email)
          setEmailForPasskey(data.user.email);
        else router.replace("/kham-pha");
      } catch (reason) {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Không thể xác thực bằng Google",
          );
      }
    };
    complete();
    return () => {
      active = false;
    };
  }, [loginState, params, router]);

  return {
    emailForPasskey,
    error,
    finish: () => router.replace("/kham-pha"),
    back: () => router.replace("/dang-nhap"),
  };
}
