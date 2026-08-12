"use client";

import { useEffect } from "react";

const RECOVERY_KEY = "doclib:chunk-recovery";

function needsRecovery(reason: unknown) {
  const message = String(
    reason instanceof Error ? reason.message : reason,
  ).toLowerCase();
  return (
    message.includes("chunkloaderror") ||
    message.includes("loading chunk") ||
    message.includes("failed to fetch rsc payload")
  );
}

export function ChunkRecovery() {
  useEffect(() => {
    const clearRecovery = window.setTimeout(
      () => sessionStorage.removeItem(RECOVERY_KEY),
      5000,
    );

    const recover = (reason: unknown) => {
      if (!needsRecovery(reason) || sessionStorage.getItem(RECOVERY_KEY)) return;
      sessionStorage.setItem(RECOVERY_KEY, "1");
      window.location.reload();
    };

    const onError = (event: ErrorEvent) => recover(event.error || event.message);
    const onUnhandledRejection = (event: PromiseRejectionEvent) =>
      recover(event.reason);

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);
    return () => {
      window.clearTimeout(clearRecovery);
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, []);

  return null;
}
