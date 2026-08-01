"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createCommentAPI,
  deleteCommentAPI,
  getCommentsByItemAPI,
} from "@/features/content/services/collaboration.service";
import { getMyDocumentsAPI } from "@/features/content/services/document.service";

export type CommentRecord = {
  id?: string;
  _id?: string;
  content: string;
  created_at: string;
  author?: { username?: string; full_name?: string };
};

export function useDocumentComments() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [comments, setComments] = useState<CommentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    getMyDocumentsAPI()
      .then((response) => {
        const rows = response.data ?? response ?? [];
        setDocuments(rows);
        setDocumentId(rows[0]?._id ?? rows[0]?.id ?? "");
      })
      .catch((cause) =>
        setError(
          cause instanceof Error ? cause.message : "Không thể tải tài liệu",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  const loadComments = useCallback(async () => {
    if (!documentId) return setComments([]);
    setLoading(true);
    setError("");
    try {
      const response = await getCommentsByItemAPI(documentId);
      setComments(response.data ?? []);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải bình luận",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => void loadComments(), [loadComments]);

  const reply = async (content: string) => {
    if (!content.trim() || !documentId) return false;
    setProcessing(true);
    setError("");
    try {
      await createCommentAPI({
        item_id: documentId,
        item_type: "document",
        content: content.trim(),
      });
      setNotice("Bình luận đã được gửi");
      await loadComments();
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể gửi bình luận",
      );
      return false;
    } finally {
      setProcessing(false);
    }
  };

  const resolve = async (commentId: string) => {
    setProcessing(true);
    setError("");
    try {
      await deleteCommentAPI(commentId);
      setNotice("Bình luận đã được giải quyết");
      await loadComments();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể giải quyết bình luận",
      );
    } finally {
      setProcessing(false);
    }
  };

  return {
    documents,
    documentId,
    setDocumentId,
    comments,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    loadComments,
    reply,
    resolve,
  };
}
