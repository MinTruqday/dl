"use client";

import React, { useState } from "react";
import { ShieldCheck, Fingerprint, Loader2 } from "lucide-react";
import {
  passkeyRegisterBeginAPI,
  passkeyRegisterFinishAPI,
} from "@/services/authentication.service";
import { useToast } from "@/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

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

export default function Passkey({
  email,
  onClose,
  onSuccess,
}: PasskeyPromptProps) {
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
    <Modal isOpen={true} onClose={onClose} showCloseButton={!loading}>
      <ModalHeader className="text-center">
        <div className="w-20 h-20 bg-white border border-zinc-100 flex items-center justify-center mx-auto mb-8 rounded-sm">
          <Fingerprint className="w-10 h-10 text-black" />
        </div>
        <ModalTitle>Bảo mật bằng Passkey</ModalTitle>
      </ModalHeader>

      <ModalContent className="text-center">
        <p className="text-sm text-zinc-500 font-medium leading-relaxed">
          Kích hoạt Passkey để đăng nhập nhanh chóng bằng vân tay hoặc khuôn mặt
          mà không cần mật khẩu.
        </p>

        <div className="flex flex-col gap-3 pt-4">
          <button
            onClick={handleRegister}
            disabled={loading}
            className="h-16 w-full bg-black text-white font-bold text-sm flex items-center justify-center gap-3 active:scale-95 disabled:bg-zinc-400 rounded-sm transition-transform"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <ShieldCheck className="w-5 h-5" />
            )}
            {loading ? "Đang xử lý" : "Thiết lập ngay"}
          </button>
          {!loading && (
            <button
              onClick={onClose}
              className="h-16 w-full border border-zinc-100 text-zinc-400 font-bold text-sm active:scale-95 rounded-sm transition-transform"
            >
              Để sau
            </button>
          )}
        </div>
      </ModalContent>

      <ModalFooter>
        <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
          Công nghệ bảo mật sinh trắc học tiên tiến
        </p>
      </ModalFooter>
    </Modal>
  );
}

