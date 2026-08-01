"use client";

import { useToast } from "@/shared/contexts/ToastContext";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { API_URL } from "@/features/authentication/services/session.service";
import {
  queryRagAPI,
  translateTextAPI,
  getAiSessionsAPI,
  createAiSessionAPI,
} from "@/features/agentic_ai/services/interaction.service";
import { getDocumentWithPasswordAPI, getDocumentDecryptionKeyAPI } from "@/features/content/services/document.service";
import { getArchiveTreeAPI, getArchiveContentAPI } from "@/features/cloud/services/storage.service";
import {
  createHighlightAPI,
  getHighlightsAPI,
  deleteHighlightAPI,
} from "@/features/content/services/highlight.service";
import {
  toggleBookmarkAPI,
  getBookmarksAPI,
} from "@/features/content/services/bookmark.service";
import {
  Lock,
  AlertTriangle,
  Send,
  ArrowLeft,
  Loader2,
  User,
  Bot,
  Highlighter,
  Bookmark,
  Zap,
  Trash2,
  BookmarkCheck,
  ZoomIn,
  ZoomOut,
  Columns,
  Square,
  Languages,
  BookOpen,
  History,
  Maximize2,
  Minimize2,
  Paperclip,
  Edit2,
  X,
  FileText,
  Image as ImageIcon,
  Folder,
} from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";
import EmptyState from "@/shared/components/common/EmptyState";

