"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL } from "@/shared/services/api-client";
import {
  createAiSessionAPI,
  getAiSessionsAPI,
  queryRagAPI,
  translateTextAPI,
} from "@/features/agentic_ai/services/interaction.service";
import {
  getArchiveContentAPI,
  getArchiveTreeAPI,
  getSystemFilePreviewUrlAPI,
} from "@/features/cloud/services/storage.service";
import {
  getBookmarksAPI,
  toggleBookmarkAPI,
} from "@/features/engagement/services/bookmark.service";
import {
  getDocumentDecryptionKeyAPI,
  getDocumentWithPasswordAPI,
} from "@/features/content/services/document.service";
import {
  createHighlightAPI,
  deleteHighlightAPI,
  getHighlightsAPI,
} from "@/features/engagement/services/highlight.service";

type Message = { id: string; role: "user" | "assistant"; content: string };
async function decrypt(document: any, id: string) {
  if (!Array.isArray(document.content_fragments))
    return document.content || document.description || "";
  const rawKey = atob(
    await getDocumentDecryptionKeyAPI(document._id ?? document.id ?? id),
  );
  const key = await crypto.subtle.importKey(
    "raw",
    Uint8Array.from(rawKey, (value) => value.charCodeAt(0)),
    { name: "AES-GCM" },
    false,
    ["decrypt"],
  );
  const parts: string[] = [];
  for (const fragment of document.content_fragments) {
    const raw = atob(fragment);
    const bytes = Uint8Array.from(raw, (value) => value.charCodeAt(0));
    const output = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: bytes.slice(0, 12) },
      key,
      bytes.slice(12),
    );
    parts.push(new TextDecoder().decode(output));
  }
  return parts.join("");
}

