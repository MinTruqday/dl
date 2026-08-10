"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getVersionDiffAPI } from "@/features/compilation/services/editorjs.service";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";
import {
  getDocumentVersionsAPI,
  restoreVersionAPI,
} from "@/features/content/services/version.service";

export function useVersionHistory() {
  const searchParams = useSearchParams();
  const requestedDocumentId = searchParams.get("tai-lieu") || "";
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [versions, setVersions] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    getMyDocumentsAPI()
      .then((response) => {
        const rows = response.data ?? response ?? [];
        setDocuments(rows);
        setDocumentId((current) => {
          const candidate = current || requestedDocumentId;
          return rows.some((item: any) => (item._id ?? item.id) === candidate)
            ? candidate
            : "";
        });
      })
      .catch((cause) =>
        setError(
          cause instanceof Error ? cause.message : "Không thể tải tài liệu",
        ),
      )
      .finally(() => setLoading(false));
  }, [requestedDocumentId]);
  const reload = useCallback(async () => {
    if (!documentId) return setVersions([]);
    setLoading(true);
    setError("");
    try {
      setVersions((await getDocumentVersionsAPI(documentId)) ?? []);
      setSelected([]);
      setComparison(null);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể tải lịch sử phiên bản",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);
  useEffect(() => void reload(), [reload]);
  const toggle = (id: string) =>
    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : current.length < 2
          ? [...current, id]
          : [current[1], id],
    );
  const compare = async () => {
    if (selected.length !== 2) return;
    setProcessing(true);
    setError("");
    try {
      const response = await getVersionDiffAPI(
        documentId,
        selected[0],
        selected[1],
      );
      setComparison(response.data ?? response);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể so sánh phiên bản",
      );
    } finally {
      setProcessing(false);
    }
  };
  const restore = async (id: string) => {
    setProcessing(true);
    setError("");
    try {
      await restoreVersionAPI(id);
      setNotice("Phiên bản đã được khôi phục");
      await reload();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể khôi phục phiên bản",
      );
    } finally {
      setProcessing(false);
    }
  };
  return {
    documents,
    documentId,
    setDocumentId,
    versions,
    selected,
    comparison,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    toggle,
    compare,
    restore,
  };
}
