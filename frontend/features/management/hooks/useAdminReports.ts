"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  getAdminReportsAPI,
  updateAdminReportAPI,
} from "@/features/management/services/health.service";

export type AdminReport = {
  _id?: string;
  id?: string;
  item_type?: string;
  target_type?: string;
  item_id?: string;
  target_id?: string;
  reason?: string;
  description?: string;
  reporter_name?: string;
  status?: string;
  created_at?: string;
};

export function useAdminReports(query: string, filter: "pending" | "closed") {
  const { user, isLoading: authLoading } = useAuth() as any;
  const allowed = String(user?.role || "").toLowerCase() === "admin";
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!allowed) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await getAdminReportsAPI();
      const data = response?.data || response || [];
      setReports(Array.isArray(data) ? data : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải báo cáo",
      );
    } finally {
      setLoading(false);
    }
  }, [allowed]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("vi");
    return reports.filter((report) => {
      const closed = ["RESOLVED", "DISMISSED"].includes(
        String(report.status || "").toUpperCase(),
      );
      if (filter === "closed" ? !closed : closed) return false;
      if (!normalized) return true;
      return `${report.reason || ""} ${report.description || ""} ${report.target_id || report.item_id || ""}`
        .toLocaleLowerCase("vi")
        .includes(normalized);
    });
  }, [filter, query, reports]);

  const update = async (id: string, status: "RESOLVED" | "DISMISSED") => {
    if (processing) return false;
    setProcessing(true);
    setError("");
    try {
      await updateAdminReportAPI(id, status);
      setReports((items) =>
        items.map((item) =>
          (item._id || item.id) === id ? { ...item, status } : item,
        ),
      );
      return true;
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể cập nhật báo cáo",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  };

  return {
    reports: visible,
    total: reports.length,
    allowed,
    loading: authLoading || loading,
    processing,
    error,
    reload: load,
    update,
  };
}
