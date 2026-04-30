"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  getToken, 
  API_URL, 
  queryRagAPI, 
  createHighlightAPI, 
  getHighlightsAPI, 
  deleteHighlightAPI,
  toggleBookmarkAPI,
  getBookmarksAPI
} from "@/app/lib/api";
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
  BookmarkCheck
} from "lucide-react";
import { Notification } from "@/app/components/NotificationToast";

export default function DocumentViewer() {
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
  const [sidebarTab, setSidebarTab] = useState<"chat" | "highlights">("chat");
  const [viewMode, setViewMode] = useState<"text" | "pdf">("text");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [highlights, setHighlights] = useState<any[]>([]);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [selection, setSelection] = useState<{ text: string; x: number; y: number } | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchHighlights = useCallback(async () => {
    try {
      const res = await getHighlightsAPI(id);
      setHighlights(res.data || res || []);
    } catch (err: any) {
        setNotification({ type: "error", text: "Không thể kết nối mạng lưới điểm nhấn" });
    }
  }, [id]);

  const checkBookmarkStatus = useCallback(async () => {
    try {
        const bookmarks = await getBookmarksAPI();
        if (bookmarks?.data) {
            setIsBookmarked(bookmarks.data.some((b: any) => b._id === id));
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
        let url = `${API_URL}/documents/${id}`;
        if (pwd) url += `?password=${encodeURIComponent(pwd)}`;

        const res = await fetch(url, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        if (res.status === 403) {
          setIsLocked(true);
          setLoading(false);
          return;
        }

        if (res.ok) {
          const data = await res.json();
          setDocument(data.data || data);
          setIsLocked(false);
        } else {
          setError("Quyền hạn của bạn không đủ để tiếp cận thực thể này");
        }
      } catch (e) {
        setError("Mất kết nối với mạng lưới tri thức DocLib");
      } finally {
        setLoading(false);
      }
    },
    [id]
  );

  useEffect(() => {
    fetchDocument();
    fetchHighlights();
    checkBookmarkStatus();
  }, [fetchDocument, fetchHighlights, checkBookmarkStatus]);

  useEffect(() => {
    if (!loading) requestAnimationFrame(() => setVisible(true));
  }, [loading]);

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleAskAI = async () => {
    if (!question.trim()) return;
    const userMsg = { role: "user", content: question.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setAsking(true);

    try {
      const res = await queryRagAPI(id, userMsg.content, usePro);
      const aiMsg = {
        role: "assistant",
        content: res.data?.answer || res.answer || "Cố vấn AI không tìm thấy dữ liệu phản hồi trong thực thể này",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Giao thức AI thất bại: ${e.message || "Không thể kết nối với trung tâm trí tuệ nhân tạo"}` },
      ]);
    } finally {
      setAsking(false);
    }
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
        y: rect.top + window.scrollY - 40,
      });
    } else {
      setSelection(null);
    }
  };

  useEffect(() => {
    if (!document?.is_protected) return;

    const preventAction = (e: any) => {
        e.preventDefault();
        setNotification({ type: "error", text: "Thực thể này được bảo mật bởi giao thức chống sao chép" });
    };

    const handleContextMenu = (e: MouseEvent) => preventAction(e);
    const handleKeyDown = (e: KeyboardEvent) => {
        const isCmdOrCtrl = e.metaKey || e.ctrlKey;
        if (isCmdOrCtrl && (e.key === 'c' || e.key === 's' || e.key === 'p' || e.key === 'u')) {
            preventAction(e);
        }
        if (e.key === 'F12') preventAction(e);
    };

    window.addEventListener("contextmenu", handleContextMenu);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
        window.removeEventListener("contextmenu", handleContextMenu);
        window.removeEventListener("keydown", handleKeyDown);
    };
  }, [document?.is_protected]);

  const saveHighlight = async () => {
    if (!selection) return;
    try {
      await createHighlightAPI(id, selection.text, "#F4F4F5");
      fetchHighlights();
      setSelection(null);
      window.getSelection()?.removeAllRanges();
      setNotification({ type: "success", text: "Đã lưu điểm nhấn vào bộ sưu tập cá nhân" });
    } catch (e) {
      setNotification({ type: "error", text: "Giao thức lưu trữ điểm nhấn thất bại" });
    }
  };

  const deleteHighlight = async (highlightId: string) => {
    try {
        await deleteHighlightAPI(highlightId);
        setHighlights(prev => prev.filter(h => h._id !== highlightId));
        setNotification({ type: "success", text: "Đã xóa bỏ điểm nhấn khỏi thực thể" });
    } catch (err: any) {
        setNotification({ type: "error", text: "Giao thức xóa bỏ thất bại" });
    }
  };

  const toggleBookmark = async () => {
    try {
        await toggleBookmarkAPI(id);
        setIsBookmarked(!isBookmarked);
        setNotification({ type: "success", text: isBookmarked ? "Đã gỡ bỏ thực thể khỏi thư viện" : "Đã lưu trữ thực thể vào thư viện" });
    } catch (err: any) {
        setNotification({ type: "error", text: "Giao thức thư viện thất bại" });
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white font-sans">
        <div className="flex flex-col items-center gap-10">
          <div className="relative">
              <Loader2 className="w-16 h-16 animate-spin text-zinc-100 stroke-[1]" />
              <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-2 h-2 bg-black rounded-full animate-pulse" />
              </div>
          </div>
          <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.5em]">Đang khởi tạo môi trường đọc tri thức</p>
        </div>
      </div>
    );
  }

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50/20 p-6 font-sans">
        <div className="bg-white p-16 w-full max-w-lg border border-zinc-100 flex flex-col items-center text-center animate-in zoom-in-95 duration-700 rounded-sm">
          <div className="w-20 h-20 bg-black flex items-center justify-center mb-12 rounded-sm">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-xl font-bold text-black mb-4 uppercase tracking-widest">Tài liệu bảo mật</h2>
          <p className="text-[11px] font-bold text-zinc-300 mb-12 leading-loose uppercase tracking-widest">
            Vui lòng nhập mã định danh bảo mật để tiếp cận nội dung thực thể
          </p>
          <div className="w-full space-y-6">
            <input
              type="password"
              placeholder=""
              className="w-full h-16 bg-zinc-50/50 border border-zinc-100 px-8 text-center text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all rounded-sm placeholder:text-zinc-200"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-16 bg-black text-white hover:bg-zinc-800 text-[11px] font-bold uppercase tracking-[0.4em] transition-all active:scale-95 rounded-sm"
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
      <div className="min-h-screen flex flex-col items-center justify-center bg-white p-12 font-sans">
        <div className="w-24 h-24 bg-zinc-50 flex items-center justify-center mb-12 border border-zinc-100 rounded-sm">
            <AlertTriangle className="w-10 h-10 text-zinc-200 stroke-[1.5]" />
        </div>
        <p className="text-[11px] font-bold text-zinc-400 mb-12 uppercase tracking-[0.3em]">{error}</p>
        <button
          onClick={() => router.back()}
          className="h-16 px-16 bg-black text-white text-[11px] font-bold uppercase tracking-[0.4em] transition-all active:scale-95 rounded-sm"
        >
          Quay lại mạng lưới
        </button>
      </div>
    );
  }

  return (
    <div
      className={`flex h-screen bg-white overflow-hidden transition-opacity duration-1000 font-sans ${document?.is_protected ? 'select-none' : ''}`}
      style={{ opacity: visible ? 1 : 0 }}
      onMouseUp={handleTextSelection}
    >
      {notification && (
        <div className="fixed top-24 right-8 z-[1100] w-80 animate-in slide-in-from-right-4 duration-300">
          <Notification type={notification.type} message={notification.text} />
        </div>
      )}

      {selection && (
        <div
          className="fixed z-[500] animate-in zoom-in-95 duration-300"
          style={{ left: selection.x, top: selection.y, transform: "translateX(-50%)" }}
        >
          <button
            onClick={saveHighlight}
            className="bg-black text-white px-8 py-4 text-[11px] font-bold uppercase tracking-widest flex items-center gap-4 hover:bg-zinc-800 border border-black transition-all active:scale-95 rounded-sm"
          >
            <Highlighter className="w-4 h-4" /> Làm nổi bật tri thức
          </button>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-20 border-b border-zinc-100 flex items-center justify-between px-10 bg-white shrink-0 z-50">
          <div className="flex items-center gap-8 min-w-0">
            <button
              onClick={() => router.back()}
              className="p-3 text-zinc-300 hover:text-black hover:bg-zinc-50 transition-all active:scale-90 rounded-sm"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="h-6 w-px bg-zinc-100" />
            <h1 className="text-sm font-bold text-black uppercase tracking-tight truncate max-w-3xl">{document?.title}</h1>
            {document?.is_protected && (
                <div className="flex items-center gap-3 px-4 py-2 bg-zinc-50 border border-zinc-100 rounded-sm">
                    <ShieldCheck className="w-3.5 h-3.5 text-black" />
                    <span className="text-[9px] font-bold uppercase tracking-widest text-black">Bảo mật đa lớp</span>
                </div>
            )}
          </div>
          <div className="flex items-center gap-8 shrink-0">
            {document?.file_url && document.file_url.toLowerCase().endsWith('.pdf') && (
                <div className="flex bg-zinc-50 p-1 border border-zinc-100 rounded-sm">
                    <button 
                        onClick={() => setViewMode("text")}
                        className={`px-6 h-10 text-[9px] font-bold uppercase tracking-widest transition-all rounded-sm ${viewMode === 'text' ? 'bg-black text-white' : 'text-zinc-300 hover:text-black'}`}
                    >
                        Góc nhìn trí tuệ
                    </button>
                    <button 
                        onClick={() => setViewMode("pdf")}
                        className={`px-6 h-10 text-[9px] font-bold uppercase tracking-widest transition-all rounded-sm ${viewMode === 'pdf' ? 'bg-black text-white' : 'text-zinc-300 hover:text-black'}`}
                    >
                        Tài liệu gốc
                    </button>
                </div>
            )}
            <div className="h-6 w-px bg-zinc-100 hidden md:block" />
            <button 
                onClick={toggleBookmark}
                className={`p-3 transition-all active:scale-90 rounded-sm ${isBookmarked ? 'text-black bg-zinc-50' : 'text-zinc-300 hover:text-black hover:bg-zinc-50'}`}
            >
              {isBookmarked ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-zinc-50/10 scrollbar-thin">
            {viewMode === "pdf" && document?.file_url ? (
                <div className="w-full h-full relative">
                    {document.is_protected && <div className="absolute inset-0 z-10 bg-transparent" onContextMenu={(e) => e.preventDefault()} />}
                    <iframe 
                        src={`${API_URL}${document.file_url}#toolbar=0`} 
                        className="w-full h-full border-none"
                        title="Document Viewer"
                    />
                </div>
            ) : (
                <div className="p-12 md:p-24 lg:p-32">
                    <div className="max-w-5xl mx-auto bg-white border border-zinc-100 p-16 md:p-24 lg:p-36 min-h-full relative animate-in slide-in-from-bottom-12 duration-1000 rounded-sm shadow-none">
                        <div className="prose prose-zinc max-w-none text-zinc-800 leading-loose text-lg font-medium">
                        {document?.content || document?.description || (
                            <div className="py-32 text-center space-y-10">
                                <Loader2 className="w-12 h-12 animate-spin text-zinc-50 mx-auto stroke-[1]" />
                                <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.4em]">Đang trích xuất tri thức từ thực thể</p>
                            </div>
                        )}
                        </div>
                        {document?.chapters &&
                        document.chapters.map((ch: any, idx: number) => (
                            <div key={idx} className="mt-32 pt-32 border-t border-zinc-50">
                            <h2 className="text-2xl font-bold text-black mb-16 uppercase tracking-tight">{ch.title}</h2>
                            <div className="prose prose-zinc max-w-none text-zinc-800 leading-loose text-lg font-medium">{ch.content}</div>
                            </div>
                        ))}

                        {highlights.length > 0 && (
                        <div className="absolute right-0 top-0 bottom-0 w-1 flex flex-col gap-1 pointer-events-none opacity-20">
                            {highlights.map((h, i) => (
                            <div key={i} className="w-full h-8 bg-zinc-200" title={h.text} />
                            ))}
                        </div>
                        )}
                    </div>
                </div>
            )}
        </main>
      </div>

      <div className="w-[480px] border-l border-zinc-100 flex flex-col bg-white hidden xl:flex z-50">
        <div className="h-20 p-8 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/10">
          <div className="flex gap-8">
            <button
              onClick={() => setSidebarTab("chat")}
              className={`flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest transition-all ${
                sidebarTab === "chat" ? "text-black" : "text-zinc-200 hover:text-black"
              }`}
            >
              <Sparkles className="w-4 h-4" /> Cố vấn AI
            </button>
            <button
              onClick={() => setSidebarTab("highlights")}
              className={`flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest transition-all ${
                sidebarTab === "highlights" ? "text-black" : "text-zinc-200 hover:text-black"
              }`}
            >
              <Highlighter className="w-4 h-4" /> Điểm nhấn ({highlights.length})
            </button>
          </div>
          <button
            onClick={() => setUsePro(!usePro)}
            className={`px-4 h-10 text-[9px] font-bold border uppercase tracking-widest transition-all active:scale-95 rounded-sm ${
              usePro ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
            }`}
          >
            {usePro ? "Chế độ Pro" : "Chế độ Standard"}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-12 scrollbar-thin">
          {sidebarTab === "chat" ? (
            <div className="space-y-12">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-10 py-32 opacity-80">
                  <div className="w-24 h-24 bg-zinc-50/50 flex items-center justify-center border border-zinc-100 group rounded-sm">
                    <Zap className="w-10 h-10 text-zinc-100 group-hover:text-black transition-all stroke-[1]" />
                  </div>
                  <div className="space-y-4">
                    <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Trí tuệ nhân tạo DocLib</p>
                    <p className="text-[10px] text-zinc-300 leading-loose font-bold uppercase tracking-widest px-12">
                      Tương tác để giải mã sâu hơn những tầng tri thức ẩn giấu trong thực thể này
                    </p>
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-6 animate-in fade-in slide-in-from-bottom-2 duration-500 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div
                    className={`w-12 h-12 shrink-0 flex items-center justify-center border rounded-sm ${
                      msg.role === "user" ? "bg-zinc-50 border-zinc-100" : "bg-black border-black text-white shadow-none"
                    }`}
                  >
                    {msg.role === "user" ? <User className="w-5 h-5 text-zinc-200" /> : <Bot className="w-5 h-5" />}
                  </div>
                  <div
                    className={`text-sm leading-loose p-8 border rounded-sm ${
                      msg.role === "user" ? "bg-zinc-50/20 border-zinc-100 text-zinc-500 font-medium" : "bg-white border-zinc-100 text-black font-bold"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          ) : (
            <div className="space-y-10">
              {highlights.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-10 py-32 opacity-40">
                  <Highlighter className="w-20 h-20 text-zinc-100 stroke-[1]" />
                  <p className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.3em]">Chưa có tri thức nào được làm nổi bật</p>
                </div>
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-10 border border-zinc-100 bg-zinc-50/10 hover:border-black transition-all duration-700 group rounded-sm animate-in fade-in duration-500"
                  >
                    <p className="text-sm leading-loose text-black font-bold mb-8 italic">"{h.text}"</p>
                    <div className="flex justify-between items-center border-t border-zinc-50 pt-8">
                      <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button 
                        onClick={() => deleteHighlight(h._id)}
                        className="p-2 text-zinc-300 hover:text-black transition-all opacity-0 group-hover:opacity-100"
                        title="Xóa bỏ tri thức"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="p-12 border-t border-zinc-100 bg-white">
          <div className="relative group">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleAskAI())}
              placeholder=""
              className="w-full min-h-[160px] p-10 text-sm font-medium border border-zinc-100 focus:outline-none focus:border-black focus:bg-zinc-50/20 transition-all resize-none placeholder:text-zinc-200 rounded-sm"
              disabled={asking}
            />
            <button
              onClick={handleAskAI}
              disabled={asking || !question.trim()}
              className="absolute bottom-8 right-8 h-14 w-14 bg-black text-white hover:bg-zinc-800 flex items-center justify-center transition-all active:scale-90 disabled:opacity-50 rounded-sm"
            >
              {asking ? <Loader2 className="w-6 h-6 animate-spin" /> : <Send className="w-6 h-6" />}
            </button>
          </div>
          <div className="mt-8 flex items-center justify-center gap-4 text-[10px] font-bold text-zinc-200 uppercase tracking-widest">
            <Info className="w-4 h-4 text-zinc-100" /> Hệ thống AI có thể cung cấp dữ liệu chưa hoàn thiện
          </div>
        </div>
      </div>
    </div>
  );
}
