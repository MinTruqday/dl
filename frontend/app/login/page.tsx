"use client";
import Navbar from "@/app/components/Navbar";
import { ChangeEvent, FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import {
  forgotPasswordAPI,
  login,
  passkeyLoginBeginAPI,
  passkeyLoginFinishAPI,
  passkeyRegisterBeginAPI,
  passkeyRegisterFinishAPI,
  resetPasswordAPI,
} from "@/app/lib/api";
import { useAuth } from "@/app/contexts/AuthContext";

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
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const router = useRouter();
  const { loginState } = useAuth();

  const completePasskeyLogin = async (inputEmail: string) => {
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
    const verify = await passkeyLoginFinishAPI(
      inputEmail,
      begin.challenge_id,
      bytesToB64url(cred.rawId),
      bytesToB64url(resp.clientDataJSON),
      bytesToB64url(resp.authenticatorData),
      bytesToB64url(resp.signature)
    );

    await loginState(verify.access_token || verify);
    router.push("/");
  };

  const registerPasskeyForEmail = async (inputEmail: string) => {
    const regBegin = await passkeyRegisterBeginAPI(inputEmail);
    const credential = await navigator.credentials.create({
      publicKey: {
        challenge: b64urlToBuffer(regBegin.public_key.challenge),
        rp: regBegin.public_key.rp,
        user: {
          ...regBegin.public_key.user,
          id: b64urlToBuffer(regBegin.public_key.user.id),
        },
        pubKeyCredParams: regBegin.public_key.pubKeyCredParams,
        timeout: regBegin.public_key.timeout,
        attestation: regBegin.public_key.attestation,
        authenticatorSelection: regBegin.public_key.authenticatorSelection,
        excludeCredentials: (regBegin.public_key.excludeCredentials || []).map((c: any) => ({
          type: c.type,
          id: b64urlToBuffer(c.id),
        })),
      },
    });

    const regCred = credential as PublicKeyCredential;
    const regResp = regCred.response as AuthenticatorAttestationResponse;
    await passkeyRegisterFinishAPI(
      inputEmail,
      regBegin.challenge_id,
      bytesToB64url(regCred.rawId),
      bytesToB64url(regResp.clientDataJSON),
      bytesToB64url(regResp.attestationObject)
    );
  };

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    setInfo("");
    setAuthStep("");
    let shouldOfferPasskeyEnrollment = false;

    if (!email) {
      setError("Vui lòng nhập email hoặc tên tài khoản.");
      setIsSubmitting(false);
      return;
    }

    if (typeof window !== "undefined" && "credentials" in navigator) {
      try {
          setAuthStep("Đang kết nối bằng Passkey");
          await completePasskeyLogin(email);
          return;
        } catch (passkeyErr: any) {
          setAuthStep("Không thể đăng nhập bằng Passkey. Vui lòng nhập mật khẩu.");
          const msg = String(passkeyErr?.message || "").toLowerCase();
          const noPasskey = msg.includes("chua dang ky passkey");
          if (noPasskey) {
            shouldOfferPasskeyEnrollment = true;
            setInfo("Chưa thiết lập Passkey. Vui lòng đăng nhập bằng mật khẩu trước.");
          } else if (msg) {
            setError(`Đăng nhập bằng Passkey không thành công: ${passkeyErr.message}`);
          }
        }
      }

      if (!password) {
        setError("Vui lòng nhập mật khẩu để đăng nhập.");
        setIsSubmitting(false);
        return;
      }

      try {
        setAuthStep("Đang đăng nhập");
        const data = await login(email, password);
        await loginState(data.access_token || data);

        if (typeof window !== "undefined" && "credentials" in navigator && shouldOfferPasskeyEnrollment) {
          const shouldCreatePasskey = window.confirm("Đăng ký thiết bị này với Passkey để đăng nhập nhanh hơn vào lần sau?");
          if (shouldCreatePasskey) {
            try {
              await registerPasskeyForEmail(email);
              setInfo("Đã đăng ký thiết bị thành công.");
            } catch (registerErr: any) {
              setError(registerErr.message || "Không thể đăng ký thiết bị vào lúc này.");
            }
          }
        }

      router.push("/");
    } catch (err: any) {
      setError(err.message || "Sai email hoặc mật khẩu.");
      setAuthStep("");
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async () => {
    setError("");
    setInfo("");
    if (!email || !email.includes("@")) {
      setError("Vui lòng nhập email trước khi làm mới mật khẩu.");
      return;
    }
    try {
      const data = await forgotPasswordAPI(email);
      setInfo(data.message || "Nếu email tồn tại, liên kết reset đã được gửi.");
    } catch (err: any) {
      setError(err.message || "Không thể gửi mã khôi phục.");
    }
  };

  const handleResetPassword = async () => {
    setError("");
    setInfo("");

    if (!email || !email.includes("@")) {
      setError("Vui lòng nhập email hợp lệ trước khi đổi mật khẩu.");
      return;
    }
    if (!resetToken.trim()) {
      setError("Vui lòng nhập mã khôi phục trước khi đổi mật khẩu.");
      return;
    }
    try {
      const data = await resetPasswordAPI(resetToken, newPassword);
      setInfo(data.message || "Đã đổi mật khẩu.");
    } catch (err: any) {
      setError(err.message || "Reset mật khẩu thất bại.");
    }
  };


  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navbar />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-extrabold text-foreground font-bold">
          Đăng nhập tài khoản DocLib
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Hoặc{" "}
          <a href="/register" className="font-medium text-black hover:underline">
            tạo tài khoản mới
          </a>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-8 px-4  sm: sm:px-10 border border-border">
          <form className="space-y-6" onSubmit={handleLogin}>
            {info && (
              <div className="bg-gray-100 border-l-4 border-black p-4  text-sm font-medium text-black">
                {info}
              </div>
            )}
            {error && (
              <div className="bg-gray-100 border-l-4 border-black p-4  text-sm font-medium text-black font-bold outline-black">
                {error}
              </div>
            )}
            {authStep && !error && (
              <div className="bg-background border-l-4 border-gray-400 p-4  text-sm font-medium text-gray-700">
                <span className="inline-flex items-center gap-2">
                  {isSubmitting && <span className="h-3 w-3 animate-spin rounded-none border-2 border-gray-400 border-t-transparent" />}
                  {authStep}
                </span>
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email hoặc Tên tài khoản
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
                  className="appearance-none block w-full px-3 py-2 border border-border   placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
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
                  className="appearance-none block w-full px-3 py-2 border border-border   placeholder-gray-400 focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
                <div className="mt-2 text-right">
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-xs font-medium text-muted-foreground hover:text-black"
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
                  className="h-4 w-4 text-black focus:ring-black border-border rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-foreground">
                  Ghi nhớ đăng nhập
                </label>
              </div>

              <div className="text-sm">
                <button type="button" onClick={() => setShowForgotModal(true)} className="font-medium text-black hover:underline">
                  Quên mật khẩu?
                </button>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center py-2 px-4 border border-transparent   text-sm font-medium text-white bg-black hover:bg-gray-800 focus:outline-none transition-colors disabled:bg-zinc-400 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Đang xử lý" : "Đăng nhập ngay"}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-card text-muted-foreground">Đăng nhập bằng phương thức khác</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-3">
              <div>
                <button
                  type="button"
                  onClick={async () => {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google/login`);
                    const data = await res.json();
                    if (data.url) window.location.href = data.url;
                  }}
                  className="w-full inline-flex justify-center py-2 px-4 border border-border   bg-card text-sm font-medium text-muted-foreground hover:bg-background"
                >
                  <span className="sr-only">Đăng nhập tài khoản Google</span>
                  Google
                </button>
              </div>

            </div>
          </div>
        </div>
      </div>

      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md bg-card   border border-border p-5">
            <h3 className="text-lg font-bold text-foreground">Khôi phục mật khẩu</h3>
            <p className="mt-1 text-sm text-muted-foreground">B1: nhập email để lấy mã xác thực. B2: nhập đúng mã xác thực rồi đổi mật khẩu. Sai mã thì nhập lại, hoặc bấm Đóng để bỏ qua.</p>

            <div className="mt-4 space-y-3">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-border  focus:outline-none focus:ring-1 focus:ring-black"
              />
              <button
                type="button"
                onClick={handleForgotPassword}
                className="w-full px-3 py-2 bg-black text-white  hover:bg-gray-800"
              >
                Gửi mã xác thực
              </button>
              <input
                type="text"
                placeholder="Mã xác thực"
                value={resetToken}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setResetToken(e.target.value)}
                className="w-full px-3 py-2 border border-border  focus:outline-none focus:ring-1 focus:ring-black"
              />
              <input
                type="password"
                placeholder="Mật khẩu mới"
                value={newPassword}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
                className="w-full px-3 py-2 border border-border  focus:outline-none focus:ring-1 focus:ring-black"
              />
              <button
                type="button"
                onClick={handleResetPassword}
                className="w-full px-3 py-2 border border-border  hover:bg-background"
              >
                Đặt lại mật khẩu
              </button>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => setShowForgotModal(false)}
                className="px-3 py-2 text-sm border border-border  hover:bg-background"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}