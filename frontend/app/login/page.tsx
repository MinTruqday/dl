"use client";

import Navbar from "@/app/components/Navbar";
import { ChangeEvent, FormEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Fingerprint } from "lucide-react";
import {
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
  passkeyRegisterBeginAPI,
  passkeyRegisterFinishAPI,
} from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";
import { useToast } from "@/app/contexts/ToastContext";
import PasskeyPrompt from "@/app/components/PasskeyPrompt";

function b64urlToBuffer(b64url: string): ArrayBuffer {
  const pad = "=".repeat((4 - (b64url.length % 4)) % 4);
  const b64 = (b64url + pad).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(b64);
  const bytes = Uint8Array.from(raw, (c) => c.charCodeAt(0));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
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
  const [showPassword, setShowPassword] = useState(false);
  const [authStep, setAuthStep] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const router = useRouter();
  const { loginState } = useAuth() as any;
  const { showToast } = useToast();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const completePasskeyLogin = async (inputEmail: string) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    try {
      const begin = await passkeyLoginBeginAPI(inputEmail);
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge: b64urlToBuffer(begin.public_key.challenge),
          rpId: begin.public_key.rpId,
          timeout: begin.public_key.timeout,
          userVerification: begin.public_key.userVerification,
          allowCredentials: (begin.public_key.allowCredentials || []).map((c: any) => ({
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
    setAuthStep("");

    if (!email) {
      showToast("Vui lòng nhập email hoặc tên tài khoản", "error");
      setIsSubmitting(false);
      return;
    }

    if (!password) {
      showToast("Vui lòng nhập mật khẩu để đăng nhập", "error");
      setIsSubmitting(false);
      return;
    }

    try {
      const data = await login(email, password);
      
      await loginState(data.access_token);
      
      if (!data.user?.has_passkey) {
        setPendingPasskeyEmail(data.user?.email || email);
        showToast("Đăng nhập thành công. Hãy cân nhắc thiết lập Passkey", "success");
      } else {
        showToast("Đăng nhập thành công", "success");
        router.push("/");
      }
    } catch (err: any) {
      showToast(err.message || "Sai email hoặc mật khẩu", "error");
      setIsSubmitting(false);
    }
  };

  const [pendingPasskeyEmail, setPendingPasskeyEmail] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navbar />
      
      {pendingPasskeyEmail && (
        <PasskeyPrompt 
          email={pendingPasskeyEmail} 
          onClose={() => router.push("/")} 
          onSuccess={() => router.push("/")} 
        />
      )}
      <div 
        className="sm:mx-auto sm:w-full sm:max-w-md mt-16 transition-all duration-300"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <h2 className="text-center text-4xl font-bold tracking-tight text-black">
          Đăng nhập DocLib
        </h2>
        <p className="mt-3 text-center text-base text-zinc-500">
          Hoặc{" "}
          <a href="/register" className="font-bold text-black hover:underline active:scale-95 inline-block transition-transform">
            tạo tài khoản mới
          </a>
        </p>
      </div>

      <div 
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md transition-all duration-300 delay-150"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className="bg-white py-8 px-4 sm:px-10 border border-zinc-200 rounded-sm">
          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label htmlFor="email" className="block text-base font-bold text-black">
                Email hoặc tên tài khoản
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="text"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-base font-bold text-black">
                Mật khẩu
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm placeholder-zinc-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
                />
                <div className="mt-2 text-right">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-xs font-medium text-zinc-500 hover:text-black active:scale-95 transition-transform"
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
                  className="h-4 w-4 text-black focus:ring-black border-zinc-300 rounded-sm"
                />
                <label htmlFor="remember-me" className="ml-2 block text-base text-zinc-600">
                  Ghi nhớ đăng nhập
                </label>
              </div>

              <div className="text-base">
                <a href="/forgot-password" className="font-bold text-black hover:underline active:scale-95 inline-block transition-transform">
                  Quên mật khẩu
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center gap-3 py-3 px-4 border border-transparent rounded-sm text-base font-bold text-white bg-black hover:bg-zinc-800 focus:outline-none transition-all active:scale-95 disabled:bg-zinc-400 disabled:cursor-not-allowed"
              >
                {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
                {isSubmitting ? "Đang xử lý" : "Đăng nhập ngay"}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-zinc-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-zinc-500">Đăng nhập bằng phương thức khác</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={async () => {
                  if (!email) {
                    showToast("Vui lòng nhập email trước để dùng Passkey", "error");
                    return;
                  }
                  await completePasskeyLogin(email);
                }}
                className="w-full inline-flex justify-center py-2 px-4 border border-zinc-200 rounded-sm bg-white text-sm font-medium text-zinc-700 hover:bg-zinc-50 active:scale-95 transition-all gap-2 items-center"
              >
                <Fingerprint className="w-4 h-4 text-black" />
                Passkey
              </button>
              <button
                type="button"
                onClick={async () => {
                  try {
                    showToast("Đang kết nối tới Google", "info");
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google/login`);
                    const resp = await res.json();
                    if (resp.data && resp.data.url) window.location.href = resp.data.url;
                    else throw new Error("Không lấy được link đăng nhập");
                  } catch (err: any) {
                    showToast("Không thể kết nối với google", "error");
                  }
                }}
                className="w-full inline-flex justify-center py-2 px-4 border border-zinc-200 rounded-sm bg-white text-sm font-medium text-zinc-700 hover:bg-zinc-50 active:scale-95 transition-all"
              >
                Google
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}