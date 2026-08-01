"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { toggleBookmarkAPI } from "@/features/content/services/bookmark.service";
import {
  getDocumentBySlugAPI,
  getDocumentDecryptionKeyAPI,
} from "@/features/content/services/document.service";
import { purchaseDocumentAPI } from "@/features/payment/services/monetization.service";
import { submitReportAPI } from "@/features/management/services/user_feedback.service";
import {
  pinDocumentAPI,
  unpinDocumentAPI,
} from "@/features/content/services/reading.service";

async function decryptFragments(document: any) {
  if (!Array.isArray(document.content_fragments))
    return document.content || document.description || "";
  const encodedKey = await getDocumentDecryptionKeyAPI(
    document._id ?? document.id,
  );
  const keyRaw = atob(encodedKey);
  const keyBytes = Uint8Array.from(keyRaw, (character) =>
    character.charCodeAt(0),
  );
  const key = await crypto.subtle.importKey(
    "raw",
    keyBytes,
    { name: "AES-GCM" },
    false,
    ["decrypt"],
  );
  const chunks: string[] = [];
  for (const fragment of document.content_fragments) {
    const raw = atob(fragment);
    const bytes = Uint8Array.from(raw, (character) => character.charCodeAt(0));
    const output = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: bytes.slice(0, 12) },
      key,
      bytes.slice(12),
    );
    chunks.push(new TextDecoder().decode(output));
  }
  return chunks.join("");
}

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
      try {
        setContent(await decryptFragments(row));
      } catch {
        setContent(row.description || "Không thể giải mã nội dung");
      }
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
  const purchase = async () => {
    if (!user) return setError("Đăng nhập để mua tài liệu");
    setProcessing(true);
    setError("");
    try {
      await purchaseDocumentAPI(document._id ?? document.id);
      setDocument((current: any) => ({ ...current, has_purchased: true }));
      setNotice("Đã mua tài liệu");
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể mua tài liệu",
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
  const report = async (reason: string, description: string) => {
    setProcessing(true);
    setError("");
    try {
      await submitReportAPI({
        item_id: document._id ?? document.id,
        item_type: "document",
        reason,
        description,
      });
      setNotice("Đã gửi báo cáo");
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể gửi báo cáo");
      return false;
    } finally {
      setProcessing(false);
    }
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
    purchase,
    pin,
    share,
    report,
  };
}
