"use client";

import { useToast } from "@/shared/contexts/Toast";
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
      <div className="flex h-screen items-center justify-center bg-white font-sans">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
      </div>
    );
  }

  const getPageContent = () => {
    if (document?.content_format === "zip") {
      return (
        <div className="w-full h-full min-h-[500px] flex flex-col bg-zinc-50 border border-zinc-200">
          <div className="h-12 border-b border-zinc-200 bg-white flex items-center px-4 shrink-0">
            <FileText className="w-4 h-4 mr-2 text-zinc-500" />
            <span className="text-sm font-medium">
              {selectedZipFile
                ? selectedZipFile.name
                : "Trình duyệt mã nguồn ZIP"}
            </span>
          </div>
          <div className="flex-1 overflow-auto p-4 bg-white">
            {zipLoading ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-300" />
              </div>
            ) : selectedZipFile ? (
              selectedZipFile.type === "text" ? (
                <pre className="text-xs font-mono text-black whitespace-pre-wrap leading-relaxed">
                  {selectedZipFile.content}
                </pre>
              ) : (
                <div className="flex h-full flex-col items-center justify-center text-zinc-500">
                  <AlertTriangle className="w-8 h-8 mb-4 opacity-20" />
                  <p className="text-sm">
                    Định dạng nhị phân không được hỗ trợ hiển thị
                  </p>
                </div>
              )
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                <Folder className="w-12 h-12 mb-4 opacity-20" />
                <p className="text-sm">
                  Chọn một tệp từ cây thư mục bên phải để xem mã nguồn
                </p>
              </div>
            )}
          </div>
        </div>
      );
    }

    const content =
      document?.content ||
      document?.description ||
      "Không có nội dung hiển thị";
    if (readingMode === "double" && document?.content_format !== "zip") {
      return (
        <div
          className="prose prose-zinc max-w-none text-black leading-relaxed text-base font-medium whitespace-pre-wrap"
          style={{ columnCount: 2, columnGap: "4rem" }}
        >
          {content}
        </div>
      );
    }

    return (
      <div className="prose prose-zinc max-w-none text-black leading-relaxed text-base font-medium whitespace-pre-wrap">
        {content}
      </div>
    );
  };

  const totalPages = 1;

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50 p-6 font-sans">
        <div className="bg-white p-12 w-full max-w-md border border-zinc-200 flex flex-col items-center text-center rounded-none ">
          <div className="w-16 h-16 bg-black flex items-center justify-center mb-8 rounded-none">
            <Lock className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-medium text-black mb-2">
            Thực thể bảo mật
          </h2>
          <p className="text-sm text-zinc-500 mb-8">
            Nhập mã định danh để tiếp cận dữ liệu bảo mật.
          </p>
          <div className="w-full space-y-4">
            <input
              type="password"
              className="w-full h-12 bg-white border border-zinc-200 px-4 text-center text-sm focus:outline-none focus:border-black rounded-none "
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
              placeholder="Nhập mã bảo mật"
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-12 bg-black text-white text-sm font-medium rounded-none  "
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
      <div className="min-h-screen flex flex-col items-center justify-center bg-white font-sans">
        <AlertTriangle className="w-12 h-12 text-zinc-300 mb-6" />
        <p className="text-sm font-medium text-zinc-500 mb-8">{error}</p>
        <button
          onClick={() => router.back()}
          className="h-10 px-6 bg-black text-white text-sm font-medium rounded-none  "
        >
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div
      className={`flex h-screen bg-white overflow-hidden font-sans animate-in fade-in slide-in-from-bottom-8 duration-300 ${document?.is_protected ? "select-none" : ""}`}
      onMouseUp={handleTextSelection}
    >
      <div className="w-16 border-r border-zinc-200 bg-white flex flex-col items-center py-6 gap-6 shrink-0">
        <button
          onClick={() => setSidebarTab("chat")}
          className={`p-3 rounded-none  ${sidebarTab === "chat" ? "bg-black text-white" : "text-zinc-500 "}`}
        >
          <Bot className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("highlights")}
          className={`p-3 rounded-none  ${sidebarTab === "highlights" ? "bg-black text-white" : "text-zinc-500 "}`}
        >
          <Highlighter className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("thumbnails")}
          className={`p-3 rounded-none  ${sidebarTab === "thumbnails" ? "bg-black text-white" : "text-zinc-500 "}`}
        >
          <BookOpen className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("history")}
          className={`p-3 rounded-none  ${sidebarTab === "history" ? "bg-black text-white" : "text-zinc-500 "}`}
        >
          <History className="w-5 h-5" />
        </button>
        {document?.content_format === "zip" && (
          <button
            onClick={() => setSidebarTab("zip")}
            className={`p-3 rounded-none  ${sidebarTab === "zip" ? "bg-black text-white" : "text-zinc-500 "}`}
          >
            <Folder className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-zinc-200 flex items-center justify-between px-6 bg-white shrink-0 z-40">
          <div className="flex items-center gap-4 flex-1">
            <button
              onClick={() => router.back()}
              className="p-2 text-zinc-500   rounded-none"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h1 className="text-sm font-medium text-black truncate max-w-xs md:max-w-md">
              {document?.title}
            </h1>
          </div>

          <div className="flex-1 flex justify-center text-sm font-medium text-zinc-500">
            Trang {currentPage} / {totalPages} (
            {((currentPage / totalPages) * 100).toFixed(0)}%)
          </div>

          <div className="flex items-center justify-end gap-6 flex-1">
            <div className="flex items-center gap-1">
              <button
                onClick={() => changeZoom(-10)}
                className="p-2 text-zinc-500   rounded-none"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-sm font-medium text-black min-w-[3rem] text-center">
                {zoom}%
              </span>
              <button
                onClick={() => changeZoom(10)}
                className="p-2 text-zinc-500   rounded-none"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>

            <div className="w-px h-4 bg-zinc-300" />

            <div className="flex items-center gap-1">
              <button
                onClick={() => setReadingMode("single")}
                className={`p-2 rounded-none  ${readingMode === "single" ? "text-black" : "text-zinc-400 "}`}
              >
                <Square className="w-4 h-4" />
              </button>
              <button
                onClick={() => setReadingMode("double")}
                className={`p-2 rounded-none  ${readingMode === "double" ? "text-black" : "text-zinc-400 "}`}
              >
                <Columns className="w-4 h-4" />
              </button>
            </div>

            <div className="w-px h-4 bg-zinc-300" />

            <button
              onClick={toggleBookmark}
              className={`p-2 rounded-none  ${isBookmarked ? "text-black" : "text-zinc-500 "}`}
            >
              {isBookmarked ? (
                <BookmarkCheck className="w-5 h-5" />
              ) : (
                <Bookmark className="w-5 h-5" />
              )}
            </button>
          </div>
        </header>

        <main
          className="flex-1 overflow-auto bg-zinc-50 p-8 md:p-12 relative flex justify-center animate-in fade-in slide-in-from-bottom-8 duration-300"
          style={{ animationDelay: "150ms", animationFillMode: "both" }}
        >
          <div
            className={`mx-auto bg-white border border-zinc-200 ${document?.content_format === "zip" ? "p-0 h-full max-w-full" : "p-12 md:p-24 min-h-full origin-top"} rounded-none ${readingMode === "double" && document?.content_format !== "zip" ? "w-full max-w-6xl" : document?.content_format !== "zip" ? "w-full max-w-3xl" : "w-full h-full"}`}
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
              className="fixed z-50 flex gap-1 bg-white p-1 border border-zinc-200 rounded-none  animate-in fade-in"
              style={{
                left: selection.x,
                top: selection.y,
                transform: "translateX(-50%)",
              }}
            >
              <button
                onClick={saveHighlight}
                className="p-2 text-zinc-600  "
                title="Lưu nêu bật"
              >
                <Highlighter className="w-4 h-4" />
              </button>
              <button
                onClick={handleTranslate}
                disabled={translating}
                className="p-2 text-zinc-600  "
                title="Dịch thuật"
              >
                {translating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Languages className="w-4 h-4" />
                )}
              </button>
              <button
                className="p-2 text-zinc-600  "
                title="Giải thích bằng AI"
              >
                <Zap className="w-4 h-4" />
              </button>
            </div>
          )}
        </main>
      </div>

      <div
        className={`${isExpanded ? "w-[500px] md:w-[600px]" : "w-[350px] md:w-[400px]"} border-l border-zinc-200 bg-white flex flex-col shrink-0 z-50 `}
      >
        <div className="h-14 border-b border-zinc-200 flex items-center px-6 justify-between bg-zinc-50 shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-black">
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
                className="p-1 text-zinc-500  "
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
              className={`px-3 py-1 text-xs font-medium border rounded-none  ${useSmart ? "bg-black text-white border-black" : "bg-white text-zinc-500 border-zinc-200  "}`}
            >
              {useSmart ? "Chuyên sâu" : "Tiêu chuẩn"}
            </button>
          )}
        </div>

        <div
          className="flex-1 overflow-y-auto p-6 scrollbar-thin animate-in fade-in slide-in-from-bottom-8 duration-300"
          style={{ animationDelay: "150ms", animationFillMode: "both" }}
        >
          {sidebarTab === "chat" ? (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-300">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} group`}
                >
                  <div
                    className={`w-8 h-8 shrink-0 border flex items-center justify-center rounded-none ${msg.role === "user" ? "bg-zinc-50 border-zinc-200" : "bg-black text-white border-black"}`}
                  >
                    {msg.role === "user" ? (
                      <User className="w-4 h-4 text-zinc-500" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-w-[85%]">
                    <div
                      className={`text-sm leading-relaxed p-4 border rounded-none relative ${msg.role === "user" ? "bg-zinc-50 border-zinc-200 text-black font-medium" : "bg-white border-zinc-200 text-black"}`}
                    >
                      {msg.content}
                      {msg.role === "user" && !asking && (
                        <button
                          onClick={() => setEditingMessageId(msg.id)}
                          className="absolute -left-10 top-0 opacity-0 group- p-2 text-zinc-400   rounded-none"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    {editingMessageId === msg.id && (
                      <div className="flex flex-col gap-3 mt-2">
                        <textarea
                          defaultValue={msg.content}
                          className="w-full p-3 text-sm border border-zinc-200 focus:outline-none focus:border-black rounded-none bg-white text-black"
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
                            className="text-xs font-medium px-4 py-2 border border-zinc-200  rounded-none text-black "
                          >
                            Hủy bỏ
                          </button>
                          <button
                            onClick={(ev) => {
                              const ta = ev.currentTarget.parentElement
                                ?.previousElementSibling as HTMLTextAreaElement;
                              handleEditAndResend(msg.id, ta.value);
                            }}
                            className="text-xs font-medium px-4 py-2 bg-black text-white  rounded-none "
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
                <div className="py-20 text-center flex flex-col items-center gap-4">
                  <Highlighter className="w-8 h-8 text-zinc-300" />
                  <p className="text-sm font-medium text-zinc-500">
                    Chưa có nêu bật nào
                  </p>
                </div>
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-4 border border-zinc-200 group rounded-none bg-zinc-50  "
                  >
                    <p className="text-sm font-medium text-black mb-4">
                      "{h.text}"
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-zinc-500">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button
                        onClick={() => deleteHighlight(h.id || h._id)}
                        className="p-1 text-zinc-400  "
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "history" ? (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-300">
              {sessions.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-4">
                  <History className="w-8 h-8 text-zinc-300" />
                  <p className="text-sm font-medium text-zinc-500">
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
                    className={`p-4 border cursor-pointer rounded-none group relative  ${currentSessionId === s._id ? "border-black bg-white" : "border-zinc-200 bg-zinc-50 "}`}
                  >
                    <p className="text-sm font-medium text-black truncate pr-8">
                      {s.title}
                    </p>
                    <p className="text-xs text-zinc-500 mt-2">
                      {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                    </p>
                    <button className="absolute right-4 top-4 opacity-0 group- text-zinc-400  ">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "zip" ? (
            <div className="space-y-1 overflow-x-auto text-sm animate-in fade-in">
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
                  className={`flex items-center gap-2 px-2 py-1.5 hover:bg-zinc-100 cursor-pointer rounded-none whitespace-nowrap ${!item.is_dir && selectedZipFile?.name === item.name ? "bg-zinc-100 font-medium" : "text-zinc-600"}`}
                  style={{
                    paddingLeft: `${item.path.split("/").length * 12}px`,
                  }}
                >
                  {item.is_dir ? (
                    <Folder className="w-4 h-4 text-zinc-400 shrink-0" />
                  ) : (
                    <FileText className="w-4 h-4 text-zinc-400 shrink-0" />
                  )}
                  <span className="truncate">{item.name}</span>
                </div>
              ))}
              {zipTree.length === 0 && (
                <div className="py-20 text-center text-zinc-400">
                  <p>Đang tải cây thư mục...</p>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <div
                  key={p}
                  onClick={() => setCurrentPage(p)}
                  className={`aspect-[3/4] border flex flex-col items-center justify-center gap-2 cursor-pointer rounded-none  ${currentPage === p ? "bg-black text-white border-black" : "bg-white border-zinc-200 text-zinc-500 "}`}
                >
                  <span className="text-sm font-medium">{p}</span>
                  <span className="text-xs uppercase">Trang</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {sidebarTab === "chat" && (
          <div className="p-6 border-t border-zinc-200 bg-white relative shrink-0">
            {showAttachments && (
              <div className="absolute bottom-full left-6 right-6 mb-4 p-4 bg-white border border-zinc-200 rounded-none z-[60]  animate-in fade-in">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs font-medium text-black uppercase tracking-wide">
                    Đính kèm tài liệu
                  </span>
                  <button
                    onClick={() => setShowAttachments(false)}
                    className="text-zinc-500  "
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex items-center gap-2 p-3 border border-zinc-200 rounded-none text-xs font-medium   text-black">
                    <FileText className="w-4 h-4" /> Thư viện
                  </button>
                  <button className="flex items-center gap-2 p-3 border border-zinc-200 rounded-none text-xs font-medium   text-black">
                    <ImageIcon className="w-4 h-4" /> Hình ảnh
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
                className="w-full min-h-[120px] p-4 pb-16 text-sm font-medium border border-zinc-200 focus:outline-none focus:border-black resize-none rounded-none  placeholder:text-zinc-400 text-black bg-zinc-50 focus:bg-white"
                placeholder="Hỏi bất cứ điều gì về tài liệu này"
                disabled={asking}
              />
              <div className="absolute bottom-4 left-4 flex items-center gap-3">
                <button
                  onClick={() => setShowAttachments(!showAttachments)}
                  className="w-8 h-8 flex items-center justify-center text-zinc-500   rounded-none"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={() => handleAskAI()}
                disabled={asking || !question.trim()}
                className="absolute bottom-4 right-4 w-8 h-8 bg-black text-white flex items-center justify-center disabled:opacity-50 rounded-none "
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
