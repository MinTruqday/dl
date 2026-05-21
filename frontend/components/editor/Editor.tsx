"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import { useToast } from "@/contexts/Toast";
import { 
    compilePreviewAPI, 
    globalFindReplaceAPI, 
    getAiSuggestionsAPI,
    addInlineCommentAPI,
    getVersionDiffAPI
} from "@/services/editor.service";
import { grammarCheckAPI, getSynonymsAPI } from "@/services/inference.service";
import { API_URL, getAuthHeaders } from "@/services/authentication.service";
import { Sparkles, CheckSquare, FileText, Download, Loader2, Maximize2, Minimize2, MessageSquare, History, Wand2, X, Brain, Bot, ShieldCheck, Languages, Binary, CheckCheck, Scale, PenLine, Network } from "lucide-react";

interface EditorProps {
  documentId?: string;
  initialContent?: string;
  onSave?: (data: string) => void;
}

export default function Editor({
  documentId,
  initialContent,
  onSave,
}: EditorProps) {
  const editorRef = useRef<EditorJS | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isZenMode, setIsZenMode] = useState(false);
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
        } catch (err: any) {
          console.warn("Error parsing initial content JSON:", err.message || err);
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
          } catch (err) { console.error(err); }
        },
      });

      if (!cancelled) {
        editorRef.current = editor;
      } else {
        editor.isReady.then(() => editor.destroy()).catch((err) => { console.error(err); });
        holderDiv.remove();
      }
    };

    init();

    return () => {
      cancelled = true;
      if (editorRef.current) {
        const instance = editorRef.current;
        editorRef.current = null;
        instance.isReady.then(() => instance.destroy()).catch((err) => { console.error(err); });
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
      } catch (err: any) {
        console.warn("Error parsing JSON when rendering Editor:", err.message || err);
        data = { blocks: [{ type: "paragraph", data: { text: initialContent } }] };
      }
      editorRef.current?.render(data);
    }).catch((err) => { console.error(err); });
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
      if (res.data) {
        showToast(`Kết quả AI: Điểm ${res.data.score}/100.`, "success");
        if (res.data.corrected_text) {
          editorRef.current.blocks.insert("paragraph", { text: `<i>[Đề xuất sửa ngữ pháp]: ${res.data.corrected_text}</i>` });
        }
      }
    } catch (err: any) {
      showToast(err.message || "Lỗi kết nối máy chủ AI", "error");
    }
  };

  const handleCompilePreview = async () => {
    if (!editorRef.current) return;
    setIsCompiling(true);
    showToast("Đang biên dịch mã nguồn LaTeX", "info");
    try {
      const data = await editorRef.current.save();
      let latexCode = "";
      data.blocks.forEach((b: any) => {
        if (b.type === "paragraph" || b.type === "header") {
          latexCode += (b.data?.text || "") + "\n\n";
        } else if (b.type === "code") {
          latexCode += (b.data?.code || "") + "\n\n";
        } else if (b.type === "raw") {
          latexCode += (b.data?.html || "") + "\n\n";
        }
      });
      
      if (!latexCode.trim()) {
        showToast("Vui lòng nhập nội dung để biên dịch", "info");
        setIsCompiling(false);
        return;
      }
      
      const pdfBlob = await compilePreviewAPI(latexCode, true);
      const pdfUrl = URL.createObjectURL(pdfBlob);
      setPreviewPdfUrl(pdfUrl);
      setIsPreview(true);
      showToast("Biên dịch LaTeX thành công", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi khi biên dịch LaTeX", "error");
    } finally {
      setIsCompiling(false);
    }
  };

  const handleSynonyms = async () => {
    if (!editorRef.current) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      let text = data.blocks.map((b: any) => b.data?.text || "").join(" ");
      
      const selection = window.getSelection();
      const targetWord = selection?.toString().trim();

      if (!targetWord || targetWord.split(" ").length > 3) {
        showToast("Vui lòng chọn một từ hoặc cụm từ ngắn để tìm đồng nghĩa", "info");
        setIsSuggesting(false);
        return;
      }

      const res = await getSynonymsAPI(targetWord, text);
      const synonyms = res.data?.synonyms || [];
      if (synonyms.length > 0) {
        showToast(`Gợi ý cho "${targetWord}": ${synonyms.join(", ")}`, "info");
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
            headers: getAuthHeaders()
        });
        if (!res.ok) throw new Error("Lỗi xác thực hoặc không thể tải nhận xét");
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
      const contextText = text.length > 3000 ? text.slice(-3000) : text;
      const res = await fetch(`${API_URL}/soan-thao/${documentId}/kiem-tra-logic`, {
          method: "POST",
          headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ content: contextText })
      });
      const result = await res.json();
      const conflicts = result.data?.conflicts || [];
      if (conflicts.length > 0) {
          showToast(`Cảnh báo logic: ${conflicts[0]}`, "error");
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
        const lastBlocks = data.blocks.slice(-5);
        lastText = lastBlocks.map((b: any) => b.data?.text || "").join(" ");
      }
      
      const res = await getAiSuggestionsAPI(documentId, lastText);
      const suggestion = res.suggestions || "";
      if (suggestion) {
        editorRef.current.blocks.insert("paragraph", { text: `<i>[Gợi ý AI]: ${suggestion}</i>` });
        showToast("Đã chèn gợi ý AI vào cuối văn bản", "success");
      } else {
        showToast("AI chưa có gợi ý phù hợp lúc này", "info");
      }
    } catch (err: any) {
      showToast(err.message || "Không thể gọi trợ lý AI", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  return (
    <div className={`flex flex-col w-full h-full bg-white relative font-sans ${isZenMode ? "fixed inset-0 z-50" : ""}`}>
      {!isZenMode && (
        <div className="flex justify-between items-center border-b border-zinc-200 p-3 animate-in fade-in ">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="flex gap-2 ml-2">
              <button
                onClick={handleSynonyms}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98]  "
              >
                Gợi ý từ ngữ
              </button>
              <button
                onClick={handleAiWritingPartner}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98]  "
              >
                Trợ lý AI
              </button>
              <button
                onClick={handleConsistencyCheck}
                disabled={isSuggesting}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98]  "
              >
                Kiểm tra tính logic
              </button>
              <button
                onClick={handleGrammarCheck}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98]  "
              >
                Kiểm tra ngữ pháp
              </button>
              <button
                onClick={handleCompilePreview}
                disabled={isCompiling}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98]   flex items-center gap-1.5"
              >
                {isCompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Binary className="w-3.5 h-3.5" />}
                Biên dịch LaTeX
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsPreview(!isPreview)}
              className={`p-1.5 border ${isPreview ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}  `}
              title="Bật/Tắt bản xem trước PDF"
            >
              <FileText className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveSidebar(activeSidebar === "comments" ? "none" : "comments")}
              className={`p-1.5 border ${activeSidebar === "comments" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}  `}
            >
              <MessageSquare className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveSidebar(activeSidebar === "history" ? "none" : "history")}
              className={`p-1.5 border ${activeSidebar === "history" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}  `}
            >
              <History className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsZenMode(true)}
              className="p-1.5 border border-zinc-200 text-zinc-600   "
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {isZenMode && (
        <button
          onClick={() => setIsZenMode(false)}
          className="fixed top-4 right-4 p-2 bg-white/80 backdrop-blur border border-zinc-200 text-zinc-400  z-[60] rounded-md  "
        >
          <Minimize2 className="w-5 h-5" />
        </button>
      )}

      <div className="flex-1 w-full flex overflow-hidden relative bg-white">
        <div className={`h-full overflow-y-auto   ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"} p-12`}>
          <div ref={containerRef} />
        </div>
        
        {activeSidebar !== "none" && (
          <div className="w-1/3 h-full border-l border-zinc-200 bg-zinc-50 flex flex-col animate-in slide-in-from-right-8 fade-in ">
            <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-white">
              <span className="text-xs font-bold uppercase tracking-tight">
                {activeSidebar === "comments" ? "Nhận xét nội dòng" : "Lịch sử phiên bản"}
              </span>
              <button onClick={() => setActiveSidebar("none")} className="p-1 text-zinc-400 "><X className="w-4 h-4" /></button>
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
                              <span className="text-[10px] font-bold text-zinc-400 uppercase">{v.created_at ? new Date(v.created_at).toLocaleString("vi-VN") : ""}</span>
                              <Clock className="w-3 h-3 text-zinc-300" />
                           </div>
                           <p className="text-xs font-medium text-black">Bản lưu bởi {v.author_name || "Hệ thống"}</p>
                        </div>
                    ))
                ) : (
                    sidebarData.map((c, idx) => (
                        <div 
                           key={c.id || `comment-${idx}`} 
                           className="p-4 border border-zinc-200 bg-white space-y-2 cursor-pointer  "
                           onClick={() => {
                             if (c.selected_text || c.content) {
                                const searchText = c.selected_text || c.content;
                                const elements = document.querySelectorAll('.ce-block');
                                for (let i = 0; i < elements.length; i++) {
                                   if (elements[i].textContent?.includes(searchText)) {
                                      elements[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                                      elements[i].classList.add('bg-zinc-100', '', '');
                                      setTimeout(() => elements[i].classList.remove('bg-zinc-100'), 2000);
                                      break;
                                   }
                                }
                             }
                           }}
                        >
                           <div className="flex justify-between items-start">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase">{c.created_at ? new Date(c.created_at).toLocaleString("vi-VN") : ""}</span>
                              <MessageSquare className="w-3 h-3 text-zinc-300" />
                           </div>
                           <p className="text-xs font-bold text-black border-b border-zinc-100 pb-1">{c.user_name || "Khách"}</p>
                           <p className="text-xs font-medium text-black">{c.text || c.content}</p>
                           <div className="pt-2 flex justify-end">
                              <button className="text-[10px] font-bold text-zinc-400  uppercase">Giải quyết</button>
                           </div>
                        </div>
                    ))
                )}
              </div>
            </div>
          </div>
        )}

        {isPreview && previewPdfUrl && (
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative animate-in slide-in-from-right-8 fade-in ">
            <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center">
              <span className="font-bold uppercase tracking-tight">Bản in PDF</span>
              <a href={previewPdfUrl} download="doclib-preview.pdf" className="p-1.5 text-zinc-300 "><Download className="w-4 h-4" /></a>
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
                  className="absolute top-0 left-0 h-full bg-black  " 
                  style={{ width: `${Math.min(100, (stats.charCount / (parseInt(typeof window !== 'undefined' ? localStorage.getItem("doclib_daily_goal") || "5000" : "5000"))) * 100)}%` }}
                />
             </div>
             <span className="text-[10px] font-bold text-zinc-400 uppercase">Mục tiêu ngày</span>
          </div>
      </div>

    </div>
  );
}
