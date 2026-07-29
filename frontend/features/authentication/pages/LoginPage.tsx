"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
  getGoogleLoginUrlAPI,
} from "@/features/authentication/services/session.service";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import Passkey from "@/features/authentication/components/Passkey";
import AuthLayout from "@/features/authentication/components/AuthLayout";
import PasswordInput from "@/features/authentication/components/PasswordInput";
import Link from "next/link";

function b64urlToBuffer(b64url: string): ArrayBuffer {
  const pad = "=".repeat((4 - (b64url.length % 4)) % 4);
  const b64 = (b64url + pad).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const bytes = Uint8Array.from(raw, (c) => c.charCodeAt(0));
  return bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength,
  );
}

function bytesToB64url(bytes: ArrayBuffer): string {
  const arr = new Uint8Array(bytes);
  let str = "";
  arr.forEach((b) => {
    str += String.fromCharCode(b);
  });
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const { loginState } = useAuth() as any;
  const { showToast } = useToast();
  const [pendingPasskeyEmail, setPendingPasskeyEmail] = useState<string | null>(
    null,
  );

  const completePasskeyLogin = async (inputEmail: string) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      const begin = await passkeyLoginBeginAPI(inputEmail);
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge: b64urlToBuffer(begin.challenge),
          rpId: begin.rpId,
          timeout: begin.timeout,
          userVerification: begin.userVerification,
          allowCredentials: (begin.allowCredentials || []).map((c: any) => ({
            type: c.type,
            id: b64urlToBuffer(c.id),
          })),
        },
      });

      const cred = assertion as PublicKeyCredential;
      const resp = cred.response as AuthenticatorAssertionResponse;

      const credentialJSON = {
        id: cred.id,
        rawId: bytesToB64url(cred.rawId),
        type: cred.type,
        response: {
          clientDataJSON: bytesToB64url(resp.clientDataJSON),
          authenticatorData: bytesToB64url(resp.authenticatorData),
          signature: bytesToB64url(resp.signature),
          userHandle: resp.userHandle ? bytesToB64url(resp.userHandle) : null,
        },
      };

      const verify = await passkeyLoginFinishAPI(inputEmail, credentialJSON);

      await loginState(verify.access_token || verify);
      showToast("Xác thực chứng thư số Passkey hợp lệ", "success");
      router.push("/kham-pha");
    } catch (err: any) {
      showToast(err.message || "Lỗi xác thực định danh chứng thư số", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const res = await login(email, password);
      if (res.needsPasskey) {
        setPendingPasskeyEmail(email);
        setIsSubmitting(false);
      } else {
        await loginState(res.access_token || res);
        showToast("Xác thực thông tin đăng nhập hợp lệ", "success");
        router.push("/kham-pha");
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi sai lệch thông tin định danh hệ thống", "error");
      setIsSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Đăng nhập"
      footer={
        <>
          Chưa có tài khoản{" "}
          <Link href="/dang-ky" className="font-semibold text-[var(--brand)]">
            Tạo tài khoản
          </Link>
        </>
      }
    >
          {pendingPasskeyEmail && (
            <div className="mb-6">
              <Passkey
                email={pendingPasskeyEmail}
                onClose={() => router.push("/kham-pha")}
                onSuccess={() => router.push("/kham-pha")}
              />
            </div>
          )}

            <form className="space-y-5" onSubmit={handleLogin}>
              <div>
                <label
                  htmlFor="email"
                    className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]"
                >
                  Tài khoản
                </label>
                  <input
                    id="email"
                    name="email"
                    type="text"
                    autoComplete="username"
                    required
                    value={email}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setEmail(e.target.value)
                    }
                    className="field-control w-full"
                  />
              </div>

              <div>
                <label
                  htmlFor="password"
                    className="mb-2 block text-[13px] font-medium text-[var(--ink-muted)]"
                >
                  Mật khẩu
                </label>
                <PasswordInput
                    id="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setPassword(e.target.value)
                    }
                  />
              </div>

              <div className="flex items-center justify-between ml-1 mr-1">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="size-4 cursor-pointer accent-[var(--brand)]"
                  />
                  <label
                    htmlFor="remember-me"
                    className="ml-2 block text-[13px] text-[var(--ink)]"
                  >
                    Ghi nhớ phiên
                  </label>
                </div>
                <Link
                  href="/quen-mat-khau"
                  className="text-[13px] font-semibold text-[var(--brand)]"
                >
                  Quên mật khẩu
                </Link>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="button-primary w-full disabled:opacity-50"
                >
                  {isSubmitting ? "Đang xử lý" : "Đăng nhập"}
                </button>
              </div>
            </form>

            <div className="mt-7 flex items-center justify-center gap-3">
              <div className="h-px flex-1 bg-[var(--border)]" />
              <span className="text-[13px] text-[var(--ink-muted)]">Hoặc</span>
              <div className="h-px flex-1 bg-[var(--border)]" />
            </div>

            <div className="mt-7 grid gap-3">
              <button
                type="button"
                onClick={async () => {
                  if (!email) {
                    showToast(
                      "Lỗi thiếu hụt trường địa chỉ email cho định danh chứng thư số",
                      "error",
                    );
                    return;
                  }
                  await completePasskeyLogin(email);
                }}
                className="button-secondary w-full"
              >
                Đăng nhập bằng Passkey
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    const url = await getGoogleLoginUrlAPI();
                    window.location.href = url;
                  } catch (err: any) {
                    showToast("Lỗi kết nối điểm cuối định danh Google", "error");
                  }
                }}
                className="button-secondary w-full"
              >
                Tiếp tục với Google
              </button>
            </div>
    </AuthLayout>
  );
}
