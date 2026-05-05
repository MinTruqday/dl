"use client";

import Navigation from "@/components/Navigation";
import { ChangeEvent, FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Fingerprint } from "lucide-react";
import {
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
  getGoogleLoginUrlAPI,
} from "@/services/auth.service";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/contexts/ToastContext";
import Passkey from "@/components/Passkey";

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

const GoogleIcon = () => (
  <svg className="w-5 h-5 text-black" viewBox="0 0 24 24" fill="currentColor">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

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
          challenge: b64urlToBuffer(begin.public_key.challenge),
          rpId: begin.public_key.rpId,
          timeout: begin.public_key.timeout,
          userVerification: begin.public_key.userVerification,
          allowCredentials: (begin.public_key.allowCredentials || []).map(
            (c: any) => ({
              type: c.type,
              id: b64urlToBuffer(c.id),
            }),
          ),
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
          "Đăng nhập thành công. Hãy cân nhắc thiết lập Passkey",
          "success"
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
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navigation />

      {pendingPasskeyEmail && (
        <Passkey
          email={pendingPasskeyEmail}
          onClose={() => router.push("/")}
          onSuccess={() => router.push("/")}
        />
      )}
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-bold tracking-tight text-black">
          Đăng nhập
        </h2>
        <p className="mt-2 text-center text-sm text-zinc-500">
          Chưa có tài khoản?{" "}
          <a
            href="/register"
            className="font-medium text-black hover:underline transition-all"
          >
            Đăng ký ngay
          </a>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-none">
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-black"
              >
                Email hoặc tên tài khoản
              </label>
              <div className="mt-2">
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
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-none placeholder-zinc-400 focus:outline-none focus:ring-0 focus:border-black text-sm text-black transition-colors"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-black"
              >
                Mật khẩu
              </label>
              <div className="mt-2">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setPassword(e.target.value)
                  }
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-none placeholder-zinc-400 focus:outline-none focus:ring-0 focus:border-black text-sm text-black transition-colors"
                />
                <div className="mt-2 text-right">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-xs font-medium text-zinc-500 hover:text-black hover:underline transition-all"
                  >
                    {showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-black focus:ring-0 border border-zinc-300 rounded-none cursor-pointer"
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm text-zinc-600"
                >
                  Ghi nhớ đăng nhập
                </label>
              </div>

              <div className="text-sm">
                <a
                  href="/forgot-password"
                  className="font-medium text-black hover:underline transition-all"
                >
                  Quên mật khẩu?
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center gap-3 h-12 border border-transparent rounded-none text-sm font-medium text-white bg-black hover:bg-zinc-800 focus:outline-none transition-colors disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed"
              >
                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                {isSubmitting ? "Đang xử lý" : "Đăng nhập"}
              </button>
            </div>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-zinc-200" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-2 bg-white text-zinc-500">
                  Hoặc tiếp tục với
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4">
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
                className="w-full inline-flex justify-center items-center h-12 border border-zinc-200 rounded-none bg-white text-sm font-medium text-black hover:bg-zinc-50 transition-colors gap-2"
              >
                <Fingerprint className="w-5 h-5 text-black" />
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
                className="w-full inline-flex justify-center items-center h-12 border border-zinc-200 rounded-none bg-white text-sm font-medium text-black hover:bg-zinc-50 transition-colors gap-2"
              >
                <GoogleIcon />
                Google
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
