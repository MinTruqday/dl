"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getReadingListByIdAPI,
  removeDocumentFromListAPI,
} from "@/features/content/services/library.service";
import type { DocumentSummary } from "@/shared/components/documents/DocumentResults";

type ReadingListDetail = {
  _id?: string;
  name?: string;
  description?: string;
  is_public?: boolean;
  documents_detailed?: DocumentSummary[];
};

export function useReadingList(id: string) {
  const [list, setList] = useState<ReadingListDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError("");
    try {
      const response = await getReadingListByIdAPI(id);
      setList(response?.data || response || null);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Không thể tải danh sách đọc",
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async (documentId: string) => {
    if (removing) return;
    setRemoving(documentId);
    setError("");
    try {
      await removeDocumentFromListAPI(id, documentId);
      setList((current) =>
        current
          ? {
              ...current,
              documents_detailed: (current.documents_detailed || []).filter(
                (document) => (document._id || document.id) !== documentId,
              ),
            }
          : current,
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể gỡ tài liệu",
      );
    } finally {
      setRemoving("");
    }
  };

  return { list, loading, removing, error, reload: load, remove };
}