export function useDocumentReader(
  id: string,
  rawUrl: string | null,
  rawName: string | null,
  initialPassword: string | null,
  shareToken: string | null,
) {
  const [document, setDocument] = useState<any>(null);
  const [content, setContent] = useState("");
  const [locked, setLocked] = useState(false);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [archive, setArchive] = useState<any[]>([]);
  const [archiveFile, setArchiveFile] = useState<any>(null);
  const [bookmarked, setBookmarked] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  const load = useCallback(
    async (password?: string) => {
      setLoading(true);
      setError("");
      try {
        if (rawUrl) {
          setDocument({
            _id: id,
            title: rawName || "Tài liệu",
            content_format: "raw",
            file_url: `${String(API_URL || "").replace("/api/v1", "")}/luu-tru/${rawUrl.replace(/^\/+/, "")}`,
          });
          setLocked(false);
          return;
        }
        const response = await getDocumentWithPasswordAPI(
          id,
          password || initialPassword || undefined,
          shareToken || undefined,
        );
        if (response.status === 401) {
          setError("Đăng nhập để mở tài liệu");
          return;
        }
        if (response.status === 403) {
          setLocked(true);
          return;
        }
        const row = response.data;
        const storedPath = String(row.file_url || row.pdf_url || "");
        if (storedPath && !/^https?:\/\//i.test(storedPath)) {
          row.file_url = await getSystemFilePreviewUrlAPI(storedPath);
        }
        setDocument(row);
        setLocked(false);
        try {
          setContent(await decrypt(row, id));
        } catch {
          setContent(row.description || "Không thể giải mã nội dung");
        }
        if (row.content_format === "zip" && row.file_url)
          setArchive(await getArchiveTreeAPI(row.file_url));
        const [highlightResponse, bookmarkResponse, sessionResponse] =
          await Promise.all([
            getHighlightsAPI(id).catch(() => []),
            getBookmarksAPI().catch(() => ({ data: [] })),
            getAiSessionsAPI(id).catch(() => ({ data: [] })),
          ]);
        setHighlights(highlightResponse.data ?? highlightResponse ?? []);
        setSessions(sessionResponse.data ?? sessionResponse ?? []);
        const bookmarks = bookmarkResponse.data ?? bookmarkResponse ?? [];
        setBookmarked(
          bookmarks.some((item: any) => (item._id ?? item.id) === id),
        );
      } catch (cause) {
        setError(
          cause instanceof Error ? cause.message : "Không thể tải tài liệu",
        );
      } finally {
        setLoading(false);
      }
    },
    [id, rawUrl, rawName, initialPassword, shareToken],
  );
  useEffect(() => void load(), [load]);
  useEffect(() => {
    if (!document?.drm_settings?.disable_copy) return;
    const prevent = (event: Event) => event.preventDefault();
    window.addEventListener("copy", prevent);
    window.addEventListener("contextmenu", prevent);
    return () => {
      window.removeEventListener("copy", prevent);
      window.removeEventListener("contextmenu", prevent);
    };
  }, [document]);
  useEffect(() => {
    if (!document?.drm_settings?.disable_print) return;
    const preventPrint = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "p")
        event.preventDefault();
    };
    globalThis.document.documentElement.classList.add("drm-print-disabled");
    window.addEventListener("keydown", preventPrint);
    return () => {
      globalThis.document.documentElement.classList.remove("drm-print-disabled");
      window.removeEventListener("keydown", preventPrint);
    };
  }, [document]);

  const ask = async (question: string, thinking: boolean) => {
    if (!question.trim()) return;
    setProcessing("ask");
    setError("");
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question.trim(),
    };
    setMessages((rows) => [...rows, userMessage]);
    try {
      let activeSession = sessionId;
      if (!activeSession) {
        const created = await createAiSessionAPI(id, question.trim());
        activeSession = created.data?._id ?? created._id;
        setSessionId(activeSession);
      }
      const response = await queryRagAPI(
        id,
        question.trim(),
        thinking,
        activeSession || undefined,
      );
      setMessages((rows) => [
        ...rows,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            response.data?.answer ?? response.answer ?? "Không có phản hồi",
        },
      ]);
      const sessionResponse = await getAiSessionsAPI(id);
      setSessions(sessionResponse.data ?? sessionResponse ?? []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể hỏi AI");
    } finally {
      setProcessing(null);
    }
  };
  const highlight = async (text: string) => {
    setProcessing("highlight");
    setError("");
    try {
      await createHighlightAPI(id, text);
      const response = await getHighlightsAPI(id);
      setHighlights(response.data ?? response ?? []);
      setNotice("Đã lưu đoạn nổi bật");
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể lưu đoạn nổi bật",
      );
      return false;
    } finally {
      setProcessing(null);
    }
  };
  const removeHighlight = async (highlightId: string) => {
    setProcessing("highlight");
    try {
      await deleteHighlightAPI(highlightId);
      setHighlights((rows) =>
        rows.filter((item) => (item._id ?? item.id) !== highlightId),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể xóa đoạn nổi bật",
      );
    } finally {
      setProcessing(null);
    }
  };
  const bookmark = async () => {
    setProcessing("bookmark");
    try {
      await toggleBookmarkAPI(id);
      setBookmarked((value) => !value);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể cập nhật thư viện",
      );
    } finally {
      setProcessing(null);
    }
  };
  const translate = async (text: string) => {
    setProcessing("translate");
    try {
      const response = await translateTextAPI(text, "vi");
      setNotice(
        response.data?.translated_text ??
          response.translated_text ??
          "Không có bản dịch",
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể dịch đoạn văn",
      );
    } finally {
      setProcessing(null);
    }
  };
  const openArchiveFile = async (item: any) => {
    if (item.is_dir || !document?.file_url) return;
    setProcessing("archive");
    try {
      const response = await getArchiveContentAPI(document.file_url, item.path);
      setArchiveFile({ ...response, name: item.name });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không thể mở tệp nén");
    } finally {
      setProcessing(null);
    }
  };
  return {
    document,
    content,
    locked,
    highlights,
    sessions,
    messages,
    archive,
    archiveFile,
    bookmarked,
    loading,
    processing,
    error,
    notice,
    clearNotice: () => setNotice(""),
    load,
    ask,
    highlight,
    removeHighlight,
    bookmark,
    translate,
    openArchiveFile,
  };
}
