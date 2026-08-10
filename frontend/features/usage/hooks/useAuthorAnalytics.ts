"use client";

import { useCallback, useEffect, useState } from "react";
import { getAuthorRevenueAPI } from "@/features/finance/services/monetization.service";

export type AuthorDocumentMetric = {
  id: string;
  slug?: string;
  title: string;
  views: number;
  price: number;
  purchases: number;
  revenue: number;
};

export type AuthorAnalytics = {
  total_revenue: number;
  total_views: number;
  total_points: number;
  available_balance: number;
  documents: AuthorDocumentMetric[];
};

const initialData: AuthorAnalytics = {
  total_revenue: 0,
  total_views: 0,
  total_points: 0,
  available_balance: 0,
  documents: [],
};

export function useAuthorAnalytics() {
  const [data, setData] = useState<AuthorAnalytics>(initialData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getAuthorRevenueAPI();
      setData(response?.data || response || initialData);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải số liệu",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, reload: load };
}
