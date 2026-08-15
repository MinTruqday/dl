"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { toggleBookmarkAPI } from "@/features/engagement/services/bookmark.service";
import { getDocumentBySlugAPI } from "@/features/content/services/document.service";
import {
  pinDocumentAPI,
  unpinDocumentAPI,
} from "@/features/engagement/services/reading.service";

export function useDocumentDetails(slug: string) {
  const { user } = useAuth();
  const [document, setDocument] = useState<any>(null);
  const [content, setContent] = useState("");
  const [bookmarked, setBookmarked] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const reload = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError("");
    try {
      const response = await getDocumentBySlugAPI(slug);
      const row = response.data ?? response;
      setDocument(row);
      setBookmarked(Boolean(row.is_bookmarked));
      setPinned(Boolean(row.is_pinned));
      setContent(row.content || row.description || "");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải tài liệu",
      );
    } finally {
      setLoading(false);
    }
  }, [slug]);
  useEffect(() => void reload(), [reload]);
  const bookmark = async () => {
    if (!user) return setError("Đăng nhập để lưu tài liệu");
    setProcessing(true);
    setError("");
    try {
      await toggleBookmarkAPI(document._id ?? document.id);
      setBookmarked((value) => !value);
      setNotice(bookmarked ? "Đã bỏ lưu tài liệu" : "Đã lưu tài liệu");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể cập nhật thư viện",
      );
    } finally {
      setProcessing(false);
    }
  };
  const pin = async () => {
    if (!user) return setError("Đăng nhập để ghim tài liệu");
    setProcessing(true);
    setError("");
    try {
      if (pinned) await unpinDocumentAPI(document._id ?? document.id);
      else await pinDocumentAPI(document._id ?? document.id);
      setPinned((value) => !value);
      setNotice(pinned ? "Đã bỏ ghim tài liệu" : "Đã ghim tài liệu");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể cập nhật ghim");
    } finally {
      setProcessing(false);
    }
  };
  const share = async () => {
    await navigator.clipboard.writeText(window.location.href);
    setNotice("Đã sao chép liên kết");
  };
  return {
    user,
    document,
    content,
    bookmarked,
    pinned,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    bookmark,
    pin,
    share,
  };
}