export default function DocumentViewer() {
  const { showToast } = useToast();
  const { id } = useParams() as { id: string };
  const searchParams = useSearchParams();
  const rawUrl = searchParams?.get("url");
  const rawName = searchParams?.get("name");
  const router = useRouter();
  const [document, setDocument] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [password, setPassword] = useState("");
  const [isLocked, setIsLocked] = useState(false);
  const [visible, setVisible] = useState(false);
  const [decryptedContent, setDecryptedContent] = useState<string>("");

  const [messages, setMessages] = useState<any[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<
    "chat" | "highlights" | "thumbnails" | "history" | "zip"
  >("chat");
  const [readingMode, setReadingMode] = useState<"single" | "double">("single");
  const [zoom, setZoom] = useState(100);
  const changeZoom = (delta: number) =>
    setZoom((prev) => Math.max(50, Math.min(200, prev + delta)));
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = 1;
  const [isExpanded, setIsExpanded] = useState(false);
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);

  const [zipTree, setZipTree] = useState<any[]>([]);
  const [selectedZipFile, setSelectedZipFile] = useState<{
    name: string;
    content: string;
    type: string;
  } | null>(null);
  const [zipLoading, setZipLoading] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [selection, setSelection] = useState<{
    text: string;
    x: number;
    y: number;
  } | null>(null);
  const [translating, setTranslating] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [showAttachments, setShowAttachments] = useState(false);

  const fetchHighlights = useCallback(async () => {
    try {
      const res = await getHighlightsAPI(id);
      setHighlights(Array.isArray(res) ? res : res.data || []);
    } catch {
      showToast("Không thể đồng bộ dữ liệu nêu bật tài liệu", "error");
    }
  }, [id, showToast]);

  const checkBookmarkStatus = useCallback(async () => {
    try {
      const bookmarks = await getBookmarksAPI();
      if (bookmarks?.data)
        setIsBookmarked(
          bookmarks.data.some((b: any) => (b.id || b._id) === id),
        );
    } catch {}
  }, [id]);

  const fetchDocument = useCallback(
    async (pwd?: string) => {
      setLoading(true);
      if (rawUrl) {
        setDocument({
          _id: id,
          title: rawName || "Tài liệu",
          content_format: "raw",
          file_url: `${(API_URL || "").replace("/api/v1", "")}/luu-tru/${rawUrl}`,
        });
        setLoading(false);
        return;
      }
      try {
        const result = await getDocumentWithPasswordAPI(id, pwd);
        if (result.status === 401) {
          router.push("/dang-nhap");
          return;
        }
        if (result.status === 403) {
          setIsLocked(true);
          setLoading(false);
          return;
        }
        if (result.data) {
          const data = result.data;
          setDocument(data);
          setIsLocked(false);
          const bookmarks = await getBookmarksAPI();
          if (bookmarks?.data)
            setIsBookmarked(
              bookmarks.data.some(
                (b: any) =>
                  (b.id || b._id) === (data.id || data._id || id),
              ),
            );
          if (data.content_format === "zip" && data.file_url) {
            setSidebarTab("zip");
            getArchiveTreeAPI(data.file_url)
              .then(setZipTree)
              .catch(() => showToast("Không thể đọc cấu trúc tệp nén", "error"));
          }
        } else
          setError("Quyền truy cập của bạn bị giới hạn đối với tài liệu này");
      } catch {
        setError("Mất kết nối đến máy chủ hệ thống");
      } finally {
        setLoading(false);
      }
    },
    [id, rawName, rawUrl, router, showToast],
  );

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getAiSessionsAPI(id);
      setSessions(data.data || data || []);
    } catch {
      showToast("Không thể đồng bộ dữ liệu lịch sử hội thoại", "error");
    }
  }, [id, showToast]);

  useEffect(() => {
    fetchDocument();
    fetchHighlights();
    checkBookmarkStatus();
    fetchSessions();
  }, [fetchDocument, fetchHighlights, checkBookmarkStatus, fetchSessions]);

  useEffect(() => {
    if (!document?.drm_settings?.disable_copy) return;
    const prevent = (e: Event) => e.preventDefault();
    window.addEventListener("contextmenu", prevent);
    window.addEventListener("copy", prevent);
    window.addEventListener("selectstart", prevent);
    return () => {
      window.removeEventListener("contextmenu", prevent);
      window.removeEventListener("copy", prevent);
      window.removeEventListener("selectstart", prevent);
    };
  }, [document]);

  useEffect(() => {
    if (!loading) requestAnimationFrame(() => setVisible(true));
  }, [loading]);

  useEffect(() => {
    if (!document) return;
    if (
      document.content_fragments &&
      Array.isArray(document.content_fragments)
    ) {
      const decrypt = async () => {
        try {
          const keyRaw = atob(await getDocumentDecryptionKeyAPI(document._id || document.id || id));
          const keyBytes = new Uint8Array(keyRaw.length);
          for (let i = 0; i < keyRaw.length; i++)
            keyBytes[i] = keyRaw.charCodeAt(i);
          const cryptoKey = await window.crypto.subtle.importKey(
            "raw",
            keyBytes,
            { name: "AES-GCM" },
            false,
            ["decrypt"],
          );
          let fullText = "";
          for (const frag of document.content_fragments) {
            const fragRaw = atob(frag);
            const fragBytes = new Uint8Array(fragRaw.length);
            for (let i = 0; i < fragRaw.length; i++)
              fragBytes[i] = fragRaw.charCodeAt(i);
            fullText += new TextDecoder().decode(
              await window.crypto.subtle.decrypt(
                { name: "AES-GCM", iv: fragBytes.slice(0, 12) },
                cryptoKey,
                fragBytes.slice(12),
              ),
            );
          }
          setDecryptedContent(fullText);
        } catch {
          setDecryptedContent(
            "Lỗi giải mã hoặc chứng thực bảo mật không hoàn tất",
          );
        }
      };
      decrypt();
    } else
      setDecryptedContent(
        document.content ||
          document.description ||
          "Không có nội dung hiển thị",
      );
  }, [document, id]);

  useEffect(() => {
    if (chatEndRef.current)
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAskAI = async (retryText?: string) => {
    const textToSubmit = retryText || question.trim();
    if (!textToSubmit) return;
    setAsking(true);
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const data = await createAiSessionAPI(id, textToSubmit);
        sessionId = data.data?._id || data._id;
        setCurrentSessionId(sessionId);
        fetchSessions();
      } catch {
        showToast("Không thể tạo phiên hội thoại mới", "error");
        setAsking(false);
        return;
      }
    }
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: textToSubmit },
    ]);
    setQuestion("");
    try {
      const res: any = await Promise.race([
        queryRagAPI(id, textToSubmit, thinking, sessionId || undefined),
        new Promise((_, r) =>
          setTimeout(() => r(new Error("AI_TIMEOUT")), 20000),
        ),
      ]);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            res.data?.answer || res.answer || "Không thể tải phản hồi",
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            e.message === "AI_TIMEOUT"
              ? "Phản hồi chậm hơn dự kiến, vui lòng thử lại."
              : `Lỗi: ${e.message || "Không thể kết nối"}`,
        },
      ]);
    } finally {
      setAsking(false);
    }
  };

  const handleEditAndResend = (msgId: string, newText: string) => {
    setMessages((prev) => prev.filter((m) => parseInt(m.id) < parseInt(msgId)));
    handleAskAI(newText);
    setEditingMessageId(null);
  };

  const handleTextSelection = () => {
    if (document?.is_protected) return;
    const sel = window.getSelection();
    if (sel && sel.toString().trim().length > 0) {
      const rect = sel.getRangeAt(0).getBoundingClientRect();
      setSelection({
        text: sel.toString(),
        x: rect.left + rect.width / 2,
        y: rect.top + window.scrollY - 50,
      });
    } else setSelection(null);
  };

  const handleTranslate = async () => {
    if (!selection) return;
    setTranslating(true);
    try {
      const res = await translateTextAPI(selection.text, "vi");
      showToast(res.data?.translated_text || res.translated_text, "success");
      setSelection(null);
    } catch {
      showToast("Lỗi xử lý dịch thuật văn bản", "error");
    } finally {
      setTranslating(false);
    }
  };

  const saveHighlight = async () => {
    if (!selection) return;
    try {
      await createHighlightAPI(id, selection.text, "hsl(var(--surface-quiet))");
      fetchHighlights();
      setSelection(null);
      window.getSelection()?.removeAllRanges();
      showToast("Lưu dữ liệu nêu bật hoàn tất", "success");
    } catch {
      showToast("Lỗi lưu dữ liệu nêu bật", "error");
    }
  };

  const deleteHighlightItem = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      setHighlights((prev) =>
        prev.filter((h) => (h.id || h._id) !== highlightId),
      );
      showToast("Xóa dữ liệu nêu bật hoàn tất", "success");
    } catch {
      showToast("Lỗi xóa dữ liệu nêu bật", "error");
    }
  };

  const toggleBookmark = async () => {
    try {
      await toggleBookmarkAPI(id);
      setIsBookmarked(!isBookmarked);
      showToast(
        isBookmarked ? "Gỡ đánh dấu trang hoàn tất" : "Thêm đánh dấu trang hoàn tất",
        "success",
      );
    } catch {
      showToast("Không thể cập nhật trạng thái dấu trang", "error");
    }
  };

  if (loading) return <PageLoader />;

  const CanvasRenderer = ({ text }: { text: string }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (!canvasRef.current || !containerRef.current || !text) return;
      const ctx = canvasRef.current.getContext("2d");
      if (!ctx) return;
      const dpr = window.devicePixelRatio || 1;
      const width = containerRef.current.clientWidth;
      const fontSize = 16,
        lineHeight = 1.6,
        padding = 0;
      let totalHeight = padding * 2;
      ctx.font = `400 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
      const paragraphs = text.split("\n");
      const wrapText = (t: string, maxW: number) => {
        const words = t.split(" "),
          lines = [];
        let current = words[0];
        for (let i = 1; i < words.length; i++) {
          if (ctx.measureText(current + " " + words[i]).width < maxW)
            current += " " + words[i];
          else {
            lines.push(current);
            current = words[i];
          }
        }
        lines.push(current);
        return lines;
      };
      paragraphs.forEach((p) => {
        if (!p.trim()) {
          totalHeight += fontSize * lineHeight;
          return;
        }
        totalHeight +=
          wrapText(p, width - padding * 2).length * fontSize * lineHeight +
          fontSize;
      });
      canvasRef.current.width = width * dpr;
      canvasRef.current.height = totalHeight * dpr;
      canvasRef.current.style.width = `${width}px`;
      canvasRef.current.style.height = `${totalHeight}px`;
      ctx.scale(dpr, dpr);
      ctx.fillStyle = "hsl(var(--ink))";
      ctx.textBaseline = "top";
      ctx.font = `400 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
      let y = padding;
      paragraphs.forEach((p) => {
        if (!p.trim()) {
          y += fontSize * lineHeight;
          return;
        }
        wrapText(p, width - padding * 2).forEach((line) => {
          ctx.fillText(line, padding, y);
          y += fontSize * lineHeight;
        });
        y += fontSize;
      });
    }, [text]);
    return (
      <div ref={containerRef} className="w-full relative select-none">
        <canvas ref={canvasRef} className="block w-full select-none" />
        <div
          className="absolute inset-0 z-10"
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    );
  };

  const getPageContent = () => {
    if (document?.content_format === "zip") {
      return (
        <div className="w-full h-full flex flex-col bg-surface-quiet border-border rounded-panel overflow-hidden">
          <div className="h-14  bg-surface-quiet flex items-center px-6 shrink-0">
            <FileText className="w-4 h-4 mr-3 text-ink-muted" />
            <span className="text-[13px] font-medium text-ink">
              {selectedZipFile
                ? selectedZipFile.name
                : "Trình duyệt mã nguồn ZIP"}
            </span>
          </div>
          <div className="flex-1 overflow-auto p-6 bg-white">
            {zipLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-brand" />
              </div>
            ) : selectedZipFile ? (
              selectedZipFile.type === "text" ? (
                <pre className="text-[13px] font-mono text-ink whitespace-pre-wrap leading-relaxed bg-surface-quiet p-6 rounded-panel ">
                  {selectedZipFile.content}
                </pre>
              ) : (
                <div className="flex h-full flex-col items-center justify-center text-ink-muted">
                  <AlertTriangle className="w-12 h-12 mb-4 text-ink-faint" />
                  <p className="text-[13px]">
                    Định dạng không được hỗ trợ hiển thị
                  </p>
                </div>
              )
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-ink-muted">
                <Folder className="w-12 h-12 mb-4 text-ink-faint" />
                <p className="text-[13px]">Chọn tệp để xem mã nguồn</p>
              </div>
            )}
          </div>
        </div>
      );
    }
    if (document?.content_format === "raw") {
      return (
        <div className="w-full h-full flex items-center justify-center bg-surface-quiet rounded-panel overflow-hidden">
          <iframe
            src={document.file_url}
            className="w-full h-full border-none bg-white"
            title={document.title}
          />
        </div>
      );
    }
    if (readingMode === "double")
      return (
        <div
          className="prose max-w-none text-ink leading-relaxed text-[15px] whitespace-pre-wrap"
          style={{ columnCount: 2, columnGap: "4rem" }}
        >
          <CanvasRenderer text={decryptedContent} />
        </div>
      );
    return (
      <div className="prose max-w-none text-ink leading-relaxed text-[15px] whitespace-pre-wrap">
        <CanvasRenderer text={decryptedContent} />
      </div>
    );
  };

  if (isLocked)
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-quiet font-sans px-6">
        <div className="bg-surface-quiet p-10 w-full max-w-[400px] border-border flex flex-col items-center text-center rounded-panel">
          <div className="w-20 h-20 bg-surface-quiet flex items-center justify-center mb-6 rounded-full">
            <Lock className="w-8 h-8 text-brand" />
          </div>
          <p className="text-[13px] font-medium text-ink-muted mb-2">
            Thực thể bảo mật
          </p>
          <p className="text-[15px] text-ink-muted mb-8">
            Nhập mã định danh để tiếp cận dữ liệu
          </p>
          <div className="w-full space-y-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
              placeholder=""
              className="w-full h-[52px] bg-surface-quiet border border-transparent px-4 text-center text-[15px] focus:outline-none focus:border-brand focus:bg-white rounded-control transition-all"
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-[52px] bg-brand text-white text-[15px] font-medium rounded-full hover:bg-brand transition-colors"
            >
              Xác thực quyền truy cập
            </button>
          </div>
        </div>
      </div>
    );

  if (error)
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-surface-quiet font-sans px-6">
        <AlertTriangle className="w-16 h-16 text-danger mb-6" />
        <p className="text-[15px] text-ink mb-8">{error}</p>
        <button
          onClick={() => router.back()}
          className="h-[44px] px-8 bg-brand text-white text-[15px] font-medium rounded-full hover:bg-brand transition-colors"
        >
          Quay lại
        </button>
      </div>
    );

  return (
    <div
      className={`flex h-[calc(100dvh-60px)] bg-surface-quiet overflow-hidden font-sans ${document?.is_protected ? "select-none" : ""}`}
      onMouseUp={handleTextSelection}
    >
      <div className="hidden w-[72px] shrink-0 flex-col items-center gap-5 border-r border-border bg-surface py-5 md:flex">
        <button
          onClick={() => setSidebarTab("chat")}
          className={`p-3 rounded-xl transition-colors ${sidebarTab === "chat" ? "bg-brand text-white " : "text-ink-muted hover:text-ink hover:bg-surface-quiet"}`}
        >
          <Bot className="w-6 h-6" />
        </button>
        <button
          onClick={() => setSidebarTab("highlights")}
          className={`p-3 rounded-xl transition-colors ${sidebarTab === "highlights" ? "bg-brand text-white " : "text-ink-muted hover:text-ink hover:bg-surface-quiet"}`}
        >
          <Highlighter className="w-6 h-6" />
        </button>
        <button
          onClick={() => setSidebarTab("thumbnails")}
          className={`p-3 rounded-xl transition-colors ${sidebarTab === "thumbnails" ? "bg-brand text-white " : "text-ink-muted hover:text-ink hover:bg-surface-quiet"}`}
        >
          <BookOpen className="w-6 h-6" />
        </button>
        <button
          onClick={() => setSidebarTab("history")}
          className={`p-3 rounded-xl transition-colors ${sidebarTab === "history" ? "bg-brand text-white " : "text-ink-muted hover:text-ink hover:bg-surface-quiet"}`}
        >
          <History className="w-6 h-6" />
        </button>
        {document?.content_format === "zip" && (
          <button
            onClick={() => setSidebarTab("zip")}
            className={`p-3 rounded-xl transition-colors ${sidebarTab === "zip" ? "bg-brand text-white " : "text-ink-muted hover:text-ink hover:bg-surface-quiet"}`}
          >
            <Folder className="w-6 h-6" />
          </button>
        )}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-[60px] flex shrink-0 items-center justify-between gap-2 border-b border-border bg-surface/90 px-3 backdrop-blur-md md:px-6">
          <div className="flex items-center gap-4 flex-1">
            <button
              onClick={() => router.back()}
              aria-label="Quay lại"
              className="p-2 text-ink-muted rounded-full hover:bg-surface-quiet hover:text-ink transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-[15px] font-semibold text-ink truncate max-w-xs md:max-w-md">
              {document?.title}
            </h1>
          </div>
          <div className="hidden flex-1 justify-center text-[13px] font-medium text-ink-muted sm:flex">
            Trang {currentPage} / 1 (100%)
          </div>
          <div className="flex flex-1 items-center justify-end gap-2 md:gap-5">
            <div className="hidden items-center gap-2 sm:flex">
              <button
                onClick={() => changeZoom(-10)}
                className="p-2 text-ink-muted rounded-full hover:bg-surface-quiet transition-colors"
              >
                <ZoomOut className="w-5 h-5" />
              </button>
              <span className="text-[13px] font-medium text-ink min-w-[3rem] text-center">
                {zoom}%
              </span>
              <button
                onClick={() => changeZoom(10)}
                className="p-2 text-ink-muted rounded-full hover:bg-surface-quiet transition-colors"
              >
                <ZoomIn className="w-5 h-5" />
              </button>
            </div>
            <div className="hidden h-6 w-px bg-border md:block" />
            <div className="hidden items-center gap-1 rounded-control bg-surface-quiet p-1 md:flex">
              <button
                onClick={() => setReadingMode("single")}
                className={`p-1.5 rounded-full transition-colors ${readingMode === "single" ? "text-ink bg-white" : "text-ink-muted hover:text-ink"}`}
              >
                <Square className="w-4 h-4" />
              </button>
              <button
                onClick={() => setReadingMode("double")}
                className={`p-1.5 rounded-full transition-colors ${readingMode === "double" ? "text-ink bg-white" : "text-ink-muted hover:text-ink"}`}
              >
                <Columns className="w-4 h-4" />
              </button>
            </div>
            <div className="hidden h-6 w-px bg-border md:block" />
            <button
              onClick={toggleBookmark}
              className={`p-2 rounded-full transition-colors ${isBookmarked ? "text-brand" : "text-ink-muted hover:bg-surface-quiet hover:text-ink"}`}
            >
              {isBookmarked ? (
                <BookmarkCheck className="w-5 h-5" />
              ) : (
                <Bookmark className="w-5 h-5" />
              )}
            </button>
            <button
              type="button"
              onClick={() => setMobilePanelOpen(true)}
              className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted hover:bg-surface-quiet lg:hidden"
              aria-label="Mở công cụ đọc"
            >
              <Bot className="h-5 w-5" />
            </button>
          </div>
        </header>

        <main className="relative flex flex-1 justify-center overflow-auto bg-surface-quiet p-3 custom-scrollbar md:p-8">
          <div
            className={`mx-auto border border-border bg-surface ${document?.content_format === "zip" ? "p-0 h-full max-w-full rounded-panel" : "p-5 md:p-16 min-h-full origin-top rounded-panel"} transition-transform duration-300 ${readingMode === "double" && document?.content_format !== "zip" ? "w-full max-w-5xl" : document?.content_format !== "zip" ? "w-full max-w-3xl" : "w-full h-full"}`}
            style={{
              transform:
                document?.content_format === "zip"
                  ? "none"
                  : `scale(${zoom / 100})`,
            }}
          >
            {getPageContent()}
          </div>
          {selection && (
            <div
              className="fixed z-50 flex gap-2 bg-surface-quiet/90 backdrop-blur-md p-2 border-border rounded-panel transition-all"
              style={{
                left: selection.x,
                top: selection.y,
                transform: "translateX(-50%)",
              }}
            >
              <button
                onClick={saveHighlight}
                className="p-2 text-ink-muted hover:text-ink hover:bg-surface-quiet rounded-full transition-colors"
              >
                <Highlighter className="w-5 h-5" />
              </button>
              <button
                onClick={handleTranslate}
                disabled={translating}
                className="p-2 text-ink-muted hover:text-ink hover:bg-surface-quiet rounded-full transition-colors"
              >
                {translating ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Languages className="w-5 h-5" />
                )}
              </button>
              <button className="p-2 text-ink-muted hover:text-ink hover:bg-surface-quiet rounded-full transition-colors">
                <Zap className="w-5 h-5" />
              </button>
            </div>
          )}
        </main>
      </div>

      {mobilePanelOpen && <button type="button" className="fixed inset-0 z-40 bg-ink/30 lg:hidden" onClick={() => setMobilePanelOpen(false)} aria-label="Đóng công cụ đọc" />}
      <aside
        className={`${mobilePanelOpen ? "flex" : "hidden"} fixed inset-y-[60px] right-0 z-50 w-[min(88vw,360px)] flex-col border-l border-border bg-surface shadow-xl lg:relative lg:inset-auto lg:flex lg:shrink-0 lg:shadow-none ${isExpanded ? "lg:w-[480px]" : "lg:w-[360px]"}`}
      >
        <div className="h-[60px]  flex items-center px-6 justify-between shrink-0">
          <span className="text-[15px] font-semibold text-ink">
            {sidebarTab === "chat"
              ? "Cố vấn AI"
              : sidebarTab === "highlights"
                ? "Nêu bật"
                : sidebarTab === "history"
                  ? "Lịch sử"
                  : sidebarTab === "zip"
                    ? "Mã nguồn ZIP"
                    : "Mục lục"}
          </span>
          <button type="button" onClick={() => setMobilePanelOpen(false)} className="flex h-10 w-10 items-center justify-center rounded-control text-ink-muted hover:bg-surface-quiet lg:hidden" aria-label="Đóng công cụ đọc">
            <X className="h-5 w-5" />
          </button>
          {sidebarTab === "chat" && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="hidden p-2 text-ink-muted rounded-control hover:bg-surface-quiet transition-colors lg:block"
            >
              {isExpanded ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </button>
          )}
        </div>

        <div className="grid grid-cols-4 gap-1 border-b border-border px-3 pb-3 md:hidden">
          {[
            { id: "chat", label: "Trò chuyện", icon: Bot },
            { id: "highlights", label: "Nêu bật", icon: Highlighter },
            { id: "thumbnails", label: "Mục lục", icon: BookOpen },
            { id: "history", label: "Lịch sử", icon: History },
          ].map((item) => (
            <button key={item.id} type="button" onClick={() => setSidebarTab(item.id as typeof sidebarTab)} aria-label={item.label} className={`flex h-10 items-center justify-center rounded-control ${sidebarTab === item.id ? "bg-brand-soft text-brand" : "text-ink-muted hover:bg-surface-quiet"}`}>
              <item.icon className="h-4 w-4" />
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
          {sidebarTab === "chat" ? (
            <div className="space-y-6">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} group`}
                >
                  <div
                    className={`w-10 h-10 shrink-0 flex items-center justify-center rounded-full ${msg.role === "user" ? "bg-surface-quiet " : "bg-brand text-white"}`}
                  >
                    {msg.role === "user" ? (
                      <User className="w-5 h-5 text-ink-muted" />
                    ) : (
                      <Bot className="w-5 h-5" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-w-[80%]">
                    <div
                      className={`text-[15px] leading-relaxed p-4 rounded-workspace relative ${msg.role === "user" ? "bg-brand text-white rounded-tr-[4px]" : "bg-surface-quiet text-ink rounded-tl-[4px]"}`}
                    >
                      {msg.content}
                      {msg.role === "user" && !asking && (
                        <button
                          onClick={() => setEditingMessageId(msg.id)}
                          className="absolute -left-12 top-1 opacity-0 group-hover:opacity-100 p-2 text-ink-muted rounded-full hover:bg-border transition-all"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    {editingMessageId === msg.id && (
                      <div className="flex flex-col gap-3 mt-2">
                        <textarea
                          defaultValue={msg.content}
                          className="w-full p-4 text-[15px] border border-brand rounded-panel outline-none"
                          onKeyDown={(e) =>
                            e.key === "Enter" &&
                            !e.shiftKey &&
                            (e.preventDefault(),
                            handleEditAndResend(msg.id, e.currentTarget.value))
                          }
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingMessageId(null)}
                            className="px-4 py-2 text-[13px] font-medium text-ink-muted hover:bg-surface-quiet rounded-full"
                          >
                            Hủy bỏ
                          </button>
                          <button
                            onClick={(e) =>
                              handleEditAndResend(
                                msg.id,
                                (
                                  e.currentTarget
                                    .previousElementSibling as HTMLTextAreaElement
                                ).value,
                              )
                            }
                            className="px-4 py-2 bg-brand text-white text-[13px] font-medium rounded-full"
                          >
                            Cập nhật
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          ) : sidebarTab === "highlights" ? (
            <div className="space-y-4">
              {!highlights.length ? (
                <EmptyState text="Chưa có nêu bật nào" />
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-5  bg-surface-quiet rounded-panel group"
                  >
                    <p className="text-[15px] text-ink mb-4 italic pl-4 border-l-2 border-brand">
                      "{h.text}"
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-[12px] text-ink-muted">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button
                        onClick={() => deleteHighlightItem(h.id || h._id)}
                        className="p-2 text-ink-muted hover:text-danger hover:bg-danger-soft rounded-full"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "history" ? (
            <div className="space-y-4">
              {!sessions.length ? (
                <EmptyState text="Chưa có lịch sử hội thoại" />
              ) : (
                sessions.map((s) => (
                  <div
                    key={s._id}
                    onClick={() => {
                      setCurrentSessionId(s._id);
                      setSidebarTab("chat");
                    }}
                    className={`p-5 border cursor-pointer rounded-panel relative ${currentSessionId === s._id ? "border-brand bg-brand-soft" : "border-border bg-surface-quiet"}`}
                  >
                    <p className="text-[15px] font-medium text-ink pr-8">
                      {s.title}
                    </p>
                    <p className="text-[12px] text-ink-muted mt-2">
                      {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                    </p>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "zip" ? (
            <div className="space-y-1 text-[13px] bg-surface-quiet p-4 rounded-panel min-h-[400px]">
              {zipTree.map((item, i) => (
                <div
                  key={i}
                  onClick={() => {
                    if (!item.is_dir) {
                      setZipLoading(true);
                      getArchiveContentAPI(document?.file_url, item.path)
                        .then((res) =>
                          setSelectedZipFile({
                            name: item.name,
                            content: res.content || "",
                            type: res.type || "text",
                          }),
                        )
                        .catch(() => {
                          showToast("Không thể tải mã nguồn tệp tin ZIP", "error");
                        })
                        .finally(() => setZipLoading(false));
                    }
                  }}
                  className={`flex items-center gap-2 px-3 py-2 cursor-pointer rounded-control ${!item.is_dir && selectedZipFile?.name === item.name ? "bg-brand text-white" : "text-ink hover:bg-border"}`}
                  style={{
                    paddingLeft: `${(item.path.split("/").length - 1) * 16 + 12}px`,
                  }}
                >
                  {item.is_dir ? (
                    <Folder className="w-4 h-4" />
                  ) : (
                    <FileText className="w-4 h-4" />
                  )}{" "}
                  <span className="truncate">{item.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <div
                  key={p}
                  onClick={() => setCurrentPage(p)}
                  className={`aspect-[3/4] border flex flex-col items-center justify-center gap-2 cursor-pointer rounded-panel ${currentPage === p ? "bg-brand text-white" : "bg-surface-quiet border-border text-ink"}`}
                >
                  <span className="text-[20px] font-semibold">{p}</span>
                  <span className="text-[12px]">Trang</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {sidebarTab === "chat" && (
          <div className="p-6 bg-white shrink-0">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  (e.preventDefault(), handleAskAI())
                }
                className="w-full min-h-[120px] p-4 pb-16 text-[15px] bg-surface-quiet border border-transparent focus:bg-white focus:border-brand resize-none rounded-panel text-ink placeholder:text-ink-muted outline-none"
                placeholder=""
                disabled={asking}
              />
              <div className="absolute bottom-4 left-4">
                <button className="w-10 h-10 flex items-center justify-center text-ink-muted bg-white  hover:bg-surface-quiet rounded-full">
                  <Paperclip className="w-5 h-5" />
                </button>
              </div>
              <button
                onClick={() => handleAskAI()}
                disabled={asking || !question.trim()}
                className="absolute bottom-4 right-4 w-10 h-10 bg-brand text-white flex items-center justify-center disabled:opacity-50 rounded-full hover:bg-brand"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
