"use client";

import React, { useState } from "react";
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
      showToast(err.message || "Lỗi khởi tạo luồng định danh chứng thư số", "error");
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
            <label className="block text-[13px] font-medium text-[var(--ink-muted)] mb-2">
              Xác thực sinh trắc học
            </label>
            <p className="text-[15px] font-medium text-[var(--ink)] leading-relaxed">
              Dùng vân tay hoặc khuôn mặt để đăng nhập thay cho mật khẩu
            </p>
          </div>
        </div>
      </ModalContent>

      <ModalFooter className="flex-col sm:flex-row">
        {!loading && (
          <button
            onClick={onClose}
            className="button-secondary flex-1"
          >
            Để sau
          </button>
        )}
        <button
          onClick={handleRegister}
          disabled={loading}
          className="button-primary flex-1 disabled:opacity-50"
        >
          {loading ? "Đang xử lý" : "Xác nhận kích hoạt"}
        </button>
      </ModalFooter>
    </Modal>
  );
}
