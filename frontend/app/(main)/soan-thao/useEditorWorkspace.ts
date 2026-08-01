"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  exportProtectedDocumentAPI,
  getDocumentDraftAPI,
  getMyDocumentsAPI,
  saveDocumentDraftAPI,
} from "@/features/content/services/document.service";
import { publishDocumentAPI } from "@/features/content/services/publication.service";
import {
  compilePreviewAPI,
  exportToWordAPI,
} from "@/features/compilation/services/editorjs.service";
import {
  compileLatexPreviewAPI,
  exportLatexAPI,
} from "@/features/compilation/services/latex.service";

export type EditorMode = "edit" | "preview" | "source";

type EditorDocument = {
  _id?: string;
  id?: string;
  title?: string;
  content_format?: string;
  status?: string;
};

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Không thể hoàn tất thao tác";
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function useEditorWorkspace() {
  const searchParams = useSearchParams();
  const requestedId = searchParams.get("tai-lieu") || "";
  const [documents, setDocuments] = useState<EditorDocument[]>([]);
  const [documentId, setDocumentId] = useState(requestedId);
  const [content, setContent] = useState("");
  const [mode, setMode] = useState<EditorMode>("edit");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");
  const [status, setStatus] = useState("Sẵn sàng");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const loadedId = useRef("");

  const selectedDocument = useMemo(
    () =>
      documents.find((item) => (item._id || item.id) === documentId) || null,
    [documentId, documents],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await getMyDocumentsAPI();
      const items = ((response?.data || response || []) as EditorDocument[])
        .filter((item) => ["doclib", "doclibx", "json", "latex"].includes(item.content_format || ""))
        .map((item) => ({
          ...item,
          content_format:
            item.content_format === "json"
              ? "doclib"
              : item.content_format === "latex"
                ? "doclibx"
                : item.content_format,
        }));
      setDocuments(items);
      setDocumentId((current) => {
        if (current && items.some((item) => (item._id || item.id) === current))
          return current;
        return requestedId || items[0]?._id || items[0]?.id || "";
      });
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [requestedId]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    if (!documentId) {
      setContent("");
      loadedId.current = "";
      return;
    }
    let active = true;
    setStatus("Đang tải");
    setError("");
    getDocumentDraftAPI(documentId)
      .then((response) => {
        if (!active) return;
        setContent(response?.data?.content || response?.content || "");
        loadedId.current = documentId;
        setStatus("Đã tải");
      })
      .catch((reason) => {
        if (!active) return;
        loadedId.current = "";
        setError(messageOf(reason));
        setStatus("Không thể tải");
      });
    return () => {
      active = false;
    };
  }, [documentId]);

  useEffect(() => {
    if (!documentId || loadedId.current !== documentId) return;
    const timer = window.setTimeout(async () => {
      setStatus("Đang lưu");
      try {
        await saveDocumentDraftAPI(
          documentId,
          content,
          selectedDocument?.content_format || "doclib",
        );
        setStatus("Đã lưu");
      } catch (reason) {
        setError(messageOf(reason));
        setStatus("Chưa lưu");
      }
    }, 1600);
    return () => window.clearTimeout(timer);
  }, [content, documentId, selectedDocument?.content_format]);

  useEffect(() => {
    if (mode !== "preview" || selectedDocument?.content_format !== "doclibx") {
      setPreviewUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return "";
      });
      return;
    }
    let active = true;
    let currentUrl = "";
    setPreviewing(true);
    compileLatexPreviewAPI(content)
      .then((blob) => {
        if (!active) return;
        currentUrl = URL.createObjectURL(blob);
        setPreviewUrl(currentUrl);
      })
      .catch((reason) => active && setError(messageOf(reason)))
      .finally(() => active && setPreviewing(false));
    return () => {
      active = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [content, mode, selectedDocument?.content_format]);

  const save = async () => {
    if (!documentId) return;
    setSaving(true);
    setError("");
    try {
      await saveDocumentDraftAPI(
        documentId,
        content,
        selectedDocument?.content_format || "doclib",
      );
      setStatus("Đã lưu");
      setNotice("Đã lưu bản thảo");
    } catch (reason) {
      setError(messageOf(reason));
      setStatus("Chưa lưu");
    } finally {
      setSaving(false);
    }
  };

  const publish = async () => {
    if (!documentId) return;
    setError("");
    try {
      await publishDocumentAPI(documentId);
      setNotice("Đã gửi xuất bản");
      await reload();
    } catch (reason) {
      setError(messageOf(reason));
    }
  };

  const exportFile = async (format: "pdf" | "docx" | "protected") => {
    if (!documentId || !selectedDocument) return;
    setExporting(true);
    setError("");
    const basename = selectedDocument.title || "tai-lieu";
    try {
      if (format === "protected") {
        const result = await exportProtectedDocumentAPI(documentId);
        const extension = result.contentDisposition?.includes(".pdf")
          ? "pdf"
          : "doclib";
        download(result.blob, `${basename}.${extension}`);
      } else {
        const blob =
          selectedDocument.content_format === "doclibx"
            ? await exportLatexAPI(content, format)
            : format === "docx"
              ? await exportToWordAPI(content)
              : await compilePreviewAPI(content);
        download(blob, `${basename}.${format}`);
      }
      setNotice("Đã tải tệp xuất");
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setExporting(false);
    }
  };

  return {
    documents,
    documentId,
    setDocumentId,
    selectedDocument,
    content,
    setContent,
    mode,
    setMode,
    loading,
    saving,
    exporting,
    previewing,
    previewUrl,
    status,
    error,
    notice,
    clearNotice: () => setNotice(""),
    reload,
    save,
    publish,
    exportFile,
  };
}
