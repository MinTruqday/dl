"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  createCommentAPI,
  getCommentsByItemAPI,
} from "@/features/collaboration/services/collaboration.service";

export type DiscussionItem = {
  _id: string;
  text?: string;
  content?: string;
  path?: string;
  user?: { full_name?: string; avatar_url?: string };
  created_at: string;
};

export function useDocumentDiscussion(documentId: string) {
  const { user } = useAuth() as any;
  const [comments, setComments] = useState<DiscussionItem[]>([]);
  const [text, setText] = useState("");
  const [replyTo, setReplyTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError("");
    try {
      const response = await getCommentsByItemAPI(documentId);
      setComments(
        Array.isArray(response?.data)
          ? response.data
          : Array.isArray(response)
            ? response
            : [],
      );
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể tải thảo luận",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!user) {
      setError("Đăng nhập để gửi phản hồi");
      return;
    }
    const content = text.trim();
    if (!content) return;
    setSubmitting(true);
    setError("");
    try {
      await createCommentAPI({
        item_id: documentId,
        item_type: "document",
        content,
        parent_id: replyTo || null,
      });
      setText("");
      setReplyTo("");
      await reload();
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Không thể gửi phản hồi",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return {
    comments,
    text,
    setText,
    replyTo,
    setReplyTo,
    loading,
    submitting,
    error,
    reload,
    submit,
  };
}
