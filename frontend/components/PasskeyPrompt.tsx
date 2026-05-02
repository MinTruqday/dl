"use client";

import React, { useState } from "react";
import { ShieldCheck, Fingerprint, X, Loader2 } from "lucide-react";
import { passkeyRegisterBeginAPI, passkeyRegisterFinishAPI } from "@/services/auth.service";
import { useToast } from "@/contexts/ToastContext";

interface PasskeyPromptProps {
  email: string;
  onClose: () => void;
  onSuccess: () => void;
}

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

export default function PasskeyPrompt({ email, onClose, onSuccess }: PasskeyPromptProps) {
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleRegister = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const begin = await passkeyRegisterBeginAPI(email);
      
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: b64urlToBuffer(begin.public_key.challenge),
          rp: begin.public_key.rp,
          user: {
            ...begin.public_key.user,
            id: b64urlToBuffer(begin.public_key.user.id),
          },
          pubKeyCredParams: begin.public_key.pubKeyCredParams,
          timeout: begin.public_key.timeout,
          attestation: begin.public_key.attestation,
          authenticatorSelection: begin.public_key.authenticatorSelection,
        },
      });

      const cred = credential as PublicKeyCredential;
      const resp = cred.response as AuthenticatorAttestationResponse;
      
      const credentialJSON = {
        id: cred.id,
        rawId: bytesToB64url(cred.rawId),
        type: cred.type,
        response: {
          attestationObject: bytesToB64url(resp.attestationObject),
          clientDataJSON: bytesToB64url(resp.clientDataJSON),
        },
      };

      await passkeyRegisterFinishAPI(email, credentialJSON);

      showToast("Đã kích hoạt Passkey thành công!", "success");
      onSuccess();
    } catch (err: any) {
      console.error(err);
      showToast(err.message || "Không thể đăng ký Passkey lúc này", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/40 animate-in fade-in duration-300">
      <div className="bg-white w-full max-w-md border border-zinc-200 overflow-hidden animate-in zoom-in-95 duration-300">
        <div className="p-10 text-center space-y-8">
          <div className="w-20 h-20 bg-zinc-50 border border-zinc-100 flex items-center justify-center mx-auto">
            <Fingerprint className="w-10 h-10 text-black" />
          </div>
          
          <div className="space-y-4">
            <h3 className="text-2xl font-bold tracking-tight text-black">Bảo mật bằng Passkey</h3>
            <p className="text-sm text-zinc-500 font-medium leading-relaxed">
              Kích hoạt Passkey để đăng nhập nhanh chóng bằng vân tay hoặc khuôn mặt mà không cần mật khẩu.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={handleRegister}
              disabled={loading}
              className="h-14 w-full bg-black text-white font-bold text-sm flex items-center justify-center gap-3 hover:bg-zinc-800 transition-all active:scale-95 disabled:bg-zinc-400"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ShieldCheck className="w-5 h-5" />}
              {loading ? "Đang xử lý" : "Thiết lập ngay"}
            </button>
            <button
              onClick={onClose}
              disabled={loading}
              className="h-14 w-full border border-zinc-100 text-zinc-400 font-bold text-sm hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
            >
              Để sau
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
