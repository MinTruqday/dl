"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getDocumentsAPI } from "@/features/content/services/document.service";
import type { DocumentSummary } from "@/shared/components/documents/DocumentResults";

export type SearchFilters = {
  price: "all" | "free" | "paid";
  time: "all" | "day" | "week" | "month";
  sort: "latest" | "most_viewed";
};

const initialFilters: SearchFilters = {
  price: "all",
  time: "all",
  sort: "latest",
};

export function useDocumentSearch() {
  const query = useSearchParams().get("q")?.trim() || "";
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [loading, setLoading] = useState(Boolean(query));
  const [error, setError] = useState("");

  useEffect(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem("doclib_search_history") || "[]",
      );
      setHistory(
        Array.isArray(saved)
          ? saved.filter((item) => typeof item === "string").slice(0, 8)
          : [],
      );
    } catch {
      setHistory([]);
    }
  }, []);

  const load = useCallback(async () => {
    if (!query) {
      setDocuments([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await getDocumentsAPI(
        query,
        filters.sort === "latest" ? "latest" : "views",
      );
      const data = response?.data || response || [];
      setDocuments(Array.isArray(data) ? data : []);
      setHistory((current) => {
        const next = [query, ...current.filter((item) => item !== query)].slice(
          0,
          8,
        );
        localStorage.setItem("doclib_search_history", JSON.stringify(next));
        return next;
      });
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tìm tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [filters.sort, query]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const now = Date.now();
    const windowByTime = {
      all: Infinity,
      day: 86400000,
      week: 604800000,
      month: 2592000000,
    }[filters.time];
    return documents
      .filter((document) => {
        const price = Number(document.price_dl ?? document.price ?? 0);
        if (filters.price === "free" && price > 0) return false;
        if (filters.price === "paid" && price <= 0) return false;
        if (windowByTime !== Infinity && document.created_at) {
          const createdAt = new Date(document.created_at).getTime();
          if (!Number.isFinite(createdAt) || now - createdAt > windowByTime)
            return false;
        }
        return true;
      })
      .sort((first, second) =>
        filters.sort === "most_viewed"
          ? Number(second.views_count ?? second.views ?? 0) -
            Number(first.views_count ?? first.views ?? 0)
          : new Date(second.created_at || 0).getTime() -
            new Date(first.created_at || 0).getTime(),
      );
  }, [documents, filters]);

  const clearHistory = () => {
    localStorage.removeItem("doclib_search_history");
    setHistory([]);
  };

  return {
    query,
    documents: visible,
    history,
    filters,
    setFilters,
    loading,
    error,
    reload: load,
    clearHistory,
  };
}
