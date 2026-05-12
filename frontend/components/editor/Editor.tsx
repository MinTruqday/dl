"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import { useToast } from "@/contexts/ToastContext";
import { 
    compilePreviewAPI, 
    globalFindReplaceAPI, 
    getAiSuggestionsAPI,
    addInlineCommentAPI,
    getVersionDiffAPI
} from "@/services/editor.service";
import { grammarCheckAPI, getSynonymsAPI } from "@/services/inference.service";
import { Sparkles, CheckSquare, FileText, Download, Loader2, Maximize2, Minimize2, MessageSquare, History, Wand2, X, Brain } from "lucide-react";
import AIToolsModal from "./AIToolsModal";

export default function Editor({
  documentId,
  initialContent,
  onSave,
}: {
  documentId?: string;
  initialContent?: string;
  onSave?: (data: string) => void;
}) {
  const editorRef = useRef<EditorJS | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isZenMode, setIsZenMode] = useState(false);
  const [isAiToolsOpen, setIsAiToolsOpen] = useState(false);
  const [activeSidebar, setActiveSidebar] = useState<"none" | "comments" | "history">("none");
  const [sidebarData, setSidebarData] = useState<any[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);
  const [stats, setStats] = useState({ wpm: 0, charCount: 0, goalProgress: 0 });
  const [lastKeystroke, setLastKeystroke] = useState<number>(Date.now());
  const lastContentRef = useRef<string>(initialContent || "");
  const { showToast } = useToast();

  useEffect(() => {
    if (!containerRef.current) return;

    const holderDiv = document.createElement("div");
    holderDiv.className = "prose prose-zinc max-w-4xl mx-auto min-h-full";
    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(holderDiv);

    let cancelled = false;

    const init = async () => {
      const EditorJSModule = (await import("@editorjs/editorjs")).default;
      const Header = (await import("@editorjs/header")).default;
      const Paragraph = (await import("@editorjs/paragraph")).default;
      const ListTool = (await import("@editorjs/list")).default;
      const Quote = (await import("@editorjs/quote")).default;
      const Warning = (await import("@editorjs/warning")).default;
      const Marker = (await import("@editorjs/marker")).default;
      const CodeTool = (await import("@editorjs/code")).default;
      const Delimiter = (await import("@editorjs/delimiter")).default;
      const InlineCode = (await import("@editorjs/inline-code")).default;
      const Embed = (await import("@editorjs/embed")).default;
      const Table = (await import("@editorjs/table")).default;
      const SimpleImage = (await import("@editorjs/simple-image")).default;
      const RawTool = (await import("@editorjs/raw")).default;
      const UnderlineTool = (await import("@editorjs/underline")).default;

      if (cancelled) {
        holderDiv.remove();
        return;
      }

      let data: OutputData = { blocks: [{ type: "paragraph", data: { text: "" } }] };
      if (initialContent) {
        try {
          const parsed = JSON.parse(initialContent);
          if (parsed.blocks && parsed.blocks.length > 0) data = parsed;
        } catch {
          data = { blocks: [{ type: "paragraph", data: { text: initialContent } }] };
        }
      }

      const tools: Record<string, any> = {};
      if (Header) tools.header = { class: Header, inlineToolbar: true };
      if (Paragraph) tools.paragraph = { class: Paragraph, inlineToolbar: true };
      if (ListTool) tools.list = { class: ListTool, inlineToolbar: true };
      if (Quote) tools.quote = { class: Quote, inlineToolbar: true };
      if (Warning) tools.warning = Warning;
      if (Marker) tools.marker = Marker;
      if (CodeTool) tools.code = CodeTool;
      if (Delimiter) tools.delimiter = Delimiter;
      if (InlineCode) tools.inlineCode = InlineCode;
      if (Embed) tools.embed = Embed;
      if (Table) tools.table = Table;
      if (SimpleImage) tools.image = SimpleImage;
      if (RawTool) tools.raw = RawTool;
      if (UnderlineTool) tools.underline = UnderlineTool;

      const editor = new EditorJSModule({
        holder: holderDiv,
        tools,
        data,
        placeholder: "Bắt đầu soạn thảo",
        onChange: async () => {
          try {
            const saved = await editor.save();
            const text = saved.blocks.map(b => b.data?.text || "").join(" ");
            const words = text.trim().split(/\s+/).length;
            setStats(prev => ({ 
                ...prev, 
                charCount: text.length,
                wpm: Math.round((words / ((Date.now() - lastKeystroke) / 60000)) || 0)
            }));
            setLastKeystroke(Date.now());
            const val = JSON.stringify(saved);
            lastContentRef.current = val;
            onSave?.(val);
          } catch {}
        },
      });

      if (!cancelled) {
        editorRef.current = editor;
      } else {
        editor.isReady.then(() => editor.destroy()).catch(() => {});
        holderDiv.remove();
      }
    };

    init();

    return () => {
      cancelled = true;
      if (editorRef.current) {
        const instance = editorRef.current;
        editorRef.current = null;
        instance.isReady.then(() => instance.destroy()).catch(() => {});
      }
      holderDiv.remove();
    };
  }, []);

  useEffect(() => {
    if (!editorRef.current || !initialContent || initialContent === lastContentRef.current) return;
    
    lastContentRef.current = initialContent;
    editorRef.current.isReady.then(() => {
      let data: OutputData;
      try {
        data = JSON.parse(initialContent);
        if (!data.blocks || data.blocks.length === 0) {
          data = { blocks: [{ type: "paragraph", data: { text: "" } }] };
        } else {
            data.blocks = data.blocks.map(b => {
                if (b.type === "paragraph" && !b.data) b.data = { text: "" };
                if (b.type === "paragraph" && b.data && typeof b.data.text !== "string") b.data.text = String(b.data.text || "");
                return b;
            });
        }
      } catch {
        data = { blocks: [{ type: "paragraph", data: { text: initialContent } }] };
      }
      editorRef.current?.render(data);
    }).catch(() => {});
  }, [initialContent]);

  const handleGrammarCheck = async () => {
    if (!editorRef.current) return;
    try {
      const data = await editorRef.current.save();
      let text = "";
      data.blocks.forEach((b: any) => {
        if (b.data?.text) text += b.data.text + " ";
      });
      if (!text || text.length < 50) {
        showToast("Vui lòng viết thêm nội dung để kiểm tra ngữ pháp", "info");
        return;
      }
      showToast("Đang phân tích ngữ pháp bằng AI", "info");
      const res = await grammarCheckAPI(text);
      showToast(`Kết quả AI: ${res.message} (Điểm: ${res.score}/100)`, "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi kết nối máy chủ AI", "error");
    }
  };

  const handleSynonyms = async () => {
    if (!editorRef.current) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      let text = "";
      data.blocks.forEach((b: any) => {
        if (b.data?.text) text += b.data.text + " ";
      });
      if (!text || text.length < 10) {
        showToast("Vui lòng chọn một từ để tìm từ đồng nghĩa", "info");
        setIsSuggesting(false);
        return;
      }
      const words = text.split(" ").filter((w: string) => w.trim().length > 0);
      const targetWord = words[words.length - 1];
      const res = await getSynonymsAPI(targetWord, text);
      if (res.synonyms && res.synonyms.length > 0) {
        showToast(`Gợi ý cho "${targetWord}": ${res.synonyms.join(", ")}`, "info");
      } else {
        showToast("Không tìm thấy từ đồng nghĩa phù hợp", "info");
      }
    } catch (err: any) {
      showToast(err.message || "Không thể lấy gợi ý lúc này", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  const fetchSidebarData = useCallback(async () => {
    if (!documentId || activeSidebar === "none") return;
    setLoadingSidebar(true);
    try {
      if (activeSidebar === "history") {
        const { getDocumentVersionsAPI } = await import("@/services/version.service");
        const data = await getDocumentVersionsAPI(documentId);
        setSidebarData(data || []);
      } else if (activeSidebar === "comments") {
        const res = await fetch(`${API_URL}/soan-thao/${documentId}/binh-luan`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const data = await res.json();
        setSidebarData(data.data || []);
      }
    } catch (err: any) {
      showToast("Không thể tải dữ liệu thanh bên", "error");
    } finally {
      setLoadingSidebar(false);
    }
  }, [documentId, activeSidebar, showToast]);

  useEffect(() => {
    fetchSidebarData();
  }, [fetchSidebarData]);

  const handleConsistencyCheck = async () => {
    if (!editorRef.current || !documentId) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      const text = data.blocks.map(b => b.data?.text || "").join(" ");
      const res = await fetch(`${API_URL}/soan-thao/${documentId}/kiem-tra-logic`, {
          method: "POST",
          headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ content: text })
      });
      const result = await res.json();
      if (result.conflicts && result.conflicts.length > 0) {
          showToast(`Cảnh báo logic: ${result.conflicts[0]}`, "error");
      } else {
          showToast("Nội dung nhất quán với các chương trước", "success");
      }
    } catch (err: any) {
      showToast("Không thể kiểm tra tính nhất quán", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleAiWritingPartner = async () => {
    if (!editorRef.current || !documentId) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      let lastText = "";
      if (data.blocks.length > 0) {
        const lastBlock = data.blocks[data.blocks.length - 1];
        lastText = lastBlock.data?.text || "";
      }
      
      const res = await getAiSuggestionsAPI(documentId, lastText);
      showToast("AI đã tạo gợi ý mới", "success");
      console.log("AI Suggestions:", res);
    } catch (err: any) {
      showToast(err.message || "Không thể gọi trợ lý AI", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  return (
    <div className={`flex flex-col w-full h-full bg-white relative font-sans ${isZenMode ? "fixed inset-0 z-50" : ""}`}>
      {!isZenMode && (
        <div className="flex justify-between items-center border-b border-zinc-200 p-3 animate-in fade-in duration-300">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex gap-2 ml-2">
              <button
                onClick={handleSynonyms}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
              >
                <Sparkles className="w-4 h-4" />
                Gợi ý từ ngữ
              </button>
              <button
                onClick={handleAiWritingPartner}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-black flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
              >
                <Wand2 className="w-4 h-4" />
                Trợ lý AI
              </button>
              <button
                onClick={() => setIsAiToolsOpen(true)}
                className="px-4 py-1.5 border border-black bg-white text-black flex gap-2 items-center text-xs font-bold active:scale-[0.98] transition-all hover:bg-zinc-50"
              >
                <Brain className="w-4 h-4" />
                Công cụ AI nâng cao
              </button>
              <button
                onClick={handleConsistencyCheck}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
              >
                <CheckSquare className="w-4 h-4" />
                Kiểm tra tính logic
              </button>
              <button
                onClick={handleGrammarCheck}
                className="px-4 py-1.5 bg-black text-white flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
              >
                <FileText className="w-4 h-4 text-zinc-400" />
                Kiểm tra ngữ pháp
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveSidebar(activeSidebar === "comments" ? "none" : "comments")}
              className={`p-1.5 border ${activeSidebar === "comments" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"} transition-colors duration-150`}
            >
              <MessageSquare className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveSidebar(activeSidebar === "history" ? "none" : "history")}
              className={`p-1.5 border ${activeSidebar === "history" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"} transition-colors duration-150`}
            >
              <History className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsZenMode(true)}
              className="p-1.5 border border-zinc-200 text-zinc-600 hover:bg-zinc-50 transition-colors duration-150"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {isZenMode && (
        <button
          onClick={() => setIsZenMode(false)}
          className="fixed top-4 right-4 p-2 bg-white/80 backdrop-blur border border-zinc-200 text-zinc-400 hover:text-black z-[60] rounded-md transition-all duration-300"
        >
          <Minimize2 className="w-5 h-5" />
        </button>
      )}

      <div className="flex-1 w-full flex overflow-hidden relative bg-white">
        <div className={`h-full overflow-y-auto transition-all duration-300 ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"} p-12`}>
          <div ref={containerRef} />
        </div>
        
        {activeSidebar !== "none" && (
          <div className="w-1/3 h-full border-l border-zinc-200 bg-zinc-50 flex flex-col animate-in slide-in-from-right-8 fade-in duration-300">
            <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-white">
              <span className="text-xs font-bold uppercase tracking-tight">
                {activeSidebar === "comments" ? "Nhận xét nội dòng" : "Lịch sử phiên bản"}
              </span>
              <button onClick={() => setActiveSidebar("none")} className="p-1 text-zinc-400 hover:text-black"><X className="w-4 h-4" /></button>
            </div>
            <div className="flex-1 p-4 overflow-y-auto no-scrollbar">
              <div className="flex flex-col gap-3">
                {loadingSidebar ? (
                   <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-zinc-400" /></div>
                ) : sidebarData.length === 0 ? (
                  <div className="p-8 border border-zinc-200 bg-white text-xs text-zinc-400 text-center italic">
                    Chưa có dữ liệu để hiển thị
                  </div>
                ) : activeSidebar === "history" ? (
                    sidebarData.map((v, idx) => (
                        <div key={v.id || `history-${idx}`} className="p-4 border border-zinc-200 bg-white space-y-2">
                           <div className="flex justify-between items-start">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase">{new Date(v.created_at).toLocaleString("vi-VN")}</span>
                              <Clock className="w-3 h-3 text-zinc-300" />
                           </div>
                           <p className="text-xs font-medium text-black">Bản lưu bởi {v.author_name || "Hệ thống"}</p>
                        </div>
                    ))
                ) : (
                    sidebarData.map((c, idx) => (
                        <div key={c.id || `comment-${idx}`} className="p-4 border border-zinc-200 bg-white space-y-2">
                           <div className="flex justify-between items-start">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase">{new Date(c.created_at).toLocaleString("vi-VN")}</span>
                              <MessageSquare className="w-3 h-3 text-zinc-300" />
                           </div>
                           <p className="text-xs font-medium text-black">{c.content}</p>
                           <div className="pt-2 flex justify-end">
                              <button className="text-[10px] font-bold text-zinc-400 hover:text-black uppercase">Giải quyết</button>
                           </div>
                        </div>
                    ))
                )}
              </div>
            </div>
          </div>
        )}

        {isPreview && previewPdfUrl && (
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative animate-in slide-in-from-right-8 fade-in duration-300">
            <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center">
              <span className="font-bold uppercase tracking-tight">Bản in PDF</span>
              <a href={previewPdfUrl} download="doclib-preview.pdf" className="p-1.5 text-zinc-300 hover:text-white"><Download className="w-4 h-4" /></a>
            </div>
            <div className="flex-1 bg-zinc-100 p-4">
              <iframe src={previewPdfUrl} className="w-full h-full bg-white border border-zinc-200" />
            </div>
          </div>
        )}
      </div>

      <div className="h-8 border-t border-zinc-200 bg-white px-6 flex items-center justify-between shrink-0 z-30">
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Tốc độ</span>
                <span className="text-[10px] font-bold text-black">{stats.wpm} WPM</span>
             </div>
             <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Số ký tự</span>
                <span className="text-[10px] font-bold text-black">{stats.charCount}</span>
             </div>
          </div>
          <div className="flex items-center gap-4">
             <div className="w-32 h-1 bg-zinc-100 relative">
                <div 
                  className="absolute top-0 left-0 h-full bg-black transition-all duration-500" 
                  style={{ width: `${Math.min(100, (stats.charCount / 5000) * 100)}%` }}
                />
             </div>
             <span className="text-[10px] font-bold text-zinc-400 uppercase">Mục tiêu ngày</span>
          </div>
      </div>

      <AIToolsModal 
        isOpen={isAiToolsOpen} 
        onClose={() => setIsAiToolsOpen(false)} 
        editorContent={lastContentRef.current} 
      />
    </div>
  );
}
