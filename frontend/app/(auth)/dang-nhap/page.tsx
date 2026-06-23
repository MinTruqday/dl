"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, KeyRound, Eye, EyeOff, Mail, Lock } from "lucide-react";
import {
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
  getGoogleLoginUrlAPI,
} from "@/features/auth/services/user_authentication.service";
import { useAuth } from "@/features/auth/contexts/AuthContext";
import { useToast } from "@/shared/contexts/ToastContext";
import Passkey from "@/features/auth/components/Passkey";

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

function GoogleIcon() {
  return (
    <svg className="w-4 h-4 text-black" viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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
      showToast("Đăng nhập Passkey thành công", "success");
      router.push("/");
    } catch (err: any) {
      showToast(err.message || "Đăng nhập bằng Passkey thất bại", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);

    if (!email) {
      showToast("Vui lòng nhập email hoặc tên tài khoản", "error");
      setIsSubmitting(false);
      return;
    }

    if (!password) {
      showToast("Vui lòng nhập mật khẩu", "error");
      setIsSubmitting(false);
      return;
    }
    try {
      const data = await login(email, password);

      await loginState(data.access_token);

      if (!data.user?.has_passkey) {
        setPendingPasskeyEmail(data.user?.email || email);
        showToast(
          "Đăng nhập thành công",
          "success",
        );
        setIsSubmitting(false);
      } else {
        showToast("Đăng nhập thành công", "success");
        router.push("/");
      }
    } catch (err: any) {
      showToast(err.message || "Sai email hoặc mật khẩu", "error");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 font-sans selection:bg-zinc-900 selection:text-white flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-[420px]">
          {pendingPasskeyEmail && (
            <div className="mb-6">
              <Passkey
                email={pendingPasskeyEmail}
                onClose={() => router.push("/")}
                onSuccess={() => router.push("/")}
              />
            </div>
          )}

          <div className="auth-panel">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold tracking-tight text-black">
                Đăng nhập
              </h1>
              <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Chào mừng trở lại! Vui lòng nhập thông tin.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleLogin}>
              <div>
                <label
                  htmlFor="email"
                  className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                >
                  Tài khoản
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
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
                    className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-4 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm"
                    placeholder="Email hoặc tên tài khoản"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                >
                  Mật khẩu
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setPassword(e.target.value)
                    }
                    className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-12 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm"
                    placeholder="Nhập mật khẩu"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between ml-1 mr-1">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-black focus:ring-0 border border-zinc-300 rounded cursor-pointer"
                  />
                  <label
                    htmlFor="remember-me"
                    className="ml-2 block text-xs font-medium text-zinc-500"
                  >
                    Ghi nhớ phiên
                  </label>
                </div>
                <a
                  href="/quen-mat-khau"
                  className="text-xs font-bold text-zinc-500"
                >
                  Quên mật khẩu?
                </a>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full flex justify-center items-center gap-2 h-12 rounded-3xl text-xs font-bold text-white bg-black shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                >
                  {isSubmitting && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                  {isSubmitting ? "Đang xử lý" : "Đăng nhập"}
                </button>
              </div>
            </form>

            <div className="mt-7 flex items-center justify-center gap-3">
              <div className="h-px bg-zinc-100 flex-1" />
              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                Hoặc
              </span>
              <div className="h-px bg-zinc-100 flex-1" />
            </div>

            <div className="mt-7 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={async () => {
                  if (!email) {
                    showToast(
                      "Vui lòng nhập email trước để dùng Passkey",
                      "error",
                    );
                    return;
                  }
                  await completePasskeyLogin(email);
                }}
                className="w-full inline-flex justify-center items-center h-12 border border-zinc-200 rounded-3xl bg-white text-xs font-bold text-zinc-700 gap-2 shadow-sm"
              >
                <KeyRound className="w-4 h-4" />
                Passkey
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    const url = await getGoogleLoginUrlAPI();
                    window.location.href = url;
                  } catch (err: any) {
                    showToast("Không thể kết nối với Google", "error");
                  }
                }}
                className="w-full inline-flex justify-center items-center h-12 border border-zinc-200 rounded-3xl bg-white text-xs font-bold text-zinc-700 gap-2 shadow-sm"
              >
                <GoogleIcon />
                Google
              </button>
            </div>

            <div className="mt-8 text-center">
              <p className="text-xs font-medium text-zinc-500">
                Chưa có tài khoản?{" "}
                <a
                  href="/dang-ky"
                  className="font-bold text-black"
                >
                  Đăng ký ngay
                </a>
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
