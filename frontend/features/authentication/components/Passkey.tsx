"use client";

import React, { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  passkeyRegisterBeginAPI,
  passkeyRegisterFinishAPI,
} from "@/features/authentication/services/session.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

interface PasskeyProps {
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

export default function Passkey({ email, onClose, onSuccess }: PasskeyProps) {
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const handleRegister = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const begin = await passkeyRegisterBeginAPI(email);

      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: b64urlToBuffer(begin.challenge),
          rp: begin.rp,
          user: {
            ...begin.user,
            id: b64urlToBuffer(begin.user.id),
          },
          pubKeyCredParams: begin.pubKeyCredParams,
          timeout: begin.timeout,
          attestation: begin.attestation,
          authenticatorSelection: begin.authenticatorSelection,
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

      showToast("Kích hoạt chứng thư số Passkey hoàn tất", "success");
      onSuccess();
    } catch (err: any) {
      console.error("Error during passkey verification:", err);
      showToast(err.message || "Không thể tạo luồng định danh chứng thư số", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      showCloseButton={!loading}
      className="max-w-sm"
    >
      <ModalHeader>
        <ModalTitle>
          Bảo mật bằng Passkey
        </ModalTitle>
      </ModalHeader>

      <ModalContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="block text-[13px] font-medium text-ink-muted mb-2">
              Xác thực sinh trắc học
            </label>
            <p className="text-[15px] font-medium text-ink leading-relaxed">
              Kích hoạt Passkey để đăng nhập nhanh chóng bằng vân tay hoặc khuôn
              mặt mà không cần mật khẩu.
            </p>
          </div>
        </div>
      </ModalContent>

      <ModalFooter className="flex-col sm:flex-row">
        {!loading && (
          <button
            onClick={onClose}
            className="flex-1 py-3 bg-white text-ink text-[15px] font-medium disabled:opacity-50 flex items-center justify-center rounded-full hover:bg-border transition-colors"
          >
            Để sau
          </button>
        )}
        <button
          onClick={handleRegister}
          disabled={loading}
          className="flex-1 py-3 bg-brand text-white text-[15px] font-medium disabled:opacity-50 flex items-center justify-center rounded-full hover:bg-brand transition-colors"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : null}
          {loading ? "Đang xử lý" : "Xác nhận kích hoạt"}
        </button>
      </ModalFooter>
    </Modal>
  );
}
