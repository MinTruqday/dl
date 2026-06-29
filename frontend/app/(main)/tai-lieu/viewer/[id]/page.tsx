"use client";

import { useToast } from "@/shared/contexts/ToastContext";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken, API_URL } from "@/features/auth/services/user_authentication.service";
import { queryRagAPI, translateTextAPI } from "@/features/ai/services/agentic_ai.service";
import { createHighlightAPI, getHighlightsAPI, deleteHighlightAPI } from "@/features/content/services/text_highlight.service";
import { toggleBookmarkAPI, getBookmarksAPI } from "@/features/content/services/document_bookmark.service";
import { Lock, AlertTriangle, Send, ArrowLeft, Loader2, User, Bot, Highlighter, Bookmark, Zap, Trash2, BookmarkCheck, ZoomIn, ZoomOut, Columns, Square, Languages, BookOpen, History, Maximize2, Minimize2, Paperclip, Edit2, X, FileText, Image as ImageIcon, Folder } from "lucide-react";
import PageLoader from "@/shared/components/common/PageLoader";

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
  const [sidebarTab, setSidebarTab] = useState<"chat" | "highlights" | "thumbnails" | "history" | "zip">("chat");
  const [readingMode, setReadingMode] = useState<"single" | "double">("single");
  const [zoom, setZoom] = useState(100);
  const [currentPage, setCurrentPage] = useState(1);
  const [isExpanded, setIsExpanded] = useState(false);

  const [zipTree, setZipTree] = useState<any[]>([]);
  const [selectedZipFile, setSelectedZipFile] = useState<{ name: string; content: string; type: string; } | null>(null);
  const [zipLoading, setZipLoading] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [selection, setSelection] = useState<{ text: string; x: number; y: number; } | null>(null);
  const [translating, setTranslating] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [showAttachments, setShowAttachments] = useState(false);

  const fetchHighlights = useCallback(async () => {
    try {
      const res = await getHighlightsAPI(id);
      setHighlights(Array.isArray(res) ? res : res.data || []);
    } catch { showToast("Không thể đồng bộ nêu bật", "error"); }
  }, [id, showToast]);

  const checkBookmarkStatus = useCallback(async () => {
    try {
      const bookmarks = await getBookmarksAPI();
      if (bookmarks?.data) setIsBookmarked(bookmarks.data.some((b: any) => (b.id || b._id) === id));
    } catch {}
  }, [id]);

  const fetchDocument = useCallback(async (pwd?: string) => {
    setLoading(true);
    try {
      const token = getToken();
      if (!token) { router.push("/dang-nhap"); return; }
      const headers: any = { Authorization: `Bearer ${token}` };
      if (pwd) headers["x-document-password"] = pwd;
      const res = await fetch(`${API_URL}/tai-lieu/${id}`, { headers });
      if (res.status === 401) { router.push("/dang-nhap"); return; }
      if (res.status === 403) { setIsLocked(true); setLoading(false); return; }
      if (res.ok) {
        const data = await res.json();
        setDocument(data.data || data);
        setIsLocked(false);
        const bookmarks = await getBookmarksAPI();
        if (bookmarks?.data) setIsBookmarked(bookmarks.data.some((b: any) => (b.id || b._id) === (data.data?.id || data.data?._id || id)));
        if (data.data?.content_format === "zip" && data.data?.file_url) {
          setSidebarTab("zip");
          fetch(`${API_URL}/doc-sach/tree-zip?file_url=${encodeURIComponent(data.data.file_url)}`)
            .then(r => r.json()).then(res => setZipTree(res.data || [])).catch(console.error);
        }
      } else setError("Quyền truy cập của bạn bị giới hạn đối với tài liệu này");
    } catch { setError("Mất kết nối với hệ thống"); } finally { setLoading(false); }
  }, [id, router]);

  const fetchSessions = useCallback(async () => {
    try {
      const token = getToken();
      const res = await fetch(`${API_URL}/lich-su?document_id=${id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setSessions(data.data || []); }
    } catch { showToast("Không thể đồng bộ lịch sử", "error"); }
  }, [id, showToast]);

  useEffect(() => { fetchDocument(); fetchHighlights(); checkBookmarkStatus(); fetchSessions(); }, [fetchDocument, fetchHighlights, checkBookmarkStatus, fetchSessions]);

  useEffect(() => {
    if (!document?.drm_settings?.disable_copy) return;
    const prevent = (e: Event) => e.preventDefault();
    window.addEventListener("contextmenu", prevent); window.addEventListener("copy", prevent); window.addEventListener("selectstart", prevent);
    return () => { window.removeEventListener("contextmenu", prevent); window.removeEventListener("copy", prevent); window.removeEventListener("selectstart", prevent); };
  }, [document]);

  useEffect(() => { if (!loading) requestAnimationFrame(() => setVisible(true)); }, [loading]);

  useEffect(() => {
    if (!document) return;
    if (document.content_fragments && Array.isArray(document.content_fragments)) {
      const decrypt = async () => {
        try {
          const token = getToken();
          const keyRes = await fetch(`${API_URL}/tai-lieu/${document._id || document.id || id}/khoa-giai-ma`, { headers: { Authorization: `Bearer ${token}` } });
          if (!keyRes.ok) throw new Error();
          const keyData = await keyRes.json();
          const keyRaw = atob(keyData.data.key);
          const keyBytes = new Uint8Array(keyRaw.length);
          for (let i = 0; i < keyRaw.length; i++) keyBytes[i] = keyRaw.charCodeAt(i);
          const cryptoKey = await window.crypto.subtle.importKey("raw", keyBytes, { name: "AES-GCM" }, false, ["decrypt"]);
          let fullText = "";
          for (const frag of document.content_fragments) {
            const fragRaw = atob(frag);
            const fragBytes = new Uint8Array(fragRaw.length);
            for (let i = 0; i < fragRaw.length; i++) fragBytes[i] = fragRaw.charCodeAt(i);
            fullText += new TextDecoder().decode(await window.crypto.subtle.decrypt({ name: "AES-GCM", iv: fragBytes.slice(0, 12) }, cryptoKey, fragBytes.slice(12)));
          }
          setDecryptedContent(fullText);
        } catch { setDecryptedContent("Lỗi giải mã hoặc chứng thực bảo mật không thành công. Hãy thử tải lại trang."); }
      };
      decrypt();
    } else setDecryptedContent(document.content || document.description || "Không có nội dung hiển thị");
  }, [document, id]);

  useEffect(() => { if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleAskAI = async (retryText?: string) => {
    const textToSubmit = retryText || question.trim();
    if (!textToSubmit) return;
    setAsking(true);
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const token = getToken();
        const res = await fetch(`${API_URL}/lich-su`, { method: "POST", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ document_id: id, first_query: textToSubmit }) });
        if (res.ok) { const data = await res.json(); sessionId = data.data._id; setCurrentSessionId(sessionId); fetchSessions(); }
      } catch { showToast("Không thể khởi tạo phiên làm việc", "error"); setAsking(false); return; }
    }
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: textToSubmit }]);
    setQuestion("");
    try {
      const res: any = await Promise.race([queryRagAPI(id, textToSubmit, useSmart, sessionId || undefined), new Promise((_, r) => setTimeout(() => r(new Error("AI_TIMEOUT")), 20000))]);
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: res.data?.answer || res.answer || "Không thể trích xuất phản hồi." }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: "assistant", content: e.message === "AI_TIMEOUT" ? "Phản hồi chậm hơn dự kiến, vui lòng thử lại." : `Lỗi: ${e.message || "Không thể kết nối"}` }]);
    } finally { setAsking(false); }
  };

  const handleEditAndResend = (msgId: string, newText: string) => { setMessages(prev => prev.filter(m => parseInt(m.id) < parseInt(msgId))); handleAskAI(newText); setEditingMessageId(null); };

  const handleTextSelection = () => {
    if (document?.is_protected) return;
    const sel = window.getSelection();
    if (sel && sel.toString().trim().length > 0) {
      const rect = sel.getRangeAt(0).getBoundingClientRect();
      setSelection({ text: sel.toString(), x: rect.left + rect.width / 2, y: rect.top + window.scrollY - 50 });
    } else setSelection(null);
  };

  const handleTranslate = async () => {
    if (!selection) return;
    setTranslating(true);
    try {
      const res = await translateTextAPI(selection.text, "vi");
      showToast(res.data?.translated_text || res.translated_text, "success");
      setSelection(null);
    } catch { showToast("Không thể dịch thuật", "error"); } finally { setTranslating(false); }
  };

  const saveHighlight = async () => {
    if (!selection) return;
    try {
      await createHighlightAPI(id, selection.text, "#F5F5F7");
      fetchHighlights(); setSelection(null); window.getSelection()?.removeAllRanges();
      showToast("Đã lưu nêu bật", "success");
    } catch { showToast("Không thể lưu nêu bật", "error"); }
  };

  const deleteHighlightItem = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      setHighlights(prev => prev.filter(h => (h.id || h._id) !== highlightId));
      showToast("Đã xóa nêu bật", "success");
    } catch { showToast("Không thể xóa nêu bật", "error"); }
  };

  const toggleBookmark = async () => {
    try {
      await toggleBookmarkAPI(id);
      setIsBookmarked(!isBookmarked);
      showToast(isBookmarked ? "Đã gỡ khỏi dấu trang" : "Đã thêm vào dấu trang", "success");
    } catch { showToast("Cập nhật dấu trang thất bại", "error"); }
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
      const fontSize = 16, lineHeight = 1.6, padding = 0;
      let totalHeight = padding * 2;
      ctx.font = `400 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
      const paragraphs = text.split("\n");
      const wrapText = (t: string, maxW: number) => {
        const words = t.split(" "), lines = [];
        let current = words[0];
        for (let i = 1; i < words.length; i++) {
          if (ctx.measureText(current + " " + words[i]).width < maxW) current += " " + words[i];
          else { lines.push(current); current = words[i]; }
        }
        lines.push(current); return lines;
      };
      paragraphs.forEach(p => {
        if (!p.trim()) { totalHeight += fontSize * lineHeight; return; }
        totalHeight += wrapText(p, width - padding * 2).length * fontSize * lineHeight + fontSize;
      });
      canvasRef.current.width = width * dpr; canvasRef.current.height = totalHeight * dpr;
      canvasRef.current.style.width = `${width}px`; canvasRef.current.style.height = `${totalHeight}px`;
      ctx.scale(dpr, dpr); ctx.fillStyle = "#1D1D1F"; ctx.textBaseline = "top";
      ctx.font = `400 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`;
      let y = padding;
      paragraphs.forEach(p => {
        if (!p.trim()) { y += fontSize * lineHeight; return; }
        wrapText(p, width - padding * 2).forEach(line => { ctx.fillText(line, padding, y); y += fontSize * lineHeight; });
        y += fontSize;
      });
    }, [text, readingMode, zoom]);
    return <div ref={containerRef} className="w-full relative select-none"><canvas ref={canvasRef} className="block w-full select-none" /><div className="absolute inset-0 z-10" onContextMenu={e => e.preventDefault()} /></div>;
  };

  const getPageContent = () => {
    if (document?.content_format === "zip") {
      return (
        <div className="w-full h-full flex flex-col bg-[#F5F5F7] border-[#E8E8ED] rounded-[24px] overflow-hidden">
          <div className="h-14 border-b border-[#E8E8ED] bg-[#F5F5F7] flex items-center px-6 shrink-0">
            <FileText className="w-4 h-4 mr-3 text-[#6E6E73]" />
            <span className="text-[13px] font-medium text-[#1D1D1F]">{selectedZipFile ? selectedZipFile.name : "Trình duyệt mã nguồn ZIP"}</span>
          </div>
          <div className="flex-1 overflow-auto p-6 bg-white">
            {zipLoading ? <div className="flex h-full items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-[#0071E3]" /></div> : selectedZipFile ? (
              selectedZipFile.type === "text" ? <pre className="text-[13px] font-mono text-[#1D1D1F] whitespace-pre-wrap leading-relaxed bg-[#F5F5F7] p-6 rounded-[18px] border border-[#E8E8ED]">{selectedZipFile.content}</pre> : <div className="flex h-full flex-col items-center justify-center text-[#6E6E73]"><AlertTriangle className="w-12 h-12 mb-4 text-[#C7C7CC]" /><p className="text-[13px]">Định dạng không được hỗ trợ hiển thị</p></div>
            ) : <div className="flex h-full flex-col items-center justify-center text-[#6E6E73]"><Folder className="w-12 h-12 mb-4 text-[#C7C7CC]" /><p className="text-[13px]">Chọn tệp để xem mã nguồn</p></div>}
          </div>
        </div>
      );
    }
    if (readingMode === "double") return <div className="prose max-w-none text-[#1D1D1F] leading-relaxed text-[15px] whitespace-pre-wrap" style={{ columnCount: 2, columnGap: "4rem" }}><CanvasRenderer text={decryptedContent} /></div>;
    return <div className="prose max-w-none text-[#1D1D1F] leading-relaxed text-[15px] whitespace-pre-wrap"><CanvasRenderer text={decryptedContent} /></div>;
  };

  if (isLocked) return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F7] font-sans px-6">
      <div className="bg-[#F5F5F7] p-10 w-full max-w-[400px] border-[#E8E8ED] flex flex-col items-center text-center rounded-[24px]">
        <div className="w-20 h-20 bg-[#F5F5F7] flex items-center justify-center mb-6 rounded-full"><Lock className="w-8 h-8 text-[#0071E3]" /></div>
        <h2 className="text-[20px] font-semibold text-[#1D1D1F] mb-2">Thực thể bảo mật</h2>
        <p className="text-[15px] text-[#6E6E73] mb-8">Nhập mã định danh để tiếp cận dữ liệu</p>
        <div className="w-full space-y-4">
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === "Enter" && fetchDocument(password)} placeholder="Nhập mã bảo mật" className="w-full h-[52px] bg-[#F5F5F7] border border-transparent px-4 text-center text-[15px] focus:outline-none focus:border-[#0071E3] focus:bg-white rounded-[14px] transition-all" />
          <button onClick={() => fetchDocument(password)} className="w-full h-[52px] bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors">Xác thực quyền truy cập</button>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#F5F5F7] font-sans px-6">
      <AlertTriangle className="w-16 h-16 text-[#FF3B30] mb-6" />
      <p className="text-[15px] text-[#1D1D1F] mb-8">{error}</p>
      <button onClick={() => router.back()} className="h-[44px] px-8 bg-[#0071E3] text-white text-[15px] font-medium rounded-full hover:bg-[#0077ED] transition-colors">Quay lại</button>
    </div>
  );

  return (
    <div className={`flex h-screen bg-[#F5F5F7] overflow-hidden font-sans ${document?.is_protected ? "select-none" : ""}`} onMouseUp={handleTextSelection}>
      <div className="w-[72px] border-r border-[#E8E8ED] bg-white flex flex-col items-center py-6 gap-6 shrink-0 z-50 shadow-sm">
        <button onClick={() => setSidebarTab("chat")} className={`p-3 rounded-xl transition-colors ${sidebarTab === "chat" ? "bg-[#0071E3] text-white shadow-md" : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}><Bot className="w-6 h-6" /></button>
        <button onClick={() => setSidebarTab("highlights")} className={`p-3 rounded-xl transition-colors ${sidebarTab === "highlights" ? "bg-[#0071E3] text-white shadow-md" : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}><Highlighter className="w-6 h-6" /></button>
        <button onClick={() => setSidebarTab("thumbnails")} className={`p-3 rounded-xl transition-colors ${sidebarTab === "thumbnails" ? "bg-[#0071E3] text-white shadow-md" : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}><BookOpen className="w-6 h-6" /></button>
        <button onClick={() => setSidebarTab("history")} className={`p-3 rounded-xl transition-colors ${sidebarTab === "history" ? "bg-[#0071E3] text-white shadow-md" : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}><History className="w-6 h-6" /></button>
        {document?.content_format === "zip" && <button onClick={() => setSidebarTab("zip")} className={`p-3 rounded-xl transition-colors ${sidebarTab === "zip" ? "bg-[#0071E3] text-white shadow-md" : "text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]"}`}><Folder className="w-6 h-6" /></button>}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-[60px] border-b border-[#E8E8ED] flex items-center justify-between px-6 bg-white/90 backdrop-blur-md shadow-sm shrink-0 z-40">
          <div className="flex items-center gap-4 flex-1">
            <button onClick={() => router.back()} className="p-2 text-[#6E6E73] rounded-full hover:bg-[#F5F5F7] hover:text-[#1D1D1F] transition-colors"><ArrowLeft className="w-5 h-5" /></button>
            <h1 className="text-[15px] font-semibold text-[#1D1D1F] truncate max-w-xs md:max-w-md">{document?.title}</h1>
          </div>
          <div className="flex-1 flex justify-center text-[13px] font-medium text-[#6E6E73]">Trang {currentPage} / 1 (100%)</div>
          <div className="flex items-center justify-end gap-6 flex-1">
            <div className="flex items-center gap-2">
              <button onClick={() => changeZoom(-10)} className="p-2 text-[#6E6E73] rounded-full hover:bg-[#F5F5F7] transition-colors"><ZoomOut className="w-5 h-5" /></button>
              <span className="text-[13px] font-medium text-[#1D1D1F] min-w-[3rem] text-center">{zoom}%</span>
              <button onClick={() => changeZoom(10)} className="p-2 text-[#6E6E73] rounded-full hover:bg-[#F5F5F7] transition-colors"><ZoomIn className="w-5 h-5" /></button>
            </div>
            <div className="w-px h-6 bg-[#E8E8ED]" />
            <div className="flex items-center gap-1 bg-[#F5F5F7] p-1 rounded-full">
              <button onClick={() => setReadingMode("single")} className={`p-1.5 rounded-full transition-colors ${readingMode === "single" ? "text-[#1D1D1F] bg-white shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><Square className="w-4 h-4" /></button>
              <button onClick={() => setReadingMode("double")} className={`p-1.5 rounded-full transition-colors ${readingMode === "double" ? "text-[#1D1D1F] bg-white shadow-sm" : "text-[#6E6E73] hover:text-[#1D1D1F]"}`}><Columns className="w-4 h-4" /></button>
            </div>
            <div className="w-px h-6 bg-[#E8E8ED]" />
            <button onClick={toggleBookmark} className={`p-2 rounded-full transition-colors ${isBookmarked ? "text-[#0071E3]" : "text-[#6E6E73] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"}`}>{isBookmarked ? <BookmarkCheck className="w-5 h-5" /> : <Bookmark className="w-5 h-5" />}</button>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-[#F5F5F7] p-6 md:p-8 relative flex justify-center custom-scrollbar">
          <div className={`mx-auto bg-[#F5F5F7] border-[#E8E8ED] ${document?.content_format === "zip" ? "p-0 h-full max-w-full rounded-[24px]" : "p-12 md:p-16 min-h-full origin-top rounded-[24px]"} transition-transform duration-300 ${readingMode === "double" && document?.content_format !== "zip" ? "w-full max-w-5xl" : document?.content_format !== "zip" ? "w-full max-w-3xl" : "w-full h-full"}`} style={{ transform: document?.content_format === "zip" ? "none" : `scale(${zoom / 100})` }}>
            {getPageContent()}
          </div>
          {selection && (
            <div className="fixed z-50 flex gap-2 bg-[#F5F5F7]/90 backdrop-blur-md p-2 border-[#E8E8ED] rounded-[18px] transition-all" style={{ left: selection.x, top: selection.y, transform: "translateX(-50%)" }}>
              <button onClick={saveHighlight} className="p-2 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-full transition-colors"><Highlighter className="w-5 h-5" /></button>
              <button onClick={handleTranslate} disabled={translating} className="p-2 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-full transition-colors">{translating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Languages className="w-5 h-5" />}</button>
              <button className="p-2 text-[#6E6E73] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-full transition-colors"><Zap className="w-5 h-5" /></button>
            </div>
          )}
        </main>
      </div>

      <div className={`${isExpanded ? "w-[480px]" : "w-[360px]"} border-l border-[#E8E8ED] bg-white flex flex-col shrink-0 z-50 transition-all duration-300 shadow-sm`}>
        <div className="h-[60px] border-b border-[#E8E8ED] flex items-center px-6 justify-between shrink-0">
          <span className="text-[15px] font-semibold text-[#1D1D1F]">{sidebarTab === "chat" ? "Cố vấn AI" : sidebarTab === "highlights" ? "Nêu bật" : sidebarTab === "history" ? "Lịch sử" : sidebarTab === "zip" ? "Mã nguồn ZIP" : "Mục lục"}</span>
          {sidebarTab === "chat" && <button onClick={() => setIsExpanded(!isExpanded)} className="p-2 text-[#6E6E73] rounded-full hover:bg-[#F5F5F7] transition-colors">{isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}</button>}
        </div>

        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white">
          {sidebarTab === "chat" ? (
            <div className="space-y-6">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} group`}>
                  <div className={`w-10 h-10 shrink-0 flex items-center justify-center rounded-full shadow-sm ${msg.role === "user" ? "bg-[#F5F5F7] border border-[#E8E8ED]" : "bg-[#0071E3] text-white"}`}>{msg.role === "user" ? <User className="w-5 h-5 text-[#6E6E73]" /> : <Bot className="w-5 h-5" />}</div>
                  <div className="flex flex-col gap-2 max-w-[80%]">
                    <div className={`text-[15px] leading-relaxed p-4 rounded-[20px] shadow-sm relative ${msg.role === "user" ? "bg-[#0071E3] text-white rounded-tr-[4px]" : "bg-[#F5F5F7] text-[#1D1D1F] rounded-tl-[4px]"}`}>
                      {msg.content}
                      {msg.role === "user" && !asking && <button onClick={() => setEditingMessageId(msg.id)} className="absolute -left-12 top-1 opacity-0 group-hover:opacity-100 p-2 text-[#6E6E73] rounded-full hover:bg-[#E8E8ED] transition-all"><Edit2 className="w-4 h-4" /></button>}
                    </div>
                    {editingMessageId === msg.id && (
                      <div className="flex flex-col gap-3 mt-2">
                        <textarea defaultValue={msg.content} className="w-full p-4 text-[15px] border border-[#0071E3] rounded-[18px] outline-none" onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleEditAndResend(msg.id, e.currentTarget.value))} />
                        <div className="flex justify-end gap-2"><button onClick={() => setEditingMessageId(null)} className="px-4 py-2 text-[13px] font-medium text-[#6E6E73] hover:bg-[#F5F5F7] rounded-full">Hủy bỏ</button><button onClick={e => handleEditAndResend(msg.id, (e.currentTarget.previousElementSibling as HTMLTextAreaElement).value)} className="px-4 py-2 bg-[#0071E3] text-white text-[13px] font-medium rounded-full">Cập nhật</button></div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
          ) : sidebarTab === "highlights" ? (
            <div className="space-y-4">
              {!highlights.length ? <div className="py-12 text-center text-[#6E6E73]"><Highlighter className="w-10 h-10 mx-auto mb-4 text-[#C7C7CC]" /><p className="text-[13px] font-medium">Chưa có nêu bật nào</p></div> : highlights.map((h, i) => (
                <div key={i} className="p-5 border border-[#E8E8ED] bg-[#F5F5F7] rounded-[18px] group"><p className="text-[15px] text-[#1D1D1F] mb-4 italic pl-4 border-l-2 border-[#0071E3]">"{h.text}"</p><div className="flex justify-between items-center"><span className="text-[12px] text-[#6E6E73]">{new Date(h.created_at).toLocaleDateString("vi-VN")}</span><button onClick={() => deleteHighlightItem(h.id || h._id)} className="p-2 text-[#6E6E73] hover:text-[#FF3B30] hover:bg-[#FFEBEB] rounded-full"><Trash2 className="w-4 h-4" /></button></div></div>
              ))}
            </div>
          ) : sidebarTab === "history" ? (
            <div className="space-y-4">
              {!sessions.length ? <div className="py-12 text-center text-[#6E6E73]"><History className="w-10 h-10 mx-auto mb-4 text-[#C7C7CC]" /><p className="text-[13px] font-medium">Chưa có lịch sử hội thoại</p></div> : sessions.map((s) => (
                <div key={s._id} onClick={() => { setCurrentSessionId(s._id); setSidebarTab("chat"); }} className={`p-5 border cursor-pointer rounded-[18px] relative ${currentSessionId === s._id ? "border-[#0071E3] bg-[#EBF4FF]" : "border-[#E8E8ED] bg-[#F5F5F7]"}`}><p className="text-[15px] font-medium text-[#1D1D1F] pr-8">{s.title}</p><p className="text-[12px] text-[#6E6E73] mt-2">{new Date(s.updated_at).toLocaleDateString("vi-VN")}</p></div>
              ))}
            </div>
          ) : sidebarTab === "zip" ? (
            <div className="space-y-1 text-[13px] bg-[#F5F5F7] p-4 rounded-[18px] min-h-[400px]">
              {zipTree.map((item, i) => (
                <div key={i} onClick={() => { if (!item.is_dir) { setZipLoading(true); fetch(`${API_URL}/doc-sach/content-zip?file_url=${encodeURIComponent(document?.file_url)}&path=${encodeURIComponent(item.path)}`).then(r => r.json()).then(res => setSelectedZipFile({ name: item.name, content: res.data?.content || "", type: res.data?.type || "text" })).catch(() => showToast("Lỗi", "error")).finally(() => setZipLoading(false)); } }} className={`flex items-center gap-2 px-3 py-2 cursor-pointer rounded-[10px] ${!item.is_dir && selectedZipFile?.name === item.name ? "bg-[#0071E3] text-white" : "text-[#1D1D1F] hover:bg-[#E8E8ED]"}`} style={{ paddingLeft: `${(item.path.split("/").length - 1) * 16 + 12}px` }}>{item.is_dir ? <Folder className="w-4 h-4" /> : <FileText className="w-4 h-4" />} <span className="truncate">{item.name}</span></div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">{Array.from({ length: totalPages }, (_, i) => i + 1).map(p => <div key={p} onClick={() => setCurrentPage(p)} className={`aspect-[3/4] border flex flex-col items-center justify-center gap-2 cursor-pointer rounded-[18px] ${currentPage === p ? "bg-[#0071E3] text-white" : "bg-[#F5F5F7] border-[#E8E8ED] text-[#1D1D1F]"}`}><span className="text-[20px] font-semibold">{p}</span><span className="text-[12px]">Trang</span></div>)}</div>
          )}
        </div>

        {sidebarTab === "chat" && (
          <div className="p-6 border-t border-[#E8E8ED] bg-white shrink-0">
            <div className="relative">
              <textarea value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleAskAI())} className="w-full min-h-[120px] p-4 pb-16 text-[15px] bg-[#F5F5F7] border border-transparent focus:bg-white focus:border-[#0071E3] resize-none rounded-[18px] text-[#1D1D1F] placeholder:text-[#6E6E73] outline-none" placeholder="Hỏi AI về tài liệu..." disabled={asking} />
              <div className="absolute bottom-4 left-4"><button className="w-10 h-10 flex items-center justify-center text-[#6E6E73] bg-white border border-[#E8E8ED] hover:bg-[#F5F5F7] rounded-full shadow-sm"><Paperclip className="w-5 h-5" /></button></div>
              <button onClick={() => handleAskAI()} disabled={asking || !question.trim()} className="absolute bottom-4 right-4 w-10 h-10 bg-[#0071E3] text-white flex items-center justify-center disabled:opacity-50 rounded-full shadow-sm hover:bg-[#0077ED]"><Send className="w-4 h-4" /></button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
