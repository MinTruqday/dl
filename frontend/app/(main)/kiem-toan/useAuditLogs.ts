"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import {
  AuditQueryParams,
  exportAuditRecordsAPI,
  getAuditRecordsAPI,
  getAuditStatsAPI,
  verifyAuditIntegrityAPI,
} from "@/features/management/services/audit.service";

export interface AuditLog {
  id?: string;
  _id?: string;
  actor_id?: string;
  actor_email?: string;
  module?: string;
  action?: string;
  severity?: string;
  status?: string;
  target_type?: string;
  target_id?: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
  timestamp?: string;
  created_at?: string;
  hash?: string;
}

export interface AuditStats {
  total_events: number;
  today_events: number;
  security_alerts: number;
  failed_operations: number;
  admin_actions: number;
  module_distribution?: Record<string, number>;
  severity_distribution?: Record<string, number>;
}

export interface IntegrityStatus {
  verified: boolean;
  checked_records: number;
  tampered_records: number;
  status: string;
}

export function useAuditLogs(enabled: boolean) {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [moduleFilter, setModuleFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0);
  const [integrityStatus, setIntegrityStatus] = useState<IntegrityStatus | null>(null);
  const [verifyingIntegrity, setVerifyingIntegrity] = useState(false);
  const [exporting, setExporting] = useState(false);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const calculateDateBounds = useCallback(() => {
    if (dateRange === "today") {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      return { from_date: start.toISOString(), to_date: "" };
    }
    if (dateRange === "7days") {
      const past = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      return { from_date: past.toISOString(), to_date: "" };
    }
    if (dateRange === "30days") {
      const past = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
      return { from_date: past.toISOString(), to_date: "" };
    }
    if (dateRange === "custom") {
      return {
        from_date: fromDate ? new Date(fromDate).toISOString() : "",
        to_date: toDate ? new Date(toDate).toISOString() : "",
      };
    }
    return { from_date: "", to_date: "" };
  }, [dateRange, fromDate, toDate]);

  const loadData = useCallback(
    async (refresh = false) => {
      if (!enabled) {
        setLoading(false);
        return;
      }
      refresh ? setRefreshing(true) : setLoading(true);
      setError("");

      const { from_date, to_date } = calculateDateBounds();
      const queryParams: AuditQueryParams = {
        page,
        page_size: pageSize,
        module: moduleFilter || undefined,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        search: searchQuery.trim() || undefined,
        from_date: from_date || undefined,
        to_date: to_date || undefined,
      };

      try {
        const [recordsRes, statsRes] = await Promise.allSettled([
          getAuditRecordsAPI(queryParams),
          getAuditStatsAPI(),
        ]);

        if (recordsRes.status === "fulfilled") {
          const resData = recordsRes.value?.data || recordsRes.value || {};
          const items = Array.isArray(resData.items) ? resData.items : [];
          setLogs(items);
          setTotal(Number(resData.total) || items.length);
          setTotalPages(Number(resData.total_pages) || 1);
        } else {
          setError(recordsRes.reason instanceof Error ? recordsRes.reason.message : "Không thể tải danh sách nhật ký");
        }

        if (statsRes.status === "fulfilled") {
          const statData = statsRes.value?.data || statsRes.value || null;
          setStats(statData);
        }
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Lỗi hệ thống khi tải nhật ký");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [
      enabled,
      page,
      pageSize,
      moduleFilter,
      severityFilter,
      statusFilter,
      searchQuery,
      calculateDateBounds,
    ]
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (autoRefreshInterval > 0 && enabled) {
      timerRef.current = setInterval(() => {
        loadData(true);
      }, autoRefreshInterval * 1000);
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoRefreshInterval, enabled, loadData]);

  const verifyIntegrity = async (logId?: string) => {
    setVerifyingIntegrity(true);
    try {
      const res = await verifyAuditIntegrityAPI(logId);
      const data = res?.data || res;
      setIntegrityStatus(data);
      return data;
    } catch (err) {
      const fallback: IntegrityStatus = {
        verified: false,
        checked_records: 0,
        tampered_records: 1,
        status: "ERROR",
      };
      setIntegrityStatus(fallback);
      return fallback;
    } finally {
      setVerifyingIntegrity(false);
    }
  };

  const exportData = async (format: "csv" | "json") => {
    setExporting(true);
    try {
      const { from_date, to_date } = calculateDateBounds();
      const res = await exportAuditRecordsAPI({
        format,
        module: moduleFilter || undefined,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        search: searchQuery.trim() || undefined,
        from_date: from_date || undefined,
        to_date: to_date || undefined,
      });

      const exportPayload = res?.data || res;
      if (format === "csv" && typeof exportPayload.content === "string") {
        const blob = new Blob([exportPayload.content], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", exportPayload.filename || "kiem_toan.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else if (format === "json") {
        const jsonContent = JSON.stringify(exportPayload.content || exportPayload, null, 2);
        const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", exportPayload.filename || "kiem_toan.json");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi khi kết xuất dữ liệu");
    } finally {
      setExporting(false);
    }
  };

  const resetFilters = () => {
    setModuleFilter("");
    setSeverityFilter("");
    setStatusFilter("");
    setSearchQuery("");
    setDateRange("all");
    setFromDate("");
    setToDate("");
    setPage(1);
  };

  return {
    logs,
    stats,
    total,
    totalPages,
    page,
    pageSize,
    moduleFilter,
    severityFilter,
    statusFilter,
    searchQuery,
    dateRange,
    fromDate,
    toDate,
    loading,
    refreshing,
    error,
    selectedLog,
    autoRefreshInterval,
    integrityStatus,
    verifyingIntegrity,
    exporting,
    setPage,
    setPageSize,
    setModuleFilter,
    setSeverityFilter,
    setStatusFilter,
    setSearchQuery,
    setDateRange,
    setFromDate,
    setToDate,
    setSelectedLog,
    setAutoRefreshInterval,
    reload: () => loadData(true),
    verifyIntegrity,
    exportData,
    resetFilters,
  };
}
