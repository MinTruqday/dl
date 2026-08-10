"use client";

import { useEffect, useRef } from "react";
import { useToast } from "@/shared/contexts/ToastContext";

export function useNoticeToast(
  message?: string | null,
  type: "success" | "error" | "info" = "success",
) {
  const { showToast } = useToast();
  const shown = useRef("");

  useEffect(() => {
    if (!message || message === shown.current) return;
    shown.current = message;
    showToast(message, type);
  }, [message, showToast, type]);

  useEffect(() => {
    if (!message) shown.current = "";
  }, [message]);
}
