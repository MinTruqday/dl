"use client";

import { useCallback, useEffect, useState } from "react";
import { getDocumentsAPI } from "@/features/content/services/document.service";
import {
  getPersonalizedRecommendationsAPI,
  getTagsCategoriesAPI,
} from "@/features/engagement/services/discovery.service";
import type { DocumentSummary } from "@/shared/components/documents/DocumentResults";

export function useExploreDocuments() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [recommendations, setRecommendations] = useState<DocumentSummary[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadContext = useCallback(async () => {
    const [categoryResult, recommendationResult] = await Promise.allSettled([
      getTagsCategoriesAPI(),
      getPersonalizedRecommendationsAPI(4),
    ]);
    if (categoryResult.status === "fulfilled") {
      const data = categoryResult.value?.data || categoryResult.value || {};
      setCategories(Array.isArray(data.categories) ? data.categories : []);
    }
    if (recommendationResult.status === "fulfilled") {
      const data =
        recommendationResult.value?.data || recommendationResult.value || [];
      setRecommendations(Array.isArray(data) ? data : []);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getDocumentsAPI(
        undefined,
        "latest",
        category === "all" ? undefined : category,
      );
      const data = response?.data || response || [];
      setDocuments(Array.isArray(data) ? data : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  useEffect(() => {
    const timer = window.setTimeout(loadDocuments, 250);
    return () => window.clearTimeout(timer);
  }, [loadDocuments]);

  return {
    documents,
    recommendations,
    categories,
    category,
    setCategory,
    loading,
    error,
    reload: loadDocuments,
  };
}
