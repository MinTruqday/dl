"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getActiveCollectionJobsAPI,
  getCollectorLogsAPI,
  getCollectorStatsAPI,
  stopCollectionAPI,
  triggerCollectionAPI,
} from "@/features/collection/services/collection.service";

export function useCollector() {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const [stats, setStats] = useState<any>({});
  const [jobs, setJobs] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(
    async (quiet = false) => {
      if (!allowed) {
        setLoading(false);
        return;
      }
      if (!quiet) setLoading(true);
      const results = await Promise.allSettled([
        getCollectorStatsAPI(),
        getActiveCollectionJobsAPI(),
        getCollectorLogsAPI(),
      ]);
      if (results[0].status === "fulfilled")
        setStats(results[0].value?.data || results[0].value || {});
      if (results[1].status === "fulfilled") {
        const value = results[1].value?.data || results[1].value || [];
        setJobs(Array.isArray(value) ? value : value.jobs || []);
      }
      if (results[2].status === "fulfilled") {
        const value = results[2].value?.data || results[2].value || [];
        setLogs(Array.isArray(value) ? value : []);
      }
      if (results.some((result) => result.status === "rejected"))
        setError("Một phần dữ liệu thu thập chưa tải được");
      else setError("");
      setLoading(false);
    },
    [allowed],
  );

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!allowed) return;
    const timer = window.setInterval(() => load(true), 5000);
    return () => window.clearInterval(timer);
  }, [allowed, load]);

  const start = async (source: string, pages: number | string) =>
    mutate(() => triggerCollectionAPI(source, pages));
  const stop = async () => mutate(stopCollectionAPI);

  async function mutate(action: () => Promise<any>) {
    if (processing) return false;
    setProcessing(true);
    setError("");
    try {
      await action();
      await load(true);
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể cập nhật tiến trình thu thập",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  }

  return {
    stats,
    jobs,
    logs,
    allowed,
    loading: authLoading || loading,
    processing,
    error,
    reload: load,
    start,
    stop,
  };
}
