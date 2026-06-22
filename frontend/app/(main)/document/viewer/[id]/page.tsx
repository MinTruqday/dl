"use client";

import { useToast } from "@/shared/contexts/ToastContext";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getToken,
  API_URL,
} from "@/features/auth/services/user_authentication.service";
import {
  queryRagAPI,
  translateTextAPI,
} from "@/features/ai/services/agentic_ai.service";
import {
  createHighlightAPI,
  getHighlightsAPI,
  deleteHighlightAPI,
} from "@/features/content/services/text_highlight.service";
import {
  toggleBookmarkAPI,
  getBookmarksAPI,
} from "@/features/content/services/document_bookmark.service";
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

export default function DocumentViewer() {
  const { showToast } = useToast();
  const { id } = useParams() as { id: string };
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
  const [useSmart, setUseSmart] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<
    "chat" | "highlights" | "thumbnails" | "history" | "zip"
  >("chat");
  const [readingMode, setReadingMode] = useState<"single" | "double">("single");
  const [zoom, setZoom] = useState(100);
  const [currentPage, setCurrentPage] = useState(1);
  const [isExpanded, setIsExpanded] = useState(false);

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
    } catch (err: any) {
      showToast("Không thể đồng bộ nêu bật", "error");
    }
  }, [id, showToast]);

  const checkBookmarkStatus = useCallback(async () => {
    try {
      const bookmarks = await getBookmarksAPI();
      if (bookmarks?.data) {
        const docId = id;
        setIsBookmarked(
          bookmarks.data.some((b: any) => (b.id || b._id) === docId),
        );
      }
    } catch (err) {
      console.error(err);
    }
  }, [id]);

  const fetchDocument = useCallback(
    async (pwd?: string) => {
      setLoading(true);
      try {
        const token = getToken();
        if (!token) {
          router.push("/login");
          return;
        }

        let url = `${API_URL}/tai-lieu/${id}`;
        const headers: any = { Authorization: `Bearer ${token}` };
        if (pwd) headers["x-document-password"] = pwd;

        const res = await fetch(url, { headers });

        if (res.status === 401) {
          router.push("/login");
          return;
        }

        if (res.status === 403) {
          setIsLocked(true);
          setLoading(false);
          return;
        }

        if (res.ok) {
          const data = await res.json();
          setDocument(data.data || data);
          setIsLocked(false);

          const bookmarks = await getBookmarksAPI();
          if (bookmarks?.data) {
            const docId = data.data?.id || data.data?._id || id;
            setIsBookmarked(
              bookmarks.data.some((b: any) => (b.id || b._id) === docId),
            );
          }
          if (data.data?.content_format === "zip" && data.data?.file_url) {
            setSidebarTab("zip");
            fetch(
              `${API_URL}/doc-sach/tree-zip?file_url=${encodeURIComponent(data.data.file_url)}`,
            )
              .then((r) => r.json())
              .then((res) => setZipTree(res.data || []))
              .catch(console.error);
          }
        } else {
          setError("Quyền truy cập của bạn bị giới hạn đối với tài liệu này");
        }
      } catch (e) {
        setError("Mất kết nối với hệ thống");
      } finally {
        setLoading(false);
      }
    },
    [id, router],
  );

  const fetchSessions = useCallback(async () => {
    try {
      const token = getToken();
      const res = await fetch(`${API_URL}/lich-su?document_id=${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.data || []);
      }
    } catch (err: any) {
      console.error(err.message || err);
      showToast("Không thể đồng bộ lịch sử", "error");
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
    const preventAction = (e: Event) => e.preventDefault();
    window.addEventListener("contextmenu", preventAction);
    window.addEventListener("copy", preventAction);
    window.addEventListener("selectstart", preventAction);
    return () => {
      window.removeEventListener("contextmenu", preventAction);
      window.removeEventListener("copy", preventAction);
      window.removeEventListener("selectstart", preventAction);
    };
  }, [document]);

  useEffect(() => {
    if (!loading) requestAnimationFrame(() => setVisible(true));
  }, [loading]);

  useEffect(() => {
    if (!document) return;
    if (document.content_fragments && Array.isArray(document.content_fragments)) {
      const decrypt = async () => {
        try {
          const token = getToken();
          const docId = document._id || document.id || id;
          const keyRes = await fetch(`${API_URL}/tai-lieu/${docId}/khoa-giai-ma`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (!keyRes.ok) throw new Error("Key fetch failed");
          const keyData = await keyRes.json();
          const keyB64 = keyData.data.key;

          const keyRaw = atob(keyB64);
          const keyBytes = new Uint8Array(keyRaw.length);
          for (let i = 0; i < keyRaw.length; i++) keyBytes[i] = keyRaw.charCodeAt(i);
          const cryptoKey = await window.crypto.subtle.importKey(
              "raw", keyBytes, { name: "AES-GCM" }, false, ["decrypt"]
          );

          let fullText = "";
          for (const frag of document.content_fragments) {
              const fragRaw = atob(frag);
              const fragBytes = new Uint8Array(fragRaw.length);
              for (let i = 0; i < fragRaw.length; i++) fragBytes[i] = fragRaw.charCodeAt(i);
              
              const iv = fragBytes.slice(0, 12);
              const ct = fragBytes.slice(12);
              
              const decrypted = await window.crypto.subtle.decrypt(
                  { name: "AES-GCM", iv: iv }, cryptoKey, ct
              );
              fullText += new TextDecoder().decode(decrypted);
          }
          setDecryptedContent(fullText);
        } catch (err) {
          console.error("Lỗi giải mã:", err);
          setDecryptedContent("Lỗi giải mã hoặc chứng thực bảo mật không thành công. Hãy thử tải lại trang.");
        }
      };
      decrypt();
    } else {
      setDecryptedContent(document.content || document.description || "Không có nội dung hiển thị");
    }
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
        const token = getToken();
        const res = await fetch(`${API_URL}/lich-su`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ document_id: id, first_query: textToSubmit }),
        });
        if (res.ok) {
          const data = await res.json();
          sessionId = data.data._id;
          setCurrentSessionId(sessionId);
          fetchSessions();
        }
      } catch (err: any) {
        console.error(err.message || err);
        showToast("Không thể khởi tạo phiên làm việc", "error");
        setAsking(false);
        return;
      }
    }

    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      content: textToSubmit,
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("AI_TIMEOUT")), 20000),
    );

    try {
      const apiCall = queryRagAPI(
        id,
        textToSubmit,
        useSmart,
        sessionId || undefined,
      );
      const res: any = await Promise.race([apiCall, timeoutPromise]);

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          res.data?.answer || res.answer || "Không thể trích xuất phản hồi.",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const errorMsg =
        e.message === "AI_TIMEOUT"
          ? "Phản hồi chậm hơn dự kiến, vui lòng thử lại."
          : `Lỗi: ${e.message || "Không thể kết nối"}`;

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: errorMsg,
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
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setSelection({
        text: sel.toString(),
        x: rect.left + rect.width / 2,
        y: rect.top + window.scrollY - 50,
      });
    } else {
      setSelection(null);
    }
  };

  const handleTranslate = async () => {
    if (!selection) return;
    setTranslating(true);
    try {
      const res = await translateTextAPI(selection.text, "vi");
      const translation = res.data?.translated_text || res.translated_text;
      showToast(translation, "success");
      setSelection(null);
    } catch (err) {
      showToast("Không thể dịch thuật", "error");
    } finally {
      setTranslating(false);
    }
  };

  const saveHighlight = async () => {
    if (!selection) return;
    try {
      await createHighlightAPI(id, selection.text, "#e4e4e7");
      fetchHighlights();
      setSelection(null);
      window.getSelection()?.removeAllRanges();
      showToast("Đã lưu nêu bật", "success");
    } catch (e) {
      showToast("Không thể lưu nêu bật", "error");
    }
  };

  const deleteHighlight = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      setHighlights((prev) =>
        prev.filter((h) => (h.id || h._id) !== highlightId),
      );
      showToast("Đã xóa nêu bật", "success");
    } catch (err: any) {
      showToast("Không thể xóa nêu bật", "error");
    }
  };

  const toggleBookmark = async () => {
    try {
      await toggleBookmarkAPI(id);
      setIsBookmarked(!isBookmarked);
      showToast(
        isBookmarked ? "Đã gỡ khỏi dấu trang" : "Đã thêm vào dấu trang",
        "success",
      );
    } catch (err: any) {
      showToast("Cập nhật dấu trang thất bại", "error");
    }
  };

  const changeZoom = (delta: number) => {
    setZoom((prev) => Math.min(Math.max(50, prev + delta), 200));
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-50 font-sans">
        <Loader2 className="w-8 h-8 animate-spin text-black" />
      </div>
    );
  }

  const getPageContent = () => {
    if (document?.content_format === "zip") {
      return (
        <div className="w-full h-full flex flex-col bg-zinc-50 border border-zinc-100 rounded-3xl overflow-hidden shadow-sm">
          <div className="h-14 border-b border-zinc-100 bg-white flex items-center px-6 shrink-0">
            <FileText className="w-4 h-4 mr-3 text-zinc-400" />
            <span className="text-xs font-bold text-zinc-900 uppercase tracking-widest">
              {selectedZipFile
                ? selectedZipFile.name
                : "Trình duyệt mã nguồn ZIP"}
            </span>
          </div>
          <div className="flex-1 overflow-auto p-6 bg-white">
            {zipLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-black" />
              </div>
            ) : selectedZipFile ? (
              selectedZipFile.type === "text" ? (
                <pre className="text-xs font-mono text-zinc-900 whitespace-pre-wrap leading-relaxed bg-zinc-50 p-6 rounded-2xl border border-zinc-100">
                  {selectedZipFile.content}
                </pre>
              ) : (
                <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                  <AlertTriangle className="w-12 h-12 mb-4 text-zinc-200" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">
                    Định dạng nhị phân không được hỗ trợ hiển thị
                  </p>
                </div>
              )
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                <Folder className="w-12 h-12 mb-4 text-zinc-200" />
                <p className="text-[10px] font-bold uppercase tracking-widest">
                  Chọn một tệp từ cây thư mục bên phải để xem mã nguồn
                </p>
              </div>
            )}
          </div>
        </div>
      );
    }

    const CanvasRenderer = ({ text }: { text: string }) => {
      const canvasRef = useRef<HTMLCanvasElement>(null);
      const containerRef = useRef<HTMLDivElement>(null);

      useEffect(() => {
        const canvas = canvasRef.current;
        const container = containerRef.current;
        if (!canvas || !container || !text) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const padding = 0;
        const width = container.clientWidth;
        const fontSize = 14;
        const lineHeight = 1.7;

        const paragraphs = text.split("\n");
        let totalHeight = padding * 2;
        ctx.font = `500 ${fontSize}px Inter, ui-sans-serif, system-ui, sans-serif`;
        
        const wrapText = (text: string, maxWidth: number) => {
            const words = text.split(" ");
            const lines: string[] = [];
            let currentLine = words[0];

            for (let i = 1; i < words.length; i++) {
                const word = words[i];
                const width = ctx.measureText(currentLine + " " + word).width;
                if (width < maxWidth) {
                    currentLine += " " + word;
                } else {
                    lines.push(currentLine);
                    currentLine = word;
                }
            }
            lines.push(currentLine);
            return lines;
        };

        paragraphs.forEach(p => {
            if (!p.trim()) {
                totalHeight += fontSize * lineHeight;
                return;
            }
            const lines = wrapText(p, width - padding * 2);
            totalHeight += lines.length * fontSize * lineHeight + fontSize;
        });

        canvas.width = width * dpr;
        canvas.height = totalHeight * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${totalHeight}px`;

        ctx.scale(dpr, dpr);
        ctx.fillStyle = "#18181b";
        ctx.font = `500 ${fontSize}px Inter, ui-sans-serif, system-ui, sans-serif`;
        ctx.textBaseline = "top";

        let y = padding;
        paragraphs.forEach(p => {
            if (!p.trim()) {
                y += fontSize * lineHeight;
                return;
            }
            const lines = wrapText(p, width - padding * 2);
            lines.forEach(line => {
                ctx.fillText(line, padding, y);
                y += fontSize * lineHeight;
            });
            y += fontSize;
        });
      }, [text, readingMode, zoom]);

      return (
        <div ref={containerRef} className="w-full relative select-none">
          <canvas ref={canvasRef} className="block w-full select-none" />
          <div className="absolute inset-0 z-10" onContextMenu={(e) => e.preventDefault()} />
        </div>
      );
    };

    if (readingMode === "double" && document?.content_format !== "zip") {
      return (
        <div
          className="prose prose-zinc max-w-none text-zinc-900 leading-relaxed text-sm font-medium whitespace-pre-wrap"
          style={{ columnCount: 2, columnGap: "4rem" }}
        >
          <CanvasRenderer text={decryptedContent} />
        </div>
      );
    }

    return (
      <div className="prose prose-zinc max-w-none text-zinc-900 leading-relaxed text-sm font-medium whitespace-pre-wrap">
        <CanvasRenderer text={decryptedContent} />
      </div>
    );
  };

  const totalPages = 1;

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50 p-6 font-sans">
        <div className="bg-white/90 backdrop-blur-md p-10 w-full max-w-md border border-zinc-100 flex flex-col items-center text-center rounded-3xl shadow-xl transition-all duration-500">
          <div className="w-20 h-20 bg-zinc-50 border border-zinc-100 shadow-sm flex items-center justify-center mb-8 rounded-2xl">
            <Lock className="w-8 h-8 text-black" />
          </div>
          <h2 className="text-xl font-bold text-zinc-900 tracking-tight mb-2">
            Thực thể bảo mật
          </h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-8">
            Nhập mã định danh để tiếp cận dữ liệu
          </p>
          <div className="w-full space-y-4">
            <input
              type="password"
              className="w-full h-12 bg-white border border-zinc-200 px-4 text-center text-sm font-medium focus:outline-none focus:border-black rounded-2xl shadow-sm transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
              placeholder="Nhập mã bảo mật"
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-12 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shadow-md"
            >
              Xác thực quyền truy cập
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-50 font-sans">
        <AlertTriangle className="w-16 h-16 text-zinc-300 mb-6" />
        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-8">{error}</p>
        <button
          onClick={() => router.back()}
          className="h-11 px-6 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 shadow-md"
        >
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div
      className={`flex h-screen bg-zinc-50 overflow-hidden font-sans ${document?.is_protected ? "select-none" : ""}`}
      onMouseUp={handleTextSelection}
    >
      <div className="w-16 border-r border-zinc-100 bg-white/90 backdrop-blur-md shadow-sm flex flex-col items-center py-6 gap-6 shrink-0 z-50">
        <button
          onClick={() => setSidebarTab("chat")}
          className={`p-3 rounded-2xl transition-all duration-200 ${sidebarTab === "chat" ? "bg-black text-white shadow-md hover:scale-105" : "text-zinc-400 hover:text-black hover:bg-zinc-50"}`}
        >
          <Bot className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("highlights")}
          className={`p-3 rounded-2xl transition-all duration-200 ${sidebarTab === "highlights" ? "bg-black text-white shadow-md hover:scale-105" : "text-zinc-400 hover:text-black hover:bg-zinc-50"}`}
        >
          <Highlighter className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("thumbnails")}
          className={`p-3 rounded-2xl transition-all duration-200 ${sidebarTab === "thumbnails" ? "bg-black text-white shadow-md hover:scale-105" : "text-zinc-400 hover:text-black hover:bg-zinc-50"}`}
        >
          <BookOpen className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("history")}
          className={`p-3 rounded-2xl transition-all duration-200 ${sidebarTab === "history" ? "bg-black text-white shadow-md hover:scale-105" : "text-zinc-400 hover:text-black hover:bg-zinc-50"}`}
        >
          <History className="w-5 h-5" />
        </button>
        {document?.content_format === "zip" && (
          <button
            onClick={() => setSidebarTab("zip")}
            className={`p-3 rounded-2xl transition-all duration-200 ${sidebarTab === "zip" ? "bg-black text-white shadow-md hover:scale-105" : "text-zinc-400 hover:text-black hover:bg-zinc-50"}`}
          >
            <Folder className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-zinc-100 flex items-center justify-between px-6 bg-white/90 backdrop-blur-md shadow-sm shrink-0 z-40">
          <div className="flex items-center gap-4 flex-1">
            <button
              onClick={() => router.back()}
              className="p-2 text-zinc-400 rounded-xl hover:bg-zinc-50 hover:text-black transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-xs font-bold text-zinc-900 uppercase tracking-widest truncate max-w-xs md:max-w-md">
              {document?.title}
            </h1>
          </div>

          <div className="flex-1 flex justify-center text-[10px] font-bold uppercase tracking-widest text-zinc-400">
            Trang {currentPage} / {totalPages} (
            {((currentPage / totalPages) * 100).toFixed(0)}%)
          </div>

          <div className="flex items-center justify-end gap-6 flex-1">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => changeZoom(-10)}
                className="p-2 text-zinc-400 rounded-xl hover:bg-zinc-50 hover:text-black transition-colors"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-[10px] font-bold text-zinc-900 min-w-[3rem] text-center">
                {zoom}%
              </span>
              <button
                onClick={() => changeZoom(10)}
                className="p-2 text-zinc-400 rounded-xl hover:bg-zinc-50 hover:text-black transition-colors"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>

            <div className="w-[1px] h-4 bg-zinc-200" />

            <div className="flex items-center gap-1 bg-zinc-50 border border-zinc-100 p-0.5 rounded-xl">
              <button
                onClick={() => setReadingMode("single")}
                className={`p-1.5 rounded-lg transition-colors ${readingMode === "single" ? "text-black bg-white shadow-sm border border-zinc-200" : "text-zinc-400 hover:text-black"}`}
              >
                <Square className="w-4 h-4" />
              </button>
              <button
                onClick={() => setReadingMode("double")}
                className={`p-1.5 rounded-lg transition-colors ${readingMode === "double" ? "text-black bg-white shadow-sm border border-zinc-200" : "text-zinc-400 hover:text-black"}`}
              >
                <Columns className="w-4 h-4" />
              </button>
            </div>

            <div className="w-[1px] h-4 bg-zinc-200" />

            <button
              onClick={toggleBookmark}
              className={`p-2 rounded-xl transition-colors ${isBookmarked ? "text-black" : "text-zinc-400 hover:bg-zinc-50 hover:text-black"}`}
            >
              {isBookmarked ? (
                <BookmarkCheck className="w-5 h-5" />
              ) : (
                <Bookmark className="w-5 h-5" />
              )}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-zinc-50 p-6 md:p-8 lg:p-12 relative flex justify-center custom-scrollbar">
          <div
            className={`mx-auto bg-white border border-zinc-100 shadow-sm ${document?.content_format === "zip" ? "p-0 h-full max-w-full rounded-3xl" : "p-12 md:p-24 min-h-full origin-top rounded-3xl"} transition-transform duration-300 ${readingMode === "double" && document?.content_format !== "zip" ? "w-full max-w-6xl" : document?.content_format !== "zip" ? "w-full max-w-3xl" : "w-full h-full"}`}
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
              className="fixed z-50 flex gap-1 bg-white/90 backdrop-blur-md p-1.5 border border-zinc-100 rounded-2xl shadow-lg transition-all"
              style={{
                left: selection.x,
                top: selection.y,
                transform: "translateX(-50%)",
              }}
            >
              <button
                onClick={saveHighlight}
                className="p-2 text-zinc-500 hover:text-black hover:bg-zinc-50 rounded-xl transition-colors"
                title="Lưu nêu bật"
              >
                <Highlighter className="w-4 h-4" />
              </button>
              <button
                onClick={handleTranslate}
                disabled={translating}
                className="p-2 text-zinc-500 hover:text-black hover:bg-zinc-50 rounded-xl transition-colors"
                title="Dịch thuật"
              >
                {translating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Languages className="w-4 h-4" />
                )}
              </button>
              <button
                className="p-2 text-zinc-500 hover:text-black hover:bg-zinc-50 rounded-xl transition-colors"
                title="Giải thích bằng AI"
              >
                <Zap className="w-4 h-4" />
              </button>
            </div>
          )}
        </main>
      </div>

      <div
        className={`${isExpanded ? "w-[500px] md:w-[600px]" : "w-[350px] md:w-[400px]"} border-l border-zinc-100 bg-white/90 backdrop-blur-md shadow-sm flex flex-col shrink-0 z-50 transition-all duration-300`}
      >
        <div className="h-16 border-b border-zinc-100 flex items-center px-6 justify-between bg-white shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold text-zinc-900 uppercase tracking-widest">
              {sidebarTab === "chat"
                ? "Cố vấn AI"
                : sidebarTab === "highlights"
                  ? "Nêu bật"
                  : sidebarTab === "history"
                    ? "Lịch sử"
                    : sidebarTab === "zip"
                      ? "Mã nguồn ZIP"
                      : "Mục lục trang"}
            </span>
            {sidebarTab === "chat" && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 text-zinc-400 rounded-xl hover:bg-zinc-50 hover:text-black transition-colors"
              >
                {isExpanded ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
          {sidebarTab === "chat" && (
            <button
              onClick={() => setUseSmart(!useSmart)}
              className={`px-3 py-1.5 text-[9px] font-bold uppercase tracking-widest border rounded-xl transition-all duration-200 hover:scale-[1.02] ${useSmart ? "bg-black text-white border-black shadow-md" : "bg-zinc-50 text-zinc-500 border-zinc-200"}`}
            >
              {useSmart ? "Chuyên sâu" : "Tiêu chuẩn"}
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-zinc-50/50">
          {sidebarTab === "chat" ? (
            <div className="space-y-6">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} group`}
                >
                  <div
                    className={`w-8 h-8 shrink-0 border flex items-center justify-center rounded-2xl shadow-sm ${msg.role === "user" ? "bg-white border-zinc-200" : "bg-black text-white border-black"}`}
                  >
                    {msg.role === "user" ? (
                      <User className="w-4 h-4 text-zinc-400" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-w-[85%]">
                    <div
                      className={`text-sm leading-relaxed p-4 border rounded-3xl relative shadow-sm ${msg.role === "user" ? "bg-zinc-900 border-zinc-800 text-white font-medium" : "bg-white border-zinc-100 text-zinc-900"}`}
                    >
                      {msg.content}
                      {msg.role === "user" && !asking && (
                        <button
                          onClick={() => setEditingMessageId(msg.id)}
                          className="absolute -left-10 top-1 opacity-0 group-hover:opacity-100 p-2 text-zinc-400 rounded-xl hover:bg-white hover:text-black transition-all"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    {editingMessageId === msg.id && (
                      <div className="flex flex-col gap-3 mt-2">
                        <textarea
                          defaultValue={msg.content}
                          className="w-full p-4 text-sm font-medium border border-zinc-200 focus:outline-none focus:border-black rounded-2xl bg-white text-zinc-900 shadow-sm"
                          onKeyDown={(e: any) =>
                            e.key === "Enter" &&
                            !e.shiftKey &&
                            (e.preventDefault(),
                            handleEditAndResend(msg.id, e.target.value))
                          }
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingMessageId(null)}
                            className="text-[10px] font-bold uppercase tracking-widest px-4 py-2 border border-zinc-200 rounded-xl text-zinc-500 hover:bg-zinc-50 transition-colors"
                          >
                            Hủy bỏ
                          </button>
                          <button
                            onClick={(ev) => {
                              const ta = ev.currentTarget.parentElement
                                ?.previousElementSibling as HTMLTextAreaElement;
                              handleEditAndResend(msg.id, ta.value);
                            }}
                            className="text-[10px] font-bold uppercase tracking-widest px-4 py-2 bg-black text-white rounded-xl shadow-md transition-transform hover:scale-[1.02] hover:-translate-y-0.5"
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
              {!Array.isArray(highlights) || highlights.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-4 bg-white border border-zinc-100 rounded-3xl shadow-sm">
                  <Highlighter className="w-8 h-8 text-zinc-200" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Chưa có nêu bật nào
                  </p>
                </div>
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-5 border border-zinc-100 group rounded-3xl bg-white shadow-sm transition-all hover:border-zinc-200"
                  >
                    <p className="text-sm font-medium text-zinc-900 mb-4 italic border-l-2 border-zinc-300 pl-3">
                      "{h.text}"
                    </p>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button
                        onClick={() => deleteHighlight(h.id || h._id)}
                        className="p-1.5 text-zinc-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
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
              {sessions.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-4 bg-white border border-zinc-100 rounded-3xl shadow-sm">
                  <History className="w-8 h-8 text-zinc-200" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                    Chưa có lịch sử hội thoại
                  </p>
                </div>
              ) : (
                sessions.map((s, i) => (
                  <div
                    key={s._id}
                    onClick={() => {
                      setCurrentSessionId(s._id);
                      setMessages(s.messages || []);
                      setSidebarTab("chat");
                    }}
                    className={`p-5 border cursor-pointer rounded-3xl group relative transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 hover:shadow-md ${currentSessionId === s._id ? "border-black bg-white shadow-sm" : "border-zinc-100 bg-white"}`}
                  >
                    <p className="text-xs font-bold text-zinc-900 truncate pr-8">
                      {s.title}
                    </p>
                    <p className="text-[9px] font-bold uppercase tracking-widest text-zinc-400 mt-2">
                      {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                    </p>
                    <button className="absolute right-4 top-4 opacity-0 group-hover:opacity-100 text-zinc-300 hover:text-red-500 p-1.5 hover:bg-red-50 rounded-lg transition-all">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "zip" ? (
            <div className="space-y-1 overflow-x-auto text-sm bg-white p-4 rounded-3xl border border-zinc-100 shadow-sm min-h-[400px]">
              {zipTree.map((item, i) => (
                <div
                  key={i}
                  onClick={() => {
                    if (!item.is_dir) {
                      setZipLoading(true);
                      fetch(
                        `${API_URL}/doc-sach/content-zip?file_url=${encodeURIComponent(document?.file_url)}&path=${encodeURIComponent(item.path)}`,
                      )
                        .then((r) => r.json())
                        .then((res) => {
                          setSelectedZipFile({
                            name: item.name,
                            content: res.data?.content || "",
                            type: res.data?.type || "text",
                          });
                        })
                        .catch(() => showToast("Không thể mở tệp", "error"))
                        .finally(() => setZipLoading(false));
                    }
                  }}
                  className={`flex items-center gap-2 px-3 py-2 cursor-pointer rounded-xl whitespace-nowrap transition-colors ${!item.is_dir && selectedZipFile?.name === item.name ? "bg-zinc-900 text-white shadow-sm" : "text-zinc-600 hover:bg-zinc-50"}`}
                  style={{
                    paddingLeft: `${(item.path.split("/").length - 1) * 16 + 12}px`,
                  }}
                >
                  {item.is_dir ? (
                    <Folder className={`w-4 h-4 shrink-0 ${!item.is_dir && selectedZipFile?.name === item.name ? "text-zinc-300" : "text-zinc-400"}`} />
                  ) : (
                    <FileText className={`w-4 h-4 shrink-0 ${!item.is_dir && selectedZipFile?.name === item.name ? "text-zinc-300" : "text-zinc-400"}`} />
                  )}
                  <span className={`text-xs ${item.is_dir ? "font-bold" : "font-medium"} truncate`}>{item.name}</span>
                </div>
              ))}
              {zipTree.length === 0 && (
                <div className="py-20 text-center flex flex-col items-center gap-3 text-zinc-400">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">Đang phân tích cấu trúc...</p>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <div
                  key={p}
                  onClick={() => setCurrentPage(p)}
                  className={`aspect-[3/4] border flex flex-col items-center justify-center gap-2 cursor-pointer rounded-3xl transition-all duration-200 hover:scale-[1.02] hover:-translate-y-1 hover:shadow-md ${currentPage === p ? "bg-black text-white border-black shadow-md" : "bg-white border-zinc-100 text-zinc-500 shadow-sm"}`}
                >
                  <span className="text-xl font-bold">{p}</span>
                  <span className="text-[9px] font-bold uppercase tracking-widest">Trang</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {sidebarTab === "chat" && (
          <div className="p-6 border-t border-zinc-100 bg-white relative shrink-0">
            {showAttachments && (
              <div className="absolute bottom-[calc(100%+16px)] left-6 right-6 p-5 bg-white border border-zinc-100 rounded-3xl z-[60] shadow-xl">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-[10px] font-bold text-black uppercase tracking-widest">
                    Đính kèm tài liệu
                  </span>
                  <button
                    onClick={() => setShowAttachments(false)}
                    className="text-zinc-400 hover:text-black transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex items-center justify-center gap-2 p-4 bg-zinc-50 border border-zinc-100 rounded-2xl text-[10px] font-bold uppercase tracking-widest text-zinc-900 transition-all hover:border-black hover:bg-white shadow-sm">
                    <FileText className="w-4 h-4 text-zinc-400" /> Thư viện
                  </button>
                  <button className="flex items-center justify-center gap-2 p-4 bg-zinc-50 border border-zinc-100 rounded-2xl text-[10px] font-bold uppercase tracking-widest text-zinc-900 transition-all hover:border-black hover:bg-white shadow-sm">
                    <ImageIcon className="w-4 h-4 text-zinc-400" /> Hình ảnh
                  </button>
                </div>
              </div>
            )}
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  (e.preventDefault(), handleAskAI())
                }
                className="w-full min-h-[140px] p-5 pb-16 text-sm font-medium border border-zinc-200 focus:outline-none focus:border-black resize-none rounded-3xl placeholder:text-zinc-400 text-zinc-900 bg-zinc-50 focus:bg-white shadow-sm transition-colors"
                placeholder="Hỏi bất cứ điều kiện gì về tài liệu..."
                disabled={asking}
              />
              <div className="absolute bottom-5 left-5 flex items-center gap-3">
                <button
                  onClick={() => setShowAttachments(!showAttachments)}
                  className="w-10 h-10 flex items-center justify-center text-zinc-400 bg-white border border-zinc-200 hover:text-black hover:border-black rounded-2xl shadow-sm transition-all duration-200 hover:scale-[1.02]"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={() => handleAskAI()}
                disabled={asking || !question.trim()}
                className="absolute bottom-5 right-5 w-10 h-10 bg-black text-white flex items-center justify-center disabled:opacity-50 rounded-2xl shadow-md transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5"
              >
                {asking ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
