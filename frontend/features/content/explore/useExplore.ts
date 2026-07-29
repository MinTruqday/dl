"use client";

import { useCallback, useEffect, useState } from "react";
import { getDocumentsAPI } from "../services/document.service";
import {
  getPersonalizedRecommendationsAPI,
  getTagsCategoriesAPI,
} from "../services/discovery.service";
import { useToast } from "@/shared/contexts/ToastContext";
import type { ExploreDocument, ExploreView } from "./types";

export function useExplore() {
  const { showToast } = useToast();
  const [documents, setDocuments] = useState<ExploreDocument[]>([]);
  const [recommendations, setRecommendations] = useState<ExploreDocument[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState<string | null>(null);
  const [view, setView] = useState<ExploreView>("grid");
  const [loading, setLoading] = useState(true);

  const loadOverview = useCallback(async () => {
    try {
      const [categoryResponse, recommendationResponse] = await Promise.all([
        getTagsCategoriesAPI(),
        getPersonalizedRecommendationsAPI(4),
      ]);
      setCategories(
        categoryResponse.data?.categories ||
          categoryResponse.categories ||
          [],
      );
      setRecommendations(
        recommendationResponse.data || recommendationResponse || [],
      );
    } catch {
      showToast("Không thể tải gợi ý", "error");
    }
  }, [showToast]);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getDocumentsAPI(
        undefined,
        "latest",
        category || undefined,
      );
      setDocuments(response.data || response || []);
    } catch {
      showToast("Không thể tải tài liệu", "error");
    } finally {
      setLoading(false);
    }
  }, [category, showToast]);

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  return {
    documents,
    recommendations,
    categories,
    category,
    setCategory,
    view,
    setView,
    loading,
  };
}
