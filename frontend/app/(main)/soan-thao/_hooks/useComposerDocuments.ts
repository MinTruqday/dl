"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getMyDocumentsAPI,
  getTrashAPI,
  restoreDocumentAPI,
} from "@/features/content/services/document.service";

export type ComposerDocument = {
  _id?: string;
  id?: string;
  title?: string;
  status?: string;
  content_format?: string;
  updated_at?: string;
  created_at?: string;
};

export function useComposerDocuments(source: "drafts" | "trash") {
  const [documents, setDocuments] = useState<ComposerDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [restoringId, setRestoringId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response =
        source === "trash" ? await getTrashAPI() : await getMyDocumentsAPI();
      const items = response?.data || response || [];
      setDocuments(Array.isArray(items) ? items : []);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [source]);

  useEffect(() => {
    load();
  }, [load]);

  const visibleDocuments = useMemo(() => {
    if (source === "trash") return documents;
    return documents.filter(
      (document) => String(document.status || "").toLowerCase() === "draft",
    );
  }, [documents, source]);

  const restore = useCallback(async (id: string) => {
    setRestoringId(id);
    setError("");
    try {
      await restoreDocumentAPI(id);
      setDocuments((items) =>
        items.filter((item) => (item._id || item.id) !== id),
      );
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể khôi phục tài liệu",
      );
    } finally {
      setRestoringId("");
    }
  }, []);

  return {
    documents: visibleDocuments,
    loading,
    error,
    restoringId,
    reload: load,
    restore,
  };
}
