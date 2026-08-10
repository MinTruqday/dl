"use client";

import { useCallback, useEffect, useState } from "react";
import {
  SharedStorageItem,
  getPublicSharedStorageItemAPI,
  validateProtectedShareLinkAPI,
} from "@/features/cloud/services/storage.service";

export function useSharedStorageItem(token: string) {
  const [item, setItem] = useState<SharedStorageItem | null>(null);
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const open = useCallback(
    async (password?: string) => {
      setLoading(true);
      setError("");
      try {
        if (token.startsWith("share_")) {
          const result = await validateProtectedShareLinkAPI(token, password);
          setItem(result.item);
        } else {
          setItem(await getPublicSharedStorageItemAPI(token));
        }
        setPasswordRequired(false);
        return true;
      } catch (cause) {
        const message =
          cause instanceof Error ? cause.message : "Không thể mở liên kết";
        if (message.toLowerCase().includes("mật khẩu")) {
          setPasswordRequired(true);
        } else {
          setError(message);
        }
        return false;
      } finally {
        setLoading(false);
      }
    },
    [token],
  );

  useEffect(() => void open(), [open]);

  return { item, passwordRequired, loading, error, open };
}
