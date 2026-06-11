"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import StandardEditor from "./StandardEditor";
import LatexEditor from "./LatexEditor";
import { useToast } from "@/contexts/Toast";
import { 
    compilePreviewAPI, 
    globalFindReplaceAPI, 
    getAiSuggestionsAPI,
    addInlineCommentAPI,
    getVersionDiffAPI,
    summarizeDocumentAPI,
    extractSmartTagsAPI,
    exportToEpubAPI,
    checkDeepPlagiarismAPI
} from "@/services/editor.service";
import { grammarCheckAPI, getSynonymsAPI, translateTextAPI } from "@/services/inference.service";
import { API_URL, getAuthHeaders } from "@/services/authentication.service";
import { Sparkles, CheckSquare, FileText, Download, Loader2, Maximize2, Minimize2, MessageSquare, History, Wand2, X, Brain, Bot, ShieldCheck, Languages, Binary, CheckCheck, Scale, PenLine, Network, Clock, Search, FileEdit, List } from "lucide-react";
import MonacoEditor from "@monaco-editor/react";

interface EditorProps {
  documentId?: string;
  initialContent?: string;
  contentFormat?: string;
  onSave?: (data: string) => void;
}

export default function Editor({
  documentId,
  initialContent,
  contentFormat = "json",
  onSave,
}: EditorProps) {
  const editorRef = useRef<EditorJS | null>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [isZenMode, setIsZenMode] = useState(false);
  const [activeSidebar, setActiveSidebar] = useState<"none" | "comments" | "history" | "toc">("none");
  const [sidebarData, setSidebarData] = useState<any[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);
  const [stats, setStats] = useState({ wpm: 0, charCount: 0, goalProgress: 0 });
  const [readingTime, setReadingTime] = useState<number>(0);
  const [lastKeystroke, setLastKeystroke] = useState<number>(Date.now());
  const lastContentRef = useRef<string>(initialContent || "");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [saveStatus, setSaveStatus] = useState<string>("Đã lưu");
  const { showToast } = useToast();

  const [isExportingWord, setIsExportingWord] = useState(false);
  const [isExportingEpub, setIsExportingEpub] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isExtractingTags, setIsExtractingTags] = useState(false);
  const [isScanningPlagiarism, setIsScanningPlagiarism] = useState(false);
  const [plagiarismScore, setPlagiarismScore] = useState<number | null>(null);
  const [tocData, setTocData] = useState<{id: string, text: string, level: number}[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [documentSummary, setDocumentSummary] = useState<string>("");
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [isFinding, setIsFinding] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<number>(1);
  const [localText, setLocalText] = useState(initialContent || "");
  const [showTranslateModal, setShowTranslateModal] = useState(false);
  const [targetLang, setTargetLang] = useState("Tiếng Anh");
  const [isTranslating, setIsTranslating] = useState(false);
  const [originalContentForUndo, setOriginalContentForUndo] = useState<string | null>(null);
  const latexValueRef = useRef<string>(initialContent || "");

  useEffect(() => {
    if (!documentId) return;
    let wsUrl = `ws://localhost:8200/soan-thao/ws-crdt/${documentId}`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (e) => {
        setOnlineUsers(prev => prev);
      };
      ws.onopen = () => setOnlineUsers(2);
      ws.onclose = () => setOnlineUsers(1);
    } catch (e) { console.error("WebSocket Error", e); }
    return () => { if (ws) ws.close(); };
  }, [documentId]);

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
        } else if (b.type === "monacoLatex") {
          latexCode += (b.data?.code || "") + "\n\n";
        }
      });
      
      if (!latexCode.trim()) {
        showToast("Vui lòng nhập nội dung để biên dịch", "info");
        setIsCompiling(false);
        return;
      }
      
      let finalLatexCode = latexCode;
      if (!latexCode.includes("\\documentclass")) {
        finalLatexCode = `
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T5]{fontenc}
\\begin{document}
${latexCode}
\\end{document}
        `.trim();
      }
      
      const pdfBlob = await compilePreviewAPI(finalLatexCode, true);
      const pdfUrl = URL.createObjectURL(pdfBlob);
      setPreviewPdfUrl(pdfUrl);
      setIsPreview(true);
      showToast("Biên dịch LaTeX thành công", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi khi biên dịch LaTeX", "error");
      setIsCompiling(false);
    }
  };

  const handleExportWord = async () => {
    if (!documentId) return;
    setIsExportingWord(true);
    showToast("Đang xuất tài liệu sang Word", "info");
    try {
      const { exportToWordAPI } = await import("@/services/editor.service");
      const blob = await exportToWordAPI(documentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DocLib_${documentId}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast("Xuất Word thành công", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi khi xuất Word", "error");
    } finally {
      setIsExportingWord(false);
    }
  };

  const executeFindReplace = async () => {
    if (!documentId || !findText) return;
    setIsFinding(true);
    try {
      await globalFindReplaceAPI(documentId, findText, replaceText, false);
      showToast("Đã thay thế thành công, nội dung sẽ được cập nhật", "success");
      setShowFindReplace(false);
    } catch (err: any) {
      showToast(err.message || "Lỗi khi thay thế", "error");
    } finally {
      setIsFinding(false);
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

      const res = await getSynonymsAPI(targetWord);
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

  const handleExportEpub = async () => {
    if (!documentId) return;
    setIsExportingEpub(true);
    showToast("Đang xuất file EPUB", "info");
    try {
      const blob = await exportToEpubAPI(documentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "tai-lieu.epub";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      showToast(err.message || "Lỗi khi xuất file EPUB", "error");
    } finally {
      setIsExportingEpub(false);
    }
  };

  const handleSummarize = async () => {
    if (!documentId) return;
    setIsSummarizing(true);
    showToast("Đang tóm tắt tài liệu bằng AI", "info");
    try {
      const res = await summarizeDocumentAPI(documentId);
      setDocumentSummary(res.summary || res.data?.summary || "");
      showToast("Tóm tắt thành công", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi kết nối máy chủ AI", "error");
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleExtractTags = async () => {
    if (!documentId) return;
    setIsExtractingTags(true);
    showToast("Đang phân tích thẻ tự động", "info");
    try {
      const res = await extractSmartTagsAPI(documentId);
      setTags(res.tags || res.data?.tags || []);
      showToast("Trích xuất thẻ thành công", "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi kết nối máy chủ AI", "error");
    } finally {
      setIsExtractingTags(false);
    }
  };

  const handlePlagiarismScan = async () => {
    if (!documentId || !editorRef.current) return;
    setIsScanningPlagiarism(true);
    showToast("Đang quét đạo văn nội bộ", "info");
    try {
      const data = await editorRef.current.save();
      const text = data.blocks.map((b: any) => b.data?.text || "").join(" ");
      if (text.length < 50) throw new Error("Văn bản quá ngắn để quét đạo văn");
      
      const res = await checkDeepPlagiarismAPI(documentId);
      const score = res.data?.duplication_score || res.duplication_score || 0;
      setPlagiarismScore(score);
      showToast(`Quét hoàn tất: ${score}% trùng lặp.`, score > 20 ? "info" : "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi hệ thống quét", "error");
    } finally {
      setIsScanningPlagiarism(false);
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

  const handleTranslate = async () => {
    if (!editorRef.current && contentFormat === "json") return;
    setIsTranslating(true);
    setShowTranslateModal(false);
    showToast(`Đang dịch sang ${targetLang}... Vui lòng đợi`, "info");
    
    try {
      if (contentFormat === "latex") {
         const currentText = latexValueRef.current;
         const res = await translateTextAPI(currentText, targetLang);
         const translated = res.translation || res.data?.translation || "";
         if (translated) {
             setOriginalContentForUndo(currentText);
             latexValueRef.current = translated;
             setLocalText(translated);
             if (onSave) onSave(translated);
             showToast("Đã dịch thành công", "success");
         }
      } else {
         if (!editorRef.current) return;
         const data = await editorRef.current.save();
         setOriginalContentForUndo(JSON.stringify(data));
         
         const newBlocks = [];
         for (const b of data.blocks) {
             if (b.data?.text && typeof b.data.text === "string") {
                 try {
                     const res = await translateTextAPI(b.data.text, targetLang);
                     const translated = res.translation || res.data?.translation;
                     if (translated) {
                         newBlocks.push({ ...b, data: { ...b.data, text: translated } });
                     } else {
                         newBlocks.push(b);
                     }
                 } catch (e) {
                     newBlocks.push(b);
                 }
             } else {
                 newBlocks.push(b);
             }
         }
         
         data.blocks = newBlocks;
         await editorRef.current.render(data);
         if (onSave) onSave(JSON.stringify(data));
         showToast("Đã dịch thành công", "success");
      }
    } catch (err: any) {
      showToast("Lỗi dịch thuật: " + err.message, "error");
    } finally {
      setIsTranslating(false);
    }
  };

  const handleRevertTranslation = async () => {
      if (!originalContentForUndo) return;
      if (contentFormat === "latex") {
          setLocalText(originalContentForUndo);
          latexValueRef.current = originalContentForUndo;
          if (onSave) onSave(originalContentForUndo);
      } else {
          if (!editorRef.current) return;
          const data = JSON.parse(originalContentForUndo);
          await editorRef.current.render(data);
          if (onSave) onSave(originalContentForUndo);
      }
      setOriginalContentForUndo(null);
      showToast("Đã hoàn tác về nguyên bản", "success");
  };

  return (
    <div className={`flex flex-col w-full h-full bg-white relative font-sans ${isZenMode ? "fixed inset-0 z-50" : ""}`}>
      {!isZenMode && (
        <div className="flex justify-between items-center border-b border-zinc-200 p-3 gap-4">
          <div className="flex flex-1 overflow-x-auto no-scrollbar gap-2 items-center">
            <button
              onClick={handleSynonyms}
              disabled={isSuggesting}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              Gợi ý từ ngữ
            </button>
            <button
              onClick={handleAiWritingPartner}
              disabled={isSuggesting}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 flex items-center gap-1.5"
            >
              <Bot className="w-3.5 h-3.5" />
              Trợ lý AI
            </button>
            <button
              onClick={handleConsistencyCheck}
              disabled={isSuggesting}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 flex items-center gap-1.5"
            >
              <Network className="w-3.5 h-3.5" />
              Kiểm tra tính logic
            </button>
            <button
              onClick={handleGrammarCheck}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 flex items-center gap-1.5"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              Kiểm tra ngữ pháp
            </button>
            <button
              onClick={handleCompilePreview}
              disabled={isCompiling}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              {isCompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Binary className="w-3.5 h-3.5" />}
              Biên dịch LaTeX
            </button>

            <button
              onClick={() => setShowFindReplace(!showFindReplace)}
              className={`px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 ${showFindReplace ? "bg-black text-white border-black hover:bg-zinc-800" : ""}`}
            >
              <Search className="w-3.5 h-3.5" />
              Tìm kiếm / Thay thế
            </button>
            
            <div className="w-px h-6 bg-zinc-200 mx-1 shrink-0" />

            <button
              onClick={handleSummarize}
              disabled={isSummarizing}
              className="px-4 py-1.5 bg-black text-white text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-800"
            >
              {isSummarizing ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white" /> : <Wand2 className="w-3.5 h-3.5 text-white" />}
              Tóm tắt bằng AI
            </button>
            <button
              onClick={handleExtractTags}
              disabled={isExtractingTags}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              {isExtractingTags ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Languages className="w-3.5 h-3.5" />}
              Tự động tạo thẻ
            </button>
            <button
              onClick={() => originalContentForUndo ? handleRevertTranslation() : setShowTranslateModal(true)}
              disabled={isTranslating}
              className={`px-4 py-1.5 border border-zinc-200 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 ${originalContentForUndo ? "bg-amber-50 text-amber-600 border-amber-200 hover:bg-amber-100" : "text-zinc-600"}`}
            >
              {isTranslating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Languages className="w-3.5 h-3.5" />}
              {originalContentForUndo ? "Nguyên bản" : "Dịch tài liệu"}
            </button>
            <button
              onClick={handlePlagiarismScan}
              disabled={isScanningPlagiarism}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              {isScanningPlagiarism ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              Kiểm tra bản quyền
            </button>
          </div>
          <div className="flex gap-2 shrink-0">
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
              onClick={() => setActiveSidebar(activeSidebar === "toc" ? "none" : "toc")}
              className={`p-1.5 border ${activeSidebar === "toc" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}`}
              title="Mục lục"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveSidebar(activeSidebar === "history" ? "none" : "history")}
              className={`p-1.5 border ${activeSidebar === "history" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}`}
              title="Lịch sử phiên bản"
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
        {showFindReplace && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-white border border-zinc-200 p-4">
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-tight">Tìm kiếm và thay thế</span>
                <button onClick={() => setShowFindReplace(false)} className="text-zinc-400 p-1"><X className="w-4 h-4" /></button>
              </div>
              <div className="flex gap-2 items-center">
                <input 
                  type="text" 
                  placeholder="Từ cần tìm" 
                  className="px-3 py-1.5 text-xs border border-zinc-200 focus:outline-none"
                  value={findText}
                  onChange={(e) => setFindText(e.target.value)}
                />
                <span className="text-xs text-zinc-400">{'->'}</span>
                <input 
                  type="text" 
                  placeholder="Thay bằng" 
                  className="px-3 py-1.5 text-xs border border-zinc-200 focus:outline-none"
                  value={replaceText}
                  onChange={(e) => setReplaceText(e.target.value)}
                />
                <button 
                  onClick={executeFindReplace}
                  disabled={isFinding || !findText}
                  className="px-4 py-1.5 bg-black text-white text-xs font-bold"
                >
                  {isFinding ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Thay thế toàn cục"}
                </button>
              </div>
            </div>
          </div>
        )}

        {showTranslateModal && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-white border border-zinc-200 p-4 shadow-xl rounded-lg">
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-tight">Dịch tài liệu</span>
                <button onClick={() => setShowTranslateModal(false)} className="text-zinc-400 p-1 hover:bg-zinc-100 rounded"><X className="w-4 h-4" /></button>
              </div>
              <div className="flex gap-2 items-center">
                <span className="text-xs text-zinc-600 font-medium">Sang:</span>
                <select 
                  className="px-3 py-1.5 text-xs border border-zinc-200 rounded focus:outline-none bg-white"
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                >
                  <option value="Tiếng Anh">Tiếng Anh</option>
                  <option value="Tiếng Việt">Tiếng Việt</option>
                  <option value="Tiếng Pháp">Tiếng Pháp</option>
                  <option value="Tiếng Trung">Tiếng Trung</option>
                  <option value="Tiếng Nhật">Tiếng Nhật</option>
                  <option value="Tiếng Hàn">Tiếng Hàn</option>
                </select>
                <button 
                  onClick={handleTranslate}
                  disabled={isTranslating}
                  className="px-4 py-1.5 bg-black text-white text-xs font-bold rounded-md hover:bg-zinc-800"
                >
                  Bắt đầu dịch
                </button>
              </div>
            </div>
          </div>
        )}

        <div className={`h-full overflow-y-auto flex justify-center bg-white ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"}`}>
          {contentFormat === "latex" ? (
            <LatexEditor 
              initialContent={localText}
              onChange={(val) => {
                 latexValueRef.current = val;
                 if (onSave) onSave(val);
              }}
              setReadingTime={setReadingTime}
              setStats={setStats}
              setLastKeystroke={setLastKeystroke}
            />
          ) : (
            <div className="w-full max-w-[900px] px-12 py-20 flex flex-col">
              <StandardEditor 
                initialContent={initialContent}
                onSave={onSave}
                documentId={documentId}
                setReadingTime={setReadingTime}
                setStats={setStats}
                setLastKeystroke={setLastKeystroke}
                setTocData={setTocData}
                setSaveStatus={setSaveStatus}
                showToast={showToast}
                editorRef={editorRef}
              />
            </div>
          )}
        </div>
        
        {activeSidebar !== "none" && (
          <div className="w-1/3 h-full border-l border-zinc-200 bg-zinc-50 flex flex-col">
            <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-white">
              <span className="text-xs font-bold uppercase tracking-tight">
                {activeSidebar === "comments" ? "Nhận xét nội dòng" : activeSidebar === "history" ? "Lịch sử phiên bản" : "Mục lục"}
              </span>
              <button onClick={() => setActiveSidebar("none")} className="p-1 text-zinc-400 "><X className="w-4 h-4" /></button>
            </div>
            <div className="flex-1 p-4 overflow-y-auto no-scrollbar">
              <div className="flex flex-col gap-3">
                {loadingSidebar ? (
                   <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-zinc-400" /></div>
                ) : activeSidebar === "toc" ? (
                  tocData.length === 0 ? (
                    <div className="p-8 border border-zinc-200 bg-white text-xs text-zinc-400 text-center italic">
                      Chưa có thẻ Header nào
                    </div>
                  ) : (
                    tocData.map((item, idx) => (
                      <div 
                        key={item.id || `toc-${idx}`}
                        className="p-2 border border-zinc-200 bg-white text-xs text-black font-medium cursor-pointer"
                        style={{ marginLeft: `${(item.level - 1) * 16}px` }}
                        onClick={() => {
                          const elements = document.querySelectorAll('.ce-header');
                          for (let i = 0; i < elements.length; i++) {
                             if (elements[i].textContent?.includes(item.text)) {
                                elements[i].scrollIntoView({ behavior: 'smooth', block: 'start' });
                                break;
                             }
                          }
                        }}
                      >
                        {item.text}
                      </div>
                    ))
                  )
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
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative">
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
             <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Thời gian đọc</span>
                <span className="text-[10px] font-bold text-black">{readingTime} phút</span>
             </div>
             {tags.length > 0 && (
               <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Thẻ</span>
                  <div className="flex gap-1">
                    {tags.map((t, idx) => (
                      <span key={idx} className="px-1.5 py-0.5 bg-zinc-100 text-[10px] text-zinc-600 font-medium">#{t}</span>
                    ))}
                  </div>
               </div>
             )}
          </div>
          <div className="flex items-center gap-4">
            {plagiarismScore !== null && (
              <div className="flex items-center gap-2 px-3 py-1 bg-zinc-50 border border-zinc-200">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Bản quyền</span>
                <span className={`text-[10px] font-bold ${plagiarismScore > 20 ? 'text-red-600' : 'text-green-600'}`}>{plagiarismScore}%</span>
              </div>
            )}
            <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${onlineUsers > 1 ? 'bg-green-500' : 'bg-zinc-400'}`}></span>
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Cộng tác</span>
                <span className="text-[10px] font-bold text-black">{onlineUsers > 1 ? `${onlineUsers} trực tuyến` : "Đang trực tuyến"}</span>
            </div>
            <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Trạng thái</span>
                <span className="text-[10px] font-bold text-black">{saveStatus}</span>
            </div>
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
