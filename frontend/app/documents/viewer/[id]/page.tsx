"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken, API_URL, queryRagAPI, createHighlightAPI, getHighlightsAPI } from "@/app/lib/api";
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
  const [selection, setSelection] = useState<{ text: string; x: number; y: number } | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchHighlights = useCallback(async () => {
    try {
      const data = await getHighlightsAPI(id);
      setHighlights(data || []);
    } catch (err: any) {
      console.error("Lỗi tải highlights:", err);
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
          setError("Bạn không có quyền truy cập nội dung này.");
        }
      } catch (e) {
        setError("Mất kết nối với máy chủ tri thức.");
      } finally {
        setLoading(false);
      }
    },
    [id, API_URL]
  );

  useEffect(() => {
    fetchDocument().then(doc => {
        console.log("Loaded document:", doc);
    });
    fetchHighlights();
  }, [fetchDocument, fetchHighlights]);

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
        content: res.data?.answer || res.answer || "Cố vấn AI không tìm thấy câu trả lời trong tài liệu này.",
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Lỗi: ${e.message || "Không thể kết nối với hệ thống trí tuệ nhân tạo."}` },
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
        setNotification({ type: "error", text: "Tài liệu này được bảo vệ chống sao chép." });
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
      setNotification({ type: "success", text: "Đã lưu điểm nhấn vào bộ sưu tập." });
    } catch (e) {
      setNotification({ type: "error", text: "Không thể lưu điểm nhấn." });
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white font-sans">
        <div className="flex flex-col items-center gap-6">
          <Loader2 className="w-12 h-12 animate-spin text-zinc-300" />
          <p className="text-[11px] font-bold text-zinc-400">Đang khởi tạo môi trường đọc tri thức</p>
        </div>
      </div>
    );
  }

  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-50/30 p-6 font-sans">
        <div className="bg-white p-12 w-full max-w-md border border-zinc-100 flex flex-col items-center text-center animate-in zoom-in-95 duration-500">
          <div className="w-16 h-16 bg-black flex items-center justify-center mb-10">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-black mb-3 tracking-tighter">Tài liệu được bảo vệ</h2>
          <p className="text-[11px] font-bold text-zinc-300 mb-10 leading-relaxed">
            Vui lòng nhập mật mã bảo mật để tiếp cận nội dung tài liệu này.
          </p>
          <div className="w-full space-y-4">
            <input
              type="password"
              placeholder=""
              className="w-full h-14 bg-zinc-50 border border-zinc-100 px-6 text-center text-sm font-bold focus:outline-none focus:border-black focus:bg-white transition-all placeholder:text-zinc-200"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchDocument(password)}
            />
            <button
              onClick={() => fetchDocument(password)}
              className="w-full h-14 bg-black text-white hover:bg-zinc-800 text-[11px] font-bold transition-all active:scale-[0.98]"
            >
              Xác thực truy cập
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-white p-6 font-sans">
        <AlertTriangle className="w-16 h-16 text-zinc-50 mb-8" />
        <p className="text-[11px] font-bold text-zinc-400 mb-10">{error}</p>
        <button
          onClick={() => router.back()}
          className="h-14 px-12 bg-black text-white text-[11px] font-bold transition-all active:scale-95"
        >
          Quay lại trang trước
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
        <div className="fixed top-20 right-8 z-[1000] w-80 animate-in slide-in-from-right-4 duration-300">
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
            className="bg-black text-white px-6 py-3 text-[11px] font-bold flex items-center gap-3 hover:bg-zinc-800 border border-black transition-all active:scale-95"
          >
            <Highlighter className="w-4 h-4" /> Làm nổi bật tri thức
          </button>
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-zinc-100 flex items-center justify-between px-8 bg-white shrink-0 z-50">
          <div className="flex items-center gap-6 min-w-0">
            <button
              onClick={() => router.back()}
              className="p-2.5 text-zinc-300 hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="h-4 w-px bg-zinc-100" />
            <h1 className="text-sm font-bold text-black tracking-tight truncate max-w-2xl">{document?.title}</h1>
            {document?.is_protected && (
                <div className="flex items-center gap-2 px-3 py-1 bg-zinc-50 border border-zinc-100 rounded-none">
                    <Lock className="w-3 h-3 text-black" />
                    <span className="text-[9px] font-bold uppercase tracking-widest text-black">Bảo vệ</span>
                </div>
            )}
          </div>
          <div className="flex items-center gap-6 shrink-0">
            {document?.file_url && document.file_url.toLowerCase().endsWith('.pdf') && (
                <div className="flex bg-zinc-50 p-1 border border-zinc-100">
                    <button 
                        onClick={() => setViewMode("text")}
                        className={`px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest transition-all ${viewMode === 'text' ? 'bg-black text-white' : 'text-zinc-300 hover:text-black'}`}
                    >
                        Góc nhìn trí tuệ
                    </button>
                    <button 
                        onClick={() => setViewMode("pdf")}
                        className={`px-4 py-1.5 text-[9px] font-bold uppercase tracking-widest transition-all ${viewMode === 'pdf' ? 'bg-black text-white' : 'text-zinc-300 hover:text-black'}`}
                    >
                        Tài liệu gốc
                    </button>
                </div>
            )}
            <div className="h-4 w-px bg-zinc-100 hidden md:block" />
            <button className="text-zinc-300 hover:text-black transition-all active:scale-90">
              <Bookmark className="w-5 h-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-zinc-50/20 scrollbar-thin">
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
                <div className="p-8 md:p-12 lg:p-24">
                    <div className="max-w-4xl mx-auto bg-white border border-zinc-100 p-12 md:p-20 lg:p-28 min-h-full relative animate-in slide-in-from-bottom-8 duration-1000">
                        <div className="prose prose-zinc max-w-none text-zinc-800 leading-relaxed text-lg">
                        {document?.content || document?.description || (
                            <div className="py-20 text-center space-y-6">
                                <Loader2 className="w-10 h-10 animate-spin text-zinc-100 mx-auto" />
                                <p className="text-[11px] font-bold text-zinc-300 uppercase tracking-widest">Đang trích xuất tri thức từ tài liệu</p>
                            </div>
                        )}
                        </div>
                        {document?.chapters &&
                        document.chapters.map((ch: any, idx: number) => (
                            <div key={idx} className="mt-24 pt-24 border-t border-zinc-50">
                            <h2 className="text-3xl font-bold text-black mb-12 tracking-tight">{ch.title}</h2>
                            <div className="prose prose-zinc max-w-none text-zinc-800 leading-loose text-lg">{ch.content}</div>
                            </div>
                        ))}

                        {highlights.length > 0 && (
                        <div className="absolute right-0 top-0 bottom-0 w-1 flex flex-col gap-1 pointer-events-none opacity-30">
                            {highlights.map((h, i) => (
                            <div key={i} className="w-full h-8 bg-zinc-100" title={h.text} />
                            ))}
                        </div>
                        )}
                    </div>
                </div>
            )}
        </main>
      </div>

      <div className="w-[440px] border-l border-zinc-100 flex flex-col bg-white hidden xl:flex z-50">
        <div className="p-8 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/10">
          <div className="flex gap-6">
            <button
              onClick={() => setSidebarTab("chat")}
              className={`flex items-center gap-3 text-[11px] font-bold transition-all ${
                sidebarTab === "chat" ? "text-black" : "text-zinc-200 hover:text-black"
              }`}
            >
              <Sparkles className="w-4 h-4" /> Cố vấn AI
            </button>
            <button
              onClick={() => setSidebarTab("highlights")}
              className={`flex items-center gap-3 text-[11px] font-bold transition-all ${
                sidebarTab === "highlights" ? "text-black" : "text-zinc-200 hover:text-black"
              }`}
            >
              <Highlighter className="w-4 h-4" /> Điểm nhấn ({highlights.length})
            </button>
          </div>
          <button
            onClick={() => setUsePro(!usePro)}
            className={`px-4 py-2 text-[9px] font-bold border transition-all active:scale-95 ${
              usePro ? "bg-black text-white border-black" : "bg-white text-zinc-300 border-zinc-100 hover:border-black hover:text-black"
            }`}
          >
            Chế độ chuyên nghiệp
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-10 scrollbar-thin">
          {sidebarTab === "chat" ? (
            <div className="space-y-10">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-8 py-24">
                  <div className="w-20 h-20 bg-zinc-50 flex items-center justify-center border border-zinc-100 group">
                    <MessageSquare className="w-10 h-10 text-zinc-100 group-hover:text-black transition-all" />
                  </div>
                  <div className="space-y-2">
                    <p className="text-[11px] font-bold text-zinc-400">Trí tuệ nhân tạo sẵn sàng</p>
                    <p className="text-[10px] text-zinc-300 leading-relaxed font-medium">
                      Tương tác để giải mã sâu hơn những tầng tri thức ẩn giấu trong văn bản này.
                    </p>
                  </div>
                </div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-6 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                  <div
                    className={`w-10 h-10 shrink-0 flex items-center justify-center border ${
                      msg.role === "user" ? "bg-zinc-50 border-zinc-100" : "bg-black border-black text-white"
                    }`}
                  >
                    {msg.role === "user" ? <User className="w-5 h-5 text-zinc-200" /> : <Bot className="w-5 h-5" />}
                  </div>
                  <div
                    className={`text-[13px] leading-relaxed p-6 border ${
                      msg.role === "user" ? "bg-zinc-50/20 border-zinc-50 text-zinc-500" : "bg-white border-zinc-100 text-black font-medium"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          ) : (
            <div className="space-y-8">
              {highlights.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-8 py-24 opacity-50">
                  <Highlighter className="w-16 h-16 text-zinc-50" />
                  <p className="text-[11px] font-bold text-zinc-300">Chưa có nội dung nào được làm nổi bật</p>
                </div>
              ) : (
                highlights.map((h, i) => (
                  <div
                    key={i}
                    className="p-8 border border-zinc-100 bg-zinc-50/10 hover:border-black transition-all duration-500 group"
                  >
                    <p className="text-[13px] leading-relaxed text-black font-medium mb-6 italic">"{h.text}"</p>
                    <div className="flex justify-between items-center border-t border-zinc-50 pt-6">
                      <span className="text-[10px] font-bold text-zinc-300">
                        {new Date(h.created_at).toLocaleDateString("vi-VN")}
                      </span>
                      <button className="text-[10px] font-bold text-zinc-200 hover:text-black transition-colors opacity-0 group-hover:opacity-100">
                        Xóa bỏ
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="p-10 border-t border-zinc-100 bg-white">
          <div className="relative group">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleAskAI())}
              placeholder=""
              className="w-full min-h-[140px] p-8 text-sm font-medium border border-zinc-100 rounded-none focus:outline-none focus:border-black focus:bg-zinc-50/10 transition-all resize-none placeholder:text-zinc-200"
              disabled={asking}
            />
            <button
              onClick={handleAskAI}
              disabled={asking || !question.trim()}
              className="absolute bottom-6 right-6 h-12 w-12 bg-black text-white hover:bg-zinc-800 flex items-center justify-center transition-all active:scale-90 disabled:opacity-50"
            >
              {asking ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
          <div className="mt-6 flex items-center justify-center gap-3 text-[10px] font-bold text-zinc-200">
            <Info className="w-3.5 h-3.5" /> Hệ thống AI có thể đưa ra câu trả lời chưa chính xác
          </div>
        </div>
      </div>
    </div>
  );
}
