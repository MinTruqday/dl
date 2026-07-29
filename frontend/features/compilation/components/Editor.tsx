"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import StandardEditor from "./StandardEditor";
import LatexEditor from "./LatexEditor";
import { useToast } from "@/shared/contexts/ToastContext";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  compilePreviewAPI,
  globalFindReplaceAPI,
  addInlineCommentAPI,
  getInlineCommentsAPI,
  getVersionDiffAPI,
  getAiSuggestionsAPI,
  summarizeDocumentAPI,
} from "@/features/compilation/services/editorjs.service";
import {
  grammarCheckAPI,
  getSynonymsAPI,
  translateTextAPI,
} from "@/features/agentic_ai/services/inference.service";
import { peerReviewAPI } from "@/features/agentic_ai/services/interaction.service";
import { getToken } from "@/features/authentication/services/session.service";
import {
  Sparkles,
  CheckSquare,
  FileText,
  Download,
  Loader2,
  Maximize2,
  Minimize2,
  MessageSquare,
  History,
  Wand2,
  X,
  Brain,
  Bot,
  ShieldCheck,
  Languages,
  Binary,
  CheckCheck,
  Scale,
  PenLine,
  Network,
  Clock,
  Search,
  FileEdit,
  List,
} from "lucide-react";
import MonacoEditor from "@monaco-editor/react";
import { sanitizeEditorData } from "./editorjs-sanitizer";
import WordCommandPalette from "./WordCommandPalette";
import {
  attachWordSettings,
  registerWordSettings,
  type WordOutputData,
} from "./word-command-engine";

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
  const [activeSidebar, setActiveSidebar] = useState<
    "none" | "comments" | "history" | "toc"
  >("none");
  const [sidebarData, setSidebarData] = useState<any[]>([]);
  const [loadingSidebar, setLoadingSidebar] = useState(false);
  const [stats, setStats] = useState({ wpm: 0, charCount: 0, goalProgress: 0 });
  const [readingTime, setReadingTime] = useState<number>(0);
  const [lastKeystroke, setLastKeystroke] = useState(Date.now());
  const lastContentRef = useRef<string>(initialContent || "");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [saveStatus, setSaveStatus] = useState<string>("Saved");
  const { showToast } = useToast();
  const { user } = useAuth() as any;

  const checkPremiumAI = () => {
    if (user?.ai_tier === "PREMIUM" || user?.role === "admin") return true;
    showToast("AI access is not available", "error");
    return false;
  };

  const [isExportingWord, setIsExportingWord] = useState(false);
  const [tocData, setTocData] = useState<
    { id: string; text: string; level: number }[]
  >([]);
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [isFinding, setIsFinding] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<number>(1);
  const [localText, setLocalText] = useState(initialContent || "");
  const [showTranslateModal, setShowTranslateModal] = useState(false);
  const [targetLang, setTargetLang] = useState("English");
  const [isTranslating, setIsTranslating] = useState(false);
  const [originalContentForUndo, setOriginalContentForUndo] = useState<
    string | null
  >(null);
  const [tags, setTags] = useState<string[]>([]);
  const latexValueRef = useRef<string>(initialContent || "");

  useEffect(() => {
    if (!documentId) return;
    const authToken = getToken();
    if (!authToken) return;
    const wsUrl = `${(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace("http", "ws")}/ws/crdt/${documentId}`;
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl, ["doclib", authToken]);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "DOCUMENT_UPDATED") {
            if (contentFormat === "latex") {
              latexValueRef.current = data.content;
              setLocalText(data.content);
            } else if (editorRef.current) {
              const parsedContent = (
                typeof data.content === "string"
                  ? JSON.parse(data.content)
                  : data.content
              ) as WordOutputData;
              if (parsedContent.wordSettings)
                registerWordSettings(
                  editorRef.current,
                  parsedContent.wordSettings,
                );
              editorRef.current.render(sanitizeEditorData(parsedContent));
            }
          }
        } catch (err) {
          setOnlineUsers((prev) => prev);
        }
      };
      ws.onopen = () => setOnlineUsers(2);
      ws.onclose = () => setOnlineUsers(1);
    } catch (e) {
      console.error("WebSocket Error", e);
    }
    return () => {
      ws?.close();
    };
  }, [contentFormat, documentId]);

  const handleGrammarCheck = async () => {
    if (!checkPremiumAI()) return;
    if (!editorRef.current) return;
    try {
      const data = await editorRef.current.save();
      let text = "";
      data.blocks.forEach((b: any) => {
        if (b.data?.text) text += b.data.text + " ";
      });
      if (!text || text.length < 50) {
        showToast("More content is required", "info");
        return;
      }
      showToast("Analyzing grammar", "info");
      const res = await grammarCheckAPI(text);
      if (res.data) {
        showToast(`Grammar confidence score: ${res.data.score}/100`, "success");
        if (res.data.corrected_text) {
          editorRef.current.blocks.insert("paragraph", {
            text: `<i>[Grammar suggestion]: ${res.data.corrected_text}</i>`,
          });
        }
      }
    } catch (err: any) {
      showToast(err.message || "AI service connection failed", "error");
    }
  };

  const handleCompilePreview = async () => {
    if (!editorRef.current) return;
    setIsCompiling(true);
      showToast("Exporting LaTeX", "info");
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
        showToast("Compilation input is required", "info");
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
      showToast("LaTeX export completed", "success");
    } catch (err: any) {
      showToast(err.message || "LaTeX export failed", "error");
      setIsCompiling(false);
    }
  };

  const handleExportWord = async () => {
    if (!documentId) return;
    setIsExportingWord(true);
      showToast("Exporting Word document", "info");
    try {
      const { exportToWordAPI } =
        await import("@/features/compilation/services/editorjs.service");
      const blob = await exportToWordAPI(documentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DocLib_${documentId}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      showToast("Word export completed", "success");
    } catch (err: any) {
      showToast(err.message || "Word export failed", "error");
    } finally {
      setIsExportingWord(false);
    }
  };

  const executeFindReplace = async () => {
    if (!documentId || !findText) return;
    setIsFinding(true);
    try {
      await globalFindReplaceAPI(documentId, findText, replaceText, false);
      showToast("Text replacement completed", "success");
      setShowFindReplace(false);
    } catch (err: any) {
      showToast(err.message || "Text replacement failed", "error");
    } finally {
      setIsFinding(false);
    }
  };

  const handleSynonyms = async () => {
    if (!checkPremiumAI()) return;
    if (!editorRef.current) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      let text = data.blocks.map((b: any) => b.data?.text || "").join(" ");

      const selection = window.getSelection();
      const targetWord = selection?.toString().trim();

      if (!targetWord || targetWord.split(" ").length > 3) {
        showToast(
          "The input may contain at most three words",
          "info",
        );
        setIsSuggesting(false);
        return;
      }

      const res = await getSynonymsAPI(targetWord);
      const synonyms = res.data?.synonyms || [];
      if (synonyms.length > 0) {
        showToast(`Synonyms for "${targetWord}": ${synonyms.join(", ")}`, "info");
      } else {
        showToast("No synonyms found", "info");
      }
    } catch (err: any) {
      showToast(err.message || "Synonym lookup failed", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  const fetchSidebarData = useCallback(async () => {
    if (!documentId || activeSidebar === "none") return;
    setLoadingSidebar(true);
    try {
      if (activeSidebar === "history") {
        const { getDocumentVersionsAPI } =
          await import("@/features/content/services/version.service");
        const data = await getDocumentVersionsAPI(documentId);
        setSidebarData(data || []);
      } else if (activeSidebar === "comments") {
        setSidebarData(await getInlineCommentsAPI(documentId));
      }
    } catch (err: any) {
      showToast("Table of contents extraction failed", "error");
    } finally {
      setLoadingSidebar(false);
    }
  }, [documentId, activeSidebar, showToast]);

  useEffect(() => {
    fetchSidebarData();
  }, [fetchSidebarData]);

  const handleConsistencyCheck = async () => {
    if (!checkPremiumAI()) return;
    if (!editorRef.current || !documentId) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      const text = data.blocks.map((b) => b.data?.text || "").join(" ");
      const contextText = text.length > 3000 ? text.slice(-3000) : text;
      const result = await peerReviewAPI(contextText, ["consistency"]);
      const conflicts =
        result.data?.conflicts || result.conflicts || result.data?.issues || [];
      if (conflicts.length > 0) {
        showToast(`Content consistency conflict: ${conflicts[0]}`, "error");
      } else {
        showToast("Content consistency check passed", "success");
      }
    } catch (err: any) {
      showToast("Content consistency check failed", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleTranslate = async () => {
    if (!checkPremiumAI()) return;
    if (!editorRef.current && contentFormat === "json") return;
    setIsTranslating(true);
    setShowTranslateModal(false);
    showToast(`Translating to ${targetLang}`, "info");

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
          showToast("Translation completed", "success");
        }
      } else {
        if (!editorRef.current) return;
        const data = attachWordSettings(
          editorRef.current,
          await editorRef.current.save(),
        );
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
        const sanitizedData = sanitizeEditorData(data);
        await editorRef.current.render(sanitizedData);
        if (onSave) onSave(JSON.stringify(sanitizedData));
        showToast("Block translation completed", "success");
      }
    } catch (err: any) {
      showToast("Translation failed: " + err.message, "error");
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
      const data = sanitizeEditorData(JSON.parse(originalContentForUndo));
      await editorRef.current.render(data);
      if (onSave) onSave(JSON.stringify(data));
    }
    setOriginalContentForUndo(null);
    showToast("Original content restored", "success");
  };

  return (
    <div
      className={`flex flex-col w-full h-full bg-white relative font-sans ${isZenMode ? "fixed inset-0 z-50" : ""}`}
    >
      {!isZenMode && (
        <div className="flex justify-between items-center border-b border-zinc-200 p-3 gap-4">
          <div className="flex flex-1 overflow-x-auto no-scrollbar gap-2 items-center">
            {contentFormat !== "latex" && (
              <WordCommandPalette
                editorRef={editorRef}
                onSave={onSave}
                showToast={showToast as any}
              />
            )}
            <button
              onClick={handleSynonyms}
              disabled={isSuggesting}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              Synonyms
            </button>

            <button
              onClick={handleConsistencyCheck}
              disabled={isSuggesting}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 flex items-center gap-1.5"
            >
              <Network className="w-3.5 h-3.5" />
              Check consistency
            </button>
            <button
              onClick={handleGrammarCheck}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 flex items-center gap-1.5"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              Check grammar
            </button>
            <button
              onClick={handleCompilePreview}
              disabled={isCompiling}
              className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50"
            >
              {isCompiling ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Binary className="w-3.5 h-3.5" />
              )}
              Export LaTeX
            </button>

            <button
              onClick={() => setShowFindReplace(!showFindReplace)}
              className={`px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 ${showFindReplace ? "bg-black text-white border-black hover:bg-zinc-800" : ""}`}
            >
              <Search className="w-3.5 h-3.5" />
              Find and replace
            </button>

            <div className="w-px h-6 bg-zinc-200 mx-1 shrink-0" />

            <button
              onClick={() =>
                originalContentForUndo
                  ? handleRevertTranslation()
                  : setShowTranslateModal(true)
              }
              disabled={isTranslating}
              className={`px-4 py-1.5 border border-zinc-200 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 whitespace-nowrap shrink-0 rounded-lg hover:bg-zinc-50 ${originalContentForUndo ? "bg-amber-50 text-amber-600 border-amber-200 hover:bg-amber-100" : "text-zinc-600"}`}
            >
              {isTranslating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Languages className="w-3.5 h-3.5" />
              )}
              {originalContentForUndo ? "Original" : "Translate"}
            </button>
          </div>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={() => setIsPreview(!isPreview)}
              className={`p-1.5 border ${isPreview ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}  `}
              title="Toggle PDF preview"
            >
              <FileText className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                setActiveSidebar(
                  activeSidebar === "comments" ? "none" : "comments",
                )
              }
              className={`p-1.5 border ${activeSidebar === "comments" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}  `}
            >
              <MessageSquare className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                setActiveSidebar(activeSidebar === "toc" ? "none" : "toc")
              }
              className={`p-1.5 border ${activeSidebar === "toc" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}`}
              title="Table of contents"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                setActiveSidebar(
                  activeSidebar === "history" ? "none" : "history",
                )
              }
              className={`p-1.5 border ${activeSidebar === "history" ? "bg-black text-white border-black" : "border-zinc-200 text-zinc-600"}`}
              title="Version history"
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
                <span className="text-xs font-bold uppercase tracking-tight">
                  Find and replace
                </span>
                <button
                  onClick={() => setShowFindReplace(false)}
                  className="text-zinc-400 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="flex gap-2 items-center">
                <input
                  type="text"
                  placeholder=""
                  className="px-3 py-1.5 text-xs border border-zinc-200 focus:outline-none"
                  value={findText}
                  onChange={(e) => setFindText(e.target.value)}
                />
                <span className="text-xs text-zinc-400">{"->"}</span>
                <input
                  type="text"
                  placeholder=""
                  className="px-3 py-1.5 text-xs border border-zinc-200 focus:outline-none"
                  value={replaceText}
                  onChange={(e) => setReplaceText(e.target.value)}
                />
                <button
                  onClick={executeFindReplace}
                  disabled={isFinding || !findText}
                  className="px-4 py-1.5 bg-black text-white text-xs font-bold"
                >
                  {isFinding ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    "Replace all"
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {showTranslateModal && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 bg-white border border-zinc-200 p-4 shadow-xl rounded-lg">
            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-tight">
                  Translate document
                </span>
                <button
                  onClick={() => setShowTranslateModal(false)}
                  className="text-zinc-400 p-1 hover:bg-zinc-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="flex gap-2 items-center">
                <span className="text-xs text-zinc-600 font-medium">To</span>
                <select
                  className="px-3 py-1.5 text-xs border border-zinc-200 rounded focus:outline-none bg-white"
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                >
                  <option value="English">English</option>
                  <option value="Vietnamese">Vietnamese</option>
                  <option value="French">French</option>
                  <option value="Chinese">Chinese</option>
                  <option value="Japanese">Japanese</option>
                  <option value="Korean">Korean</option>
                </select>
                <button
                  onClick={handleTranslate}
                  disabled={isTranslating}
                  className="px-4 py-1.5 bg-black text-white text-xs font-bold rounded-md hover:bg-zinc-800"
                >
                  Translate
                </button>
              </div>
            </div>
          </div>
        )}

        <div
          className={`h-full overflow-y-auto flex justify-center bg-white ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"}`}
        >
          {contentFormat === "latex" ? (
            <LatexEditor
              initialContent={localText}
              documentId={documentId}
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
                showToast={showToast as any}
                editorRef={editorRef}
              />
            </div>
          )}
        </div>

        {activeSidebar !== "none" && (
          <div className="w-1/3 h-full border-l border-zinc-200 bg-zinc-50 flex flex-col">
            <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-white">
              <span className="text-xs font-bold uppercase tracking-tight">
                {activeSidebar === "comments"
                  ? "Inline comments"
                  : activeSidebar === "history"
                    ? "Version history"
                    : "Table of contents"}
              </span>
              <button
                onClick={() => setActiveSidebar("none")}
                className="p-1 text-zinc-400 "
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 p-4 overflow-y-auto no-scrollbar">
              <div className="flex flex-col gap-3">
                {loadingSidebar ? (
                  <div className="py-12 flex justify-center">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
                  </div>
                ) : activeSidebar === "toc" ? (
                  tocData.length === 0 ? (
                    <div className="p-8 border border-zinc-200 bg-white text-xs text-zinc-400 text-center italic">
                      No headings found
                    </div>
                  ) : (
                    tocData.map((item, idx) => (
                      <div
                        key={item.id || `toc-${idx}`}
                        className="p-2 border border-zinc-200 bg-white text-xs text-black font-medium cursor-pointer"
                        style={{ marginLeft: `${(item.level - 1) * 16}px` }}
                        onClick={() => {
                          const elements =
                            document.querySelectorAll(".ce-header");
                          for (let i = 0; i < elements.length; i++) {
                            if (elements[i].textContent?.includes(item.text)) {
                              elements[i].scrollIntoView({
                                behavior: "smooth",
                                block: "start",
                              });
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
                    No data available
                  </div>
                ) : activeSidebar === "history" ? (
                  sidebarData.map((v, idx) => (
                    <div
                      key={v.id || `history-${idx}`}
                      className="p-4 border border-zinc-200 bg-white space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase">
                          {v.created_at
                            ? new Date(v.created_at).toLocaleString("vi-VN")
                            : ""}
                        </span>
                        <Clock className="w-3 h-3 text-zinc-300" />
                      </div>
                      <p className="text-xs font-medium text-black">
                        Saved by {v.author_name || "System"}
                      </p>
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
                          const elements =
                            document.querySelectorAll(".ce-block");
                          for (let i = 0; i < elements.length; i++) {
                            if (elements[i].textContent?.includes(searchText)) {
                              elements[i].scrollIntoView({
                                behavior: "smooth",
                                block: "center",
                              });
                              elements[i].classList.add("bg-zinc-100", "", "");
                              setTimeout(
                                () =>
                                  elements[i].classList.remove("bg-zinc-100"),
                                2000,
                              );
                              break;
                            }
                          }
                        }
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-[10px] font-bold text-zinc-400 uppercase">
                          {c.created_at
                            ? new Date(c.created_at).toLocaleString("vi-VN")
                            : ""}
                        </span>
                        <MessageSquare className="w-3 h-3 text-zinc-300" />
                      </div>
                      <p className="text-xs font-bold text-black border-b border-zinc-100 pb-1">
                        {c.user_name || "Guest"}
                      </p>
                      <p className="text-xs font-medium text-black">
                        {c.text || c.content}
                      </p>
                      <div className="pt-2 flex justify-end">
                        <button className="text-[10px] font-bold text-zinc-400  uppercase">
                          Resolve
                        </button>
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
              <span className="font-bold uppercase tracking-tight">
                PDF preview
              </span>
              <a
                href={previewPdfUrl}
                download="doclib-preview.pdf"
                className="p-1.5 text-zinc-300 "
              >
                <Download className="w-4 h-4" />
              </a>
            </div>
            <div className="flex-1 bg-zinc-100 p-4">
              <iframe
                src={previewPdfUrl}
                className="w-full h-full bg-white border border-zinc-200"
              />
            </div>
          </div>
        )}
      </div>

      <div className="h-10 border-t border-[var(--border-strong)] bg-white px-6 flex items-center justify-between shrink-0 z-30">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-[var(--ink-muted)]">Speed</span>
            <span className="text-[13px] font-medium text-[var(--ink)]">
              {stats.wpm} WPM
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-[var(--ink-muted)]">Characters</span>
            <span className="text-[13px] font-medium text-[var(--ink)]">
              {stats.charCount}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-[var(--ink-muted)]">Reading time</span>
            <span className="text-[13px] font-medium text-[var(--ink)]">
              {readingTime} minutes
            </span>
          </div>
          {tags.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-[13px] text-[var(--ink-muted)]">Tags</span>
              <div className="flex gap-1.5">
                {tags.map((t, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-[var(--surface-quiet)] rounded-md text-[13px] text-[var(--ink-muted)] font-medium"
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${onlineUsers > 1 ? "bg-[#34C759]" : "bg-[var(--border-strong)]"}`}
            ></span>
            <span className="text-[13px] text-[var(--ink-muted)]">Collaboration</span>
            <span className="text-[13px] font-medium text-[var(--ink)]">
              {onlineUsers > 1
                ? `${onlineUsers} online`
                : "Online"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-[var(--ink-muted)]">Status</span>
            <span className="text-[13px] font-medium text-[var(--ink)]">
              {saveStatus}
            </span>
          </div>
          <div className="w-32 h-1.5 bg-[var(--border)] rounded-full relative overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-[var(--brand)] transition-all duration-300"
              style={{
                width: `${Math.min(100, (stats.charCount / parseInt(typeof window !== "undefined" ? localStorage.getItem("doclib_daily_goal") || "5000" : "5000")) * 100)}%`,
              }}
            />
          </div>
          <span className="text-[13px] text-[var(--ink-muted)]">Daily goal</span>
        </div>
      </div>
    </div>
  );
}
