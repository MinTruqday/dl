"use client";

import { Suspense } from "react";
import { Button } from "@/shared/components/ui/Button";
import AuthFrame from "@/app/(auth)/_components/AuthFrame";
import AuthLoading from "@/app/(auth)/_components/AuthLoading";
import InlineState from "@/app/_components/InlineState";
import { useGoogleCallback } from "./useGoogleCallback";
import PasskeySetup from "./PasskeySetup";

function GoogleCallbackContent() {
  const { emailForPasskey, error, finish, back } = useGoogleCallback();

  if (emailForPasskey)
    return (
      <AuthFrame title="Thiết lập Passkey">
        <PasskeySetup
          email={emailForPasskey}
          onClose={finish}
          onSuccess={finish}
        />
      </AuthFrame>
    );

  if (error) {
    return (
      <AuthFrame title="Xác thực Google">
        <InlineState title="Không thể đăng nhập" detail={error} tone="danger" />
        <Button className="mt-5 w-full" onClick={back}>
          Quay lại đăng nhập
        </Button>
      </AuthFrame>
    );
  }

  return <AuthLoading />;
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<AuthLoading />}>
      <GoogleCallbackContent />
    </Suspense>
  );
}
