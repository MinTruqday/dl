"use client";

import { useToast } from "@/contexts/ToastContext";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken, API_URL } from "@/services/auth.service";
import { queryRagAPI, translateTextAPI } from "@/services/ai.service";
import {
  createHighlightAPI,
  getHighlightsAPI,
  deleteHighlightAPI,
  toggleBookmarkAPI,
  getBookmarksAPI,
} from "@/services/read.service";
import {
  Lock,
  AlertTriangle,
  Send,
  MessageSquare,
  ArrowLeft,
  Loader2,
  Sparkles,
  User,
  Bot,
  Highlighter,
  Bookmark,
  Info,
  ShieldCheck,
  Zap,
  Trash2,
  BookmarkCheck,
  ZoomIn,
  ZoomOut,
  Maximize,
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
  const [usePro, setUsePro] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<
    "chat" | "highlights" | "thumbnails" | "history"
  >("chat");
  const [viewMode, setViewMode] = useState<"text" | "pdf">("text");
  const [zoom, setZoom] = useState(100);
  const [readingMode, setReadingMode] = useState<"single" | "double">("single");
  const [currentPage, setCurrentPage] = useState(1);
  const [isExpanded, setIsExpanded] = useState(false);

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
      showToast("Không thể đồng bộ các điểm nhấn tri thức", "error");
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
    } catch {
      // Silent failure for bookmark check
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

        let url = `${API_URL}/documents/${id}`;
        if (pwd) url += `?password=${encodeURIComponent(pwd)}`;

        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });

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
        } else {
          setError("Quyền truy cập của bạn bị giới hạn đối với thực thể này");
        }
      } catch (e) {
        setError("Mất kết nối với hệ thống lưu trữ DocLib");
      } finally {
        setLoading(false);
      }
    },
    [id, router],
  );

  const fetchSessions = useCallback(async () => {
    try {
      const token = getToken();
      const res = await fetch(`${API_URL}/ai/history?document_id=${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.data || []);
      }
    } catch {
      showToast("Không thể đồng bộ lịch sử hội thoại", "error");
    }
  }, [id, showToast]);

  useEffect(() => {
    fetchDocument();
    fetchHighlights();
    checkBookmarkStatus();
    fetchSessions();
  }, [fetchDocument, fetchHighlights, checkBookmarkStatus, fetchSessions]);

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
        const res = await fetch(`${API_URL}/ai/history`, {
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
      } catch {
        showToast("Không thể khởi tạo phiên làm việc AI", "error");
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
        usePro,
        sessionId || undefined,
      );
      const res: any = await Promise.race([apiCall, timeoutPromise]);

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          res.data?.answer ||
          res.answer ||
          "Cố vấn AI không thể trích xuất dữ liệu phản hồi",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const errorMsg =
        e.message === "AI_TIMEOUT"
          ? "Giao thức AI phản hồi chậm hơn dự kiến, vui lòng thử lại."
          : `Giao thức AI gặp lỗi: ${e.message || "Không thể kết nối với trung tâm trí tuệ"}`;

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
      showToast("Giao thức dịch thuật AI không khả dụng lúc này", "error");
    } finally {
      setTranslating(false);
    }
  };

  const saveHighlight = async () => {
    if (!selection) return;
    try {
      await createHighlightAPI(id, selection.text, "#F4F4F5");
      fetchHighlights();
      setSelection(null);
      window.getSelection()?.removeAllRanges();
      showToast("Đã ghi nhận điểm nhấn vào nhật ký học thuật", "success");
    } catch (e) {
      showToast("Giao thức lưu trữ điểm nhấn thất bại", "error");
    }
  };

  const deleteHighlight = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      setHighlights((prev) =>
        prev.filter((h) => (h.id || h._id) !== highlightId),
      );
      showToast("Đã loại bỏ điểm nhấn khỏi thực thể", "success");
    } catch (err: any) {
      showToast("Giao thức xóa bỏ thất bại", "error");
    }
  };

  const toggleBookmark = async () => {
    try {
      await toggleBookmarkAPI(id);
      setIsBookmarked(!isBookmarked);
      showToast(
        isBookmarked
          ? "Đã gỡ thực thể khỏi thư viện"
          : "Đã lưu thực thể vào thư viện",
        "success",
      );
    } catch (err: any) {
      showToast("Giao thức thư viện thất bại", "error");
    }
  };

  const changeZoom = (delta: number) => {
    setZoom((prev) => Math.min(Math.max(50, prev + delta), 200));
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white font-sans">
        <div className="flex flex-col items-center gap-10">
          <div className="w-12 h-[1px] bg-zinc-200 animate-pulse" />
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
            Đang đồng bộ thực thể tri thức
          </p>
        </div>
      </div>
    );
  }

  const getPageContent = () => {
    const content =
      document?.content ||
      document?.description ||
      "Không có nội dung hiển thị";
    const charsPerPage = 3000;

    if (readingMode === "double") {
      const start1 = (currentPage - 1) * charsPerPage * 2;
      const end1 = start1 + charsPerPage;
      const start2 = end1;
      const end2 = start2 + charsPerPage;

      return (
        <div className="grid grid-cols-2 gap-16 w-full">
          <div className="prose prose-zinc max-w-none text-zinc-800 leading-relaxed text-base font-medium whitespace-pre-wrap">
            {content.substring(start1, end1)}
          </div>
          <div className="prose prose-zinc max-w-none text-zinc-800 leading-relaxed text-base font-medium whitespace-pre-wrap">
            {content.substring(start2, end2)}
          </div>
        </div>
      );
    }

    const start = (currentPage - 1) * charsPerPage;
    const end = start + charsPerPage;
    return (
      <div className="prose prose-zinc max-w-none text-zinc-800 leading-relaxed text-base font-medium whitespace-pre-wrap">
        {content.substring(start, end)}
      </div>
    );
  };

  const totalPages =
    Math.ceil(
      (document?.content?.length || 0) /
        (readingMode === "double" ? 6000 : 3000),
    ) || 1;

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white/20 p-6 font-sans">
        <div className="bg-white p-16 w-full max-w-lg border border-zinc-100 flex flex-col items-center text-center animate-in zoom-in-95 rounded-sm">
          <div className="w-20 h-20 bg-black flex items-center justify-center mb-12 rounded-sm">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-lg font-bold text-black mb-4 uppercase tracking-widest">
            Thực thể bảo mật
          </h2>
          <p className="text-[11px] font-bold text-zinc-300 mb-12 uppercase tracking-widest">
            Nhập mã định danh để tiếp cận tầng dữ liệu bảo mật
          </p>
          <div className="w-full space-y-4">
            <input
              type="password"
              className="w-full h-14 bg-white border border-zinc-100 px-6 text-center text-sm font-bold focus:outline-none focus:border-black rounded-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-14 bg-black text-white text-[11px] font-bold uppercase tracking-widest rounded-sm"
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
        <AlertTriangle className="w-12 h-12 text-zinc-100 mb-8" />
        <p className="text-[11px] font-bold text-zinc-400 mb-12 uppercase tracking-widest">
          {error}
        </p>
        <button
          onClick={() => router.back()}
          className="h-14 px-12 bg-black text-white text-[11px] font-bold uppercase tracking-widest rounded-sm"
        >
          Quay lại mạng lưới
        </button>
      </div>
    );
  }

  return (
    <div
      className={`flex h-screen bg-white overflow-hidden transition-opacity font-sans ${document?.is_protected ? "select-none" : ""}`}
      style={{ opacity: visible ? 1 : 0 }}
      onMouseUp={handleTextSelection}
    >
      <div className="w-20 border-r border-zinc-100 bg-white flex flex-col items-center py-8 gap-10 shrink-0">
        <button
          onClick={() => setSidebarTab("chat")}
          className={`p-4 rounded-sm ${sidebarTab === "chat" ? "bg-black text-white" : "text-zinc-200"}`}
        >
          <Bot className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("highlights")}
          className={`p-4 rounded-sm ${sidebarTab === "highlights" ? "bg-black text-white" : "text-zinc-200"}`}
        >
          <Highlighter className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("thumbnails")}
          className={`p-4 rounded-sm ${sidebarTab === "thumbnails" ? "bg-black text-white" : "text-zinc-200"}`}
        >
          <BookOpen className="w-5 h-5" />
        </button>
        <button
          onClick={() => setSidebarTab("history")}
          className={`p-4 rounded-sm ${sidebarTab === "history" ? "bg-black text-white" : "text-zinc-200"}`}
        >
          <History className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-zinc-100 flex items-center justify-between px-8 bg-white shrink-0 z-50">
          <div className="flex items-center gap-6">
            <button
              onClick={() => router.back()}
              className="p-2 text-zinc-300 "
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-[12px] font-bold text-black uppercase tracking-tight truncate max-w-lg">
              {document?.title}
            </h1>
          </div>

          <div className="flex items-center gap-4 bg-white p-1 border border-zinc-100 rounded-sm">
            <button
              onClick={() => changeZoom(-10)}
              className="p-2 text-zinc-400 "
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-[10px] font-bold text-black min-w-[40px] text-center">
              {zoom}%
            </span>
            <button
              onClick={() => changeZoom(10)}
              className="p-2 text-zinc-400 "
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-zinc-200 mx-2" />
            <button
              onClick={() =>
                setReadingMode(readingMode === "single" ? "double" : "single")
              }
              className={`p-2 rounded-sm ${readingMode === "double" ? "text-black" : "text-zinc-300"}`}
            >
              {readingMode === "single" ? (
                <Square className="w-4 h-4" />
              ) : (
                <Columns className="w-4 h-4" />
              )}
            </button>
          </div>

          <div className="flex items-center gap-6">
            <button
              onClick={toggleBookmark}
              className={`p-2 ${isBookmarked ? "text-black" : "text-zinc-200"}`}
            >
              {" "}
              {isBookmarked ? (
                <BookmarkCheck className="w-5 h-5" />
              ) : (
                <Bookmark className="w-5 h-5" />
              )}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-zinc-100/30 p-12 scrollbar-thin relative">
          <div
            className={`mx-auto bg-white border border-zinc-100 p-16 md:p-24 shadow-none rounded-sm min-h-full origin-top`}
            style={{
              width: readingMode === "double" ? "1800px" : "900px",
              transform: `scale(${zoom / 100})`,
              transformOrigin: "top center",
            }}
          >
            {getPageContent()}
          </div>

          {selection && (
            <div
              className="fixed z-50 flex gap-1 bg-black p-1 border border-black rounded-sm animate-in zoom-in-95 "
              style={{
                left: selection.x,
                top: selection.y,
                transform: "translateX(-50%)",
              }}
            >
              <button
                onClick={saveHighlight}
                className="p-2 text-white "
                title="Highlight"
              >
                <Highlighter className="w-4 h-4" />
              </button>
              <button
                onClick={handleTranslate}
                disabled={translating}
                className="p-2 text-white "
                title="Dịch thuật"
              >
                {translating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Languages className="w-4 h-4" />
                )}
              </button>
              <button className="p-2 text-white " title="Giải thích AI">
                <Zap className="w-4 h-4" />
              </button>
            </div>
          )}
        </main>
      </div>

      <div
        className={`${isExpanded ? "w-[800px]" : "w-[400px]"} border-l border-zinc-100 bg-white flex flex-col shrink-0 z-50 `}
      >
        <div className="h-16 border-b border-zinc-100 flex items-center px-6 justify-between bg-white/10">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-bold text-black uppercase tracking-widest">
              {sidebarTab === "chat"
                ? "Cố vấn AI"
                : sidebarTab === "highlights"
                  ? "Điểm nhấn tri thức"
                  : sidebarTab === "history"
                    ? "Lịch sử hội thoại"
                    : "Danh mục trang"}
            </span>
            {sidebarTab === "chat" && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1 text-zinc-300 "
              >
                {isExpanded ? (
                  <Minimize2 className="w-3.5 h-3.5" />
                ) : (
                  <Maximize2 className="w-3.5 h-3.5" />
                )}
              </button>
            )}
          </div>
          {sidebarTab === "chat" && (
            <button
              onClick={() => setUsePro(!usePro)}
              className={`h-8 px-4 text-[9px] font-bold border uppercase tracking-widest rounded-sm ${usePro ? "bg-black text-white border-black" : "text-zinc-300 border-zinc-100"}`}
            >
              {usePro ? "Pro" : "Standard"}
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
          {sidebarTab === "chat" ? (
            <div className="space-y-8 animate-in fade-in ">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} group`}
                >
                  <div
                    className={`w-10 h-10 shrink-0 border flex items-center justify-center rounded-sm ${msg.role === "user" ? "bg-white border-zinc-100" : "bg-black text-white border-black"}`}
                  >
                    {msg.role === "user" ? (
                      <User className="w-4 h-4 text-zinc-300" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex flex-col gap-2 max-w-[80%]">
                    <div
                      className={`text-[13px] leading-relaxed p-6 border rounded-sm relative ${msg.role === "user" ? "bg-white/20 border-zinc-100 text-zinc-500" : "bg-white border-zinc-100 text-black font-bold"}`}
                    >
                      {msg.content}
                      {msg.role === "user" && !asking && (
                        <button
                          onClick={() => setEditingMessageId(msg.id)}
                          className="absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 p-2 text-zinc-300 "
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    {editingMessageId === msg.id && (
                      <div className="flex flex-col gap-2 mt-2">
                        <textarea
                          defaultValue={msg.content}
                          className="w-full p-4 text-[13px] border border-black focus:outline-none rounded-sm bg-white"
                          onKeyDown={(e: any) =>
                            e.key === "Enter" &&
                            handleEditAndResend(msg.id, e.target.value)
                          }
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingMessageId(null)}
                            className="text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-sm"
                          >
                            Hủy
                          </button>
                          <button className="text-[10px] font-bold uppercase tracking-widest px-4 py-2 bg-black text-white rounded-sm">
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
            <div className="space-y-6">
              {!Array.isArray(highlights) || highlights.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-6 opacity-30">
                  <Highlighter className="w-10 h-10 stroke-[1]" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">
                    Chưa có tri thức nào được ghi nhận
                  </p>
                </div>
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-6 border border-zinc-100 group rounded-sm"
                  >
                    <p className="text-[13px] font-bold text-black italic mb-4">
                      "{h.text}"
                    </p>
                    <div className="flex justify-between items-center opacity-40 ">
                      <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button
                        onClick={() => deleteHighlight(h.id || h._id)}
                        className="p-1 "
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : sidebarTab === "history" ? (
            <div className="space-y-4 animate-in slide-in-from-right ">
              {sessions.length === 0 ? (
                <div className="py-20 text-center flex flex-col items-center gap-6 opacity-30">
                  <History className="w-10 h-10 stroke-[1]" />
                  <p className="text-[10px] font-bold uppercase tracking-widest">
                    Chưa có dấu ấn tri thức nào
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
                    className={`p-6 border cursor-pointer rounded-sm group relative ${currentSessionId === s._id ? "border-black bg-white" : "border-zinc-100"}`}
                  >
                    <p className="text-[11px] font-bold text-black uppercase tracking-tight pr-8">
                      {s.title}
                    </p>
                    <p className="text-[9px] font-bold text-zinc-400 mt-2 uppercase tracking-widest">
                      {new Date(s.updated_at).toLocaleDateString("vi-VN")}
                    </p>
                    <button className="absolute right-6 top-6 opacity-0 text-zinc-300 ">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-6">
              {[1, 2, 3, 4].map((p) => (
                <div
                  key={p}
                  className="aspect-[3/4] bg-white border border-zinc-100 flex flex-col items-center justify-center gap-4 cursor-pointer rounded-sm"
                >
                  <div className="w-8 h-8 border border-zinc-100 flex items-center justify-center rounded-sm text-[10px] font-bold text-zinc-300">
                    {p}
                  </div>
                  <span className="text-[9px] font-bold text-zinc-300 uppercase tracking-widest">
                    Trang {p}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-zinc-100 bg-white relative">
          {showAttachments && (
            <div className="absolute bottom-full left-6 right-6 mb-4 p-4 bg-white border border-black animate-in slide-in-from-bottom-4 rounded-sm z-[60]">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest">
                  Đính kèm thực thể
                </span>
                <button onClick={() => setShowAttachments(false)}>
                  <X className="w-3 h-3" />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <button className="flex items-center gap-3 p-3 border border-zinc-100 rounded-sm text-[11px] font-bold uppercase tracking-tight">
                  <FileText className="w-4 h-4" /> Thư viện
                </button>
                <button className="flex items-center gap-3 p-3 border border-zinc-100 rounded-sm text-[11px] font-bold uppercase tracking-tight">
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
              className="w-full min-h-[140px] p-6 pb-20 text-[13px] font-medium border border-zinc-100 focus:outline-none focus:border-black resize-none rounded-sm"
              placeholder=""
              disabled={asking}
            />
            <div className="absolute bottom-6 left-6 flex items-center gap-4">
              <button
                onClick={() => setShowAttachments(!showAttachments)}
                className="w-10 h-10 border border-zinc-100 text-zinc-300 flex items-center justify-center rounded-sm"
              >
                <Paperclip className="w-4 h-4" />
              </button>
            </div>
            <button
              onClick={() => handleAskAI()}
              disabled={asking || !question.trim()}
              className="absolute bottom-6 right-6 w-12 h-12 bg-black text-white flex items-center justify-center disabled:opacity-30 rounded-sm"
            >
              {asking ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
