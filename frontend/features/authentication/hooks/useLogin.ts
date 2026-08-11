"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getGoogleLoginUrlAPI,
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
} from "@/features/authentication/services/session.service";
import { b64urlToBuffer, bufferToB64url } from "../lib/webauthn";

export function useLogin() {
  const router = useRouter();
  const { loginState } = useAuth() as any;
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const finish = async (token: string) => {
    await loginState(token);
    router.push("/kham-pha");
  };

  const passwordLogin = async (email: string, password: string) => {
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await login(email.trim(), password);
      await finish(response.access_token || response);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Email hoặc mật khẩu không đúng",
      );
      setSubmitting(false);
    }
  };

  const passkeyLogin = async (email: string) => {
    if (submitting) return;
    if (!email.trim()) {
      setError("Nhập email trước khi dùng passkey");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const begin = await passkeyLoginBeginAPI(email.trim());
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge: b64urlToBuffer(begin.challenge),
          rpId: begin.rpId,
          timeout: begin.timeout,
          userVerification: begin.userVerification,
          allowCredentials: (begin.allowCredentials || []).map(
            (credential: any) => ({
              type: credential.type,
              id: b64urlToBuffer(credential.id),
            }),
          ),
        },
      });
      if (!assertion) throw new Error("Không nhận được thông tin passkey");
      const credential = assertion as PublicKeyCredential;
      const response = credential.response as AuthenticatorAssertionResponse;
      const result = await passkeyLoginFinishAPI(email.trim(), {
        id: credential.id,
        rawId: bufferToB64url(credential.rawId),
        type: credential.type,
        response: {
          clientDataJSON: bufferToB64url(response.clientDataJSON),
          authenticatorData: bufferToB64url(response.authenticatorData),
          signature: bufferToB64url(response.signature),
          userHandle: response.userHandle
            ? bufferToB64url(response.userHandle)
            : null,
        },
      });
      await finish(result.access_token || result);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể đăng nhập bằng passkey",
      );
      setSubmitting(false);
    }
  };

  const googleLogin = async () => {
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      window.location.assign(await getGoogleLoginUrlAPI());
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể kết nối với Google",
      );
      setSubmitting(false);
    }
  };

  return { submitting, error, passwordLogin, passkeyLogin, googleLogin };
}
