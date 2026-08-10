"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getAcademicMetricsAPI,
  getDocumentAnalyticsAPI,
} from "@/features/content/services/document.service";
import {
  getAuthorRevenueAPI,
  setDocumentPricingAPI,
} from "@/features/finance/services/monetization.service";
import type {
  AuthorAnalytics,
  AuthorDocumentMetric,
} from "@/features/usage/hooks/useAuthorAnalytics";

const empty: AuthorAnalytics = {
  total_revenue: 0,
  total_views: 0,
  total_points: 0,
  available_balance: 0,
  documents: [],
};

export function useDocumentStatistics() {
  const [data, setData] = useState<AuthorAnalytics>(empty);
  const [selected, setSelected] = useState<AuthorDocumentMetric | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [academic, setAcademic] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getAuthorRevenueAPI();
      setData(response.data ?? response ?? empty);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải số liệu",
      );
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => void reload(), [reload]);
  const inspect = async (document: AuthorDocumentMetric) => {
    setSelected(document);
    setProcessing(true);
    setError("");
    try {
      const [analyticsResponse, academicResponse] = await Promise.all([
        getDocumentAnalyticsAPI(document.id),
        getAcademicMetricsAPI(document.id),
      ]);
      setAnalytics(analyticsResponse?.data ?? analyticsResponse);
      setAcademic(academicResponse?.data ?? academicResponse);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải số liệu tài liệu",
      );
    } finally {
      setProcessing(false);
    }
  };
  const setPrice = async (price: number) => {
    if (!selected) return false;
    setProcessing(true);
    setError("");
    try {
      await setDocumentPricingAPI(selected.id, price);
      setNotice("Đã cập nhật giá tài liệu");
      await reload();
      setSelected((current) => (current ? { ...current, price } : null));
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể cập nhật giá",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  };
  return {
    data,
    selected,
    setSelected,
    analytics,
    academic,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    inspect,
    setPrice,
  };
}
