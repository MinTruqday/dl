"use client";

import { useState } from "react";
import {
  passkeyRegisterBeginAPI,
  passkeyRegisterFinishAPI,
} from "@/features/authentication/services/session.service";
import { b64urlToBuffer, bufferToB64url } from "@/features/authentication/lib/webauthn";

export function usePasskeySetup(email: string, onSuccess: () => void) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const register = async () => {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const begin = await passkeyRegisterBeginAPI(email);
      const result = await navigator.credentials.create({
        publicKey: {
          challenge: b64urlToBuffer(begin.challenge),
          rp: begin.rp,
          user: { ...begin.user, id: b64urlToBuffer(begin.user.id) },
          pubKeyCredParams: begin.pubKeyCredParams,
          timeout: begin.timeout,
          attestation: begin.attestation,
          authenticatorSelection: begin.authenticatorSelection,
        },
      });
      if (!result) throw new Error("Không nhận được thông tin khóa truy cập");
      const credential = result as PublicKeyCredential;
      const response = credential.response as AuthenticatorAttestationResponse;
      await passkeyRegisterFinishAPI(email, {
        id: credential.id,
        rawId: bufferToB64url(credential.rawId),
        type: credential.type,
        response: {
          attestationObject: bufferToB64url(response.attestationObject),
          clientDataJSON: bufferToB64url(response.clientDataJSON),
        },
      });
      onSuccess();
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể thiết lập khóa truy cập",
      );
    } finally {
      setLoading(false);
    }
  };

  return { loading, error, register };
}
