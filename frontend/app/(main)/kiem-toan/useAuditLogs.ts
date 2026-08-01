"use client";

import { useCallback, useEffect, useState } from "react";
import { getModeratorActivityAPI } from "@/features/management/services/audit.service";

export type AuditLog = {
  id?: string;
  _id?: string;
  action?: string;
  target_type?: string;
  target_id?: string;
  created_at?: string;
  status?: string;
};

export function useAuditLogs(enabled: boolean) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (refresh = false) => {
      if (!enabled) {
        setLoading(false);
        return;
      }
      refresh ? setRefreshing(true) : setLoading(true);
      setError("");
      try {
        const response = await getModeratorActivityAPI();
        const items = response?.data || response || [];
        setLogs(Array.isArray(items) ? items : []);
      } catch (reason) {
        setError(
          reason instanceof Error ? reason.message : "Không thể tải nhật ký",
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [enabled],
  );

  useEffect(() => {
    load();
  }, [load]);

  return { logs, loading, refreshing, error, reload: () => load(true) };
}
