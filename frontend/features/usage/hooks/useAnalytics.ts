"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AuthorOverviewData,
  DocumentAnalyticsItem,
  exportAnalyticsAPI,
  getAuthorDocumentsAnalyticsAPI,
  getAuthorOverviewAPI,
  getAuthorTrendsAPI,
  getSystemAnalyticsAPI,
  SystemAnalyticsData,
  TimeseriesItem,
} from "@/features/management/services/analytics.service";
import { getUserMe } from "@/features/authentication/services/session.service";

export type TimePreset = "all" | "today" | "7d" | "30d" | "90d" | "custom";
export type AnalyticsTab = "author" | "system";

const initialOverview: AuthorOverviewData = {
  total_revenue: 0,
  total_views: 0,
  total_purchases: 0,
  conversion_rate: 0,
  unique_buyers: 0,
  total_documents: 0,
  available_balance: 0,
  reward_points: 0,
};

const initialSystem: SystemAnalyticsData = {
  total_revenue: 0,
  total_purchases: 0,
  total_views: 0,
  total_documents: 0,
  total_users: 0,
  total_authors: 0,
  top_authors: [],
  top_documents: [],
};

export function useAnalytics() {
  const [tab, setTab] = useState<AnalyticsTab>("author");
  const [isAdmin, setIsAdmin] = useState(false);
  const [timePreset, setTimePreset] = useState<TimePreset>("30d");
  const [customFromDate, setCustomFromDate] = useState("");
  const [customToDate, setCustomToDate] = useState("");

  const [overview, setOverview] = useState<AuthorOverviewData>(initialOverview);
  const [trends, setTrends] = useState<TimeseriesItem[]>([]);
  const [documents, setDocuments] = useState<DocumentAnalyticsItem[]>([]);
  const [totalDocs, setTotalDocs] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("revenue");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const [systemData, setSystemData] = useState<SystemAnalyticsData>(initialSystem);
  const [selectedDoc, setSelectedDoc] = useState<DocumentAnalyticsItem | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date>(new Date());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    getUserMe().then((u) => {
      if (u && String(u.role).toLowerCase() === "admin") {
        setIsAdmin(true);
      }
    }).catch(() => {});
  }, []);

  const calculateDateRange = useCallback(() => {
    const now = new Date();
    let fromDate: string | undefined;
    let toDate: string | undefined;

    if (timePreset === "today") {
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
      fromDate = todayStart.toISOString();
      toDate = now.toISOString();
    } else if (timePreset === "7d") {
      const d = new Date();
      d.setDate(d.getDate() - 7);
      fromDate = d.toISOString();
      toDate = now.toISOString();
    } else if (timePreset === "30d") {
      const d = new Date();
      d.setDate(d.getDate() - 30);
      fromDate = d.toISOString();
      toDate = now.toISOString();
    } else if (timePreset === "90d") {
      const d = new Date();
      d.setDate(d.getDate() - 90);
      fromDate = d.toISOString();
      toDate = now.toISOString();
    } else if (timePreset === "custom") {
      if (customFromDate) fromDate = new Date(customFromDate).toISOString();
      if (customToDate) toDate = new Date(customToDate).toISOString();
    }

    return { fromDate, toDate };
  }, [timePreset, customFromDate, customToDate]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    const { fromDate, toDate } = calculateDateRange();

    try {
      if (tab === "author") {
        const days = timePreset === "7d" ? 7 : timePreset === "90d" ? 90 : 30;
        const [overviewRes, trendsRes, docsRes] = await Promise.all([
          getAuthorOverviewAPI(fromDate, toDate),
          getAuthorTrendsAPI(days, fromDate, toDate),
          getAuthorDocumentsAnalyticsAPI({
            search,
            sort_by: sortBy,
            sort_order: sortOrder,
            page,
            page_size: pageSize,
            from_date: fromDate,
            to_date: toDate,
          }),
        ]);

        setOverview(overviewRes?.data || initialOverview);
        setTrends(trendsRes?.data || []);
        const docPage = docsRes?.data;
        if (docPage) {
          setDocuments(docPage.items || []);
          setTotalDocs(docPage.total || 0);
          setTotalPages(docPage.total_pages || 1);
        }
      } else {
        const sysRes = await getSystemAnalyticsAPI(fromDate, toDate);
        setSystemData(sysRes?.data || initialSystem);
      }
      setLastRefreshedAt(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải dữ liệu phân tích");
    } finally {
      setLoading(false);
    }
  }, [calculateDateRange, page, pageSize, search, sortBy, sortOrder, tab, timePreset]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (autoRefreshInterval > 0) {
      timerRef.current = setInterval(() => {
        loadData();
      }, autoRefreshInterval * 1000);
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoRefreshInterval, loadData]);

  const handleExport = async (format: "csv" | "json") => {
    setExporting(true);
    const { fromDate, toDate } = calculateDateRange();
    try {
      const res = await exportAnalyticsAPI({
        format,
        scope: tab,
        from_date: fromDate,
        to_date: toDate,
      });
      const data = res?.data;
      if (!data) return;

      let blob: Blob;
      if (format === "csv") {
        blob = new Blob([data.content], { type: "text/csv;charset=utf-8;" });
      } else {
        blob = new Blob([JSON.stringify(data.content, null, 2)], {
          type: "application/json",
        });
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", data.filename || `phan_tich.${format}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể kết xuất báo cáo");
    } finally {
      setExporting(false);
    }
  };

  return {
    tab,
    setTab,
    isAdmin,
    timePreset,
    setTimePreset,
    customFromDate,
    setCustomFromDate,
    customToDate,
    setCustomToDate,
    overview,
    trends,
    documents,
    totalDocs,
    totalPages,
    page,
    setPage,
    pageSize,
    setPageSize,
    search,
    setSearch,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    systemData,
    selectedDoc,
    setSelectedDoc,
    loading,
    error,
    exporting,
    autoRefreshInterval,
    setAutoRefreshInterval,
    lastRefreshedAt,
    reload: loadData,
    handleExport,
  };
}
