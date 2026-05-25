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
import { Sparkles, CheckSquare, FileText, Download, Loader2, Maximize2, Minimize2, MessageSquare, History, Wand2, X, Brain, Bot, ShieldCheck, Languages, Binary, CheckCheck, Scale, PenLine, Network, Clock, Search, FileEdit } from "lucide-react";

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

  const [isExportingWord, setIsExportingWord] = useState(false);
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [showPageSetup, setShowPageSetup] = useState(false);
  const [pageMargin, setPageMargin] = useState(48);
  const [pageHeader, setPageHeader] = useState("");
  const [pageFooter, setPageFooter] = useState("");
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [isFinding, setIsFinding] = useState(false);

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
      const Checklist = (await import("@editorjs/checklist")).default;
      const LinkTool = (await import("@editorjs/link")).default;
      const Strikethrough = (await import("@sotaproject/strikethrough")).default;
      const AlignmentTune = (await import("editor-js-alignment-tune")).default;
      const TextColor = (await import("editorjs-text-color-plugin")).default;
      const Undo = (await import("editorjs-undo")).default;
      const DragDrop = (await import("editorjs-drag-drop")).default;
      const Columns = (await import("@calumk/editorjs-columns")).default;
      const AttachesTool = (await import("@editorjs/attaches")).default;
      const Tooltip = (await import("editorjs-tooltip")).default;
      const Alert = (await import("editorjs-alert")).default;
      const Button = (await import("editorjs-button")).default;
      const MermaidTool = (await import("editorjs-mermaid")).default;
      const LatexTool = (await import("editorjs-latex")).default;
      const IndentTune = (await import("editorjs-indent-tune")).default;
      const Spoiler = (await import("editorjs-inline-spoiler-tool")).default;
      const ChangeCase = (await import("editorjs-change-case")).default;
      const TextVariantTune = (await import("@editorjs/text-variant-tune")).default;
      const NestedList = (await import("@editorjs/nested-list")).default;
      const Codebox = (await import("@bomdi/codebox")).default;
      const NestedChecklist = (await import("@calumk/editorjs-nested-checklist")).default;
      const Anchor = (await import("@coolbytes/editorjs-anchor")).default;
      const GroupImage = (await import("@cychann/editorjs-group-image")).default;
      const AdvancedImage = (await import("@editorjs/image")).default;
      const LinkAutocomplete = (await import("@editorjs/link-autocomplete")).default;
      const Audio = (await import("@furison-tech/editorjs-audio")).default;
      const TextStyle = (await import("@skchawala/editorjs-text-style")).default;
      const Video = (await import("@weekwood/editorjs-video")).default;
      const Annotation = (await import("editorjs-annotation")).default;
      const Chart = (await import("editorjs-chart")).default;
      const Gallery = (await import("editorjs-gallery")).default;
      const Hyperlink = (await import("editorjs-hyperlink")).default;
      const TelegramPost = (await import("editorjs-telegram-post")).default;
      const Title = (await import("title-editorjs")).default;
      const StyleTune = (await import("editorjs-style")).default;
      const Codecup = (await import("@calumk/editorjs-codecup")).default;
      const ParagraphLinebreakable = (await import("@calumk/editorjs-paragraph-linebreakable")).default;
      const CoolbytesDelimiter = (await import("@coolbytes/editorjs-delimiter")).default;
      const CychannQuote = (await import("@cychann/editorjs-quote")).default;
      const AudioPlayer = (await import("editorjs-audio-player")).default;
      const ChartJS = (await import("editorjs-chartjs")).default;
      const CollapsibleBlock = (await import("editorjs-collapsible-block")).default;
      const ColorPicker = (await import("editorjs-color-picker")).default;
      const EditorjsComment = (await import("editorjs-comment")).default;
      const ImageCropResize = (await import("editorjs-image-crop-resize")).default;
      const Inline = (await import("editorjs-inline")).default;
      const InlineHotkey = (await import("editorjs-inline-hotkey")).default;
      const InlineImage = (await import("editorjs-inline-image")).default;
      const InlineTemplate = (await import("editorjs-inline-template")).default;
      const InlineTool = (await import("editorjs-inline-tool")).default;
      const MultiBlockSelection = (await import("editorjs-multiblock-selection-plugin")).default;
      const Notice = (await import("editorjs-notice")).default;
      const Footnotes = (await import("editorjs-footnotes")).default;
      const BreakLine = (await import("editorjs-break-line")).default;
      const Gist = (await import("editorjs-github-gist-plugin")).default;
      const PageBreak = (await import("editorjs-page-break")).default;
      const MathTool = (await import("editorjs-math")).default;
      const Personality = (await import("@editorjs/personality")).default;
      const Carousel = (await import("editorjs-carousel")).default;
      const PdfTool = (await import("editorjs-pdf")).default;
      const Quiz = (await import("editorjs-quiz")).default;
      const Superscript = (await import("editorjs-superscript")).default;
      const Subscript = (await import("editorjs-subscript")).default;

      if (cancelled) {
        holderDiv.remove();
        return;
      }

      let data: OutputData = { blocks: [{ type: "paragraph", data: { text: "" } }] };
      if (initialContent) {
        try {
          const parsed = JSON.parse(initialContent);
          if (parsed.blocks && parsed.blocks.length > 0) data = parsed;
          if (parsed.pageSetup) {
            setPageMargin(parsed.pageSetup.margin || 48);
            setPageHeader(parsed.pageSetup.header || "");
            setPageFooter(parsed.pageSetup.footer || "");
          }
        } catch (err: any) {
          const blocks = initialContent.split('\\n').map(line => ({
            type: "paragraph",
            data: { text: line }
          }));
          data = { blocks: blocks.length > 0 ? blocks : [{ type: "paragraph", data: { text: "" } }] };
        }
      }

      const tools: Record<string, any> = {};
      if (AlignmentTune) tools.alignment = { class: AlignmentTune };
      if (IndentTune) tools.indent = { class: IndentTune };
      if (TextVariantTune) tools.textVariant = TextVariantTune;
      if (StyleTune) tools.style = StyleTune;
      
      const commonTunes = ['alignment', 'indent', 'style'];
      
      if (Title) tools.title = { class: Title, inlineToolbar: true };
      if (Header) tools.header = { class: Header, inlineToolbar: true, tunes: commonTunes };
      if (ParagraphLinebreakable) tools.paragraph = { class: ParagraphLinebreakable, inlineToolbar: true, tunes: [...commonTunes, 'textVariant'] };
      if (NestedList) tools.list = { class: NestedList, inlineToolbar: true, tunes: ['indent'] };
      if (NestedChecklist) tools.checklist = { class: NestedChecklist, inlineToolbar: true, tunes: ['indent'] };
      if (CychannQuote) tools.quote = { class: CychannQuote, inlineToolbar: true, tunes: ['alignment'] };
      if (Warning) tools.warning = Warning;
      if (Alert) tools.alert = { class: Alert, inlineToolbar: true };
      if (Notice) tools.notice = Notice;
      if (CollapsibleBlock) tools.collapsible = { class: CollapsibleBlock, inlineToolbar: true };
      if (Marker) tools.marker = Marker;
      if (Codebox) tools.code = Codebox;
      if (CoolbytesDelimiter) tools.delimiter = CoolbytesDelimiter;
      if (InlineCode) tools.inlineCode = InlineCode;
      if (LinkAutocomplete) tools.linkTool = LinkAutocomplete;
      if (Hyperlink) tools.hyperlink = { class: Hyperlink };
      if (Embed) tools.embed = Embed;
      if (Table) tools.table = Table;
      if (AdvancedImage) tools.image = AdvancedImage;
      if (ImageCropResize) tools.imageCrop = ImageCropResize;
      if (InlineImage) tools.inlineImage = InlineImage;
      if (GroupImage) tools.groupImage = GroupImage;
      if (Gallery) tools.gallery = Gallery;
      if (AttachesTool) tools.attaches = { class: AttachesTool };
      if (Button) tools.button = { class: Button };
      if (MermaidTool) tools.mermaid = MermaidTool;
      if (LatexTool) tools.latex = LatexTool;
      if (Audio) tools.audio = Audio;
      if (AudioPlayer) tools.audioPlayer = AudioPlayer;
      if (Video) tools.video = Video;
      if (Chart) tools.chart = Chart;
      if (ChartJS) tools.chartjs = ChartJS;
      if (Anchor) tools.anchor = Anchor;
      if (TelegramPost) tools.telegramPost = TelegramPost;
      if (Columns) tools.columns = { class: Columns, config: { tools: { header: Header, paragraph: ParagraphLinebreakable || Paragraph, list: NestedList || ListTool, image: AdvancedImage || SimpleImage, quote: CychannQuote || Quote } } };
      if (Layout) tools.layout = { class: Layout, config: { tools: { header: Header, paragraph: ParagraphLinebreakable || Paragraph, list: NestedList || ListTool, image: AdvancedImage || SimpleImage, quote: CychannQuote || Quote } } };
      if (RawTool) tools.raw = RawTool;
      if (UnderlineTool) tools.underline = UnderlineTool;
      if (Strikethrough) tools.strikethrough = Strikethrough;
      
      if (Footnotes) tools.footnotes = Footnotes;
      if (BreakLine) tools.breakLine = { class: BreakLine, inlineToolbar: true };
      if (Gist) tools.gist = Gist;
      if (PageBreak) tools.pageBreak = { class: PageBreak, inlineToolbar: true };
      if (MathTool) tools.math = MathTool;
      if (Personality) tools.personality = { class: Personality };
      if (Carousel) tools.carousel = { class: Carousel };
      if (PdfTool) tools.pdf = PdfTool;
      if (Quiz) tools.quiz = Quiz;
      if (Superscript) tools.superscript = Superscript;
      if (Subscript) tools.subscript = Subscript;
      if (TextStyle) tools.textStyle = TextStyle;
      if (TextColor) tools.textColor = { class: TextColor, inlineToolbar: true };
      if (ColorPicker) tools.colorPicker = { class: ColorPicker, inlineToolbar: true };
      if (Tooltip) tools.tooltip = { class: Tooltip, inlineToolbar: true };
      if (Spoiler) tools.spoiler = { class: Spoiler };
      if (Annotation) tools.annotation = Annotation;
      if (ChangeCase) tools.changeCase = { class: ChangeCase };
      if (EditorjsComment) tools.comment = EditorjsComment;
      if (Inline) tools.inline = Inline;
      if (InlineHotkey) tools.inlineHotkey = InlineHotkey;
      if (InlineTemplate) tools.inlineTemplate = InlineTemplate;
      if (InlineTool) tools.inlineTool = InlineTool;
      
      const editor = new EditorJSModule({
        holder: holderDiv,
        tools,
        data,
        placeholder: "Bắt đầu soạn thảo",
        onReady: () => {
          if (Undo) new Undo({ editor });
          if (DragDrop) new DragDrop(editor);
          if (MultiBlockSelection) new MultiBlockSelection(editor);
        },
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
            const payload = {
               ...saved,
               pageSetup: { margin: pageMargin, header: pageHeader, footer: pageFooter }
            };
            const val = JSON.stringify(payload);
            lastContentRef.current = val;
            onSave?.(val);
          } catch (err: any) { 
            showToast("Lỗi khi tự động lưu nội dung: " + (err.message || ""), "error"); 
          }
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
        const blocks = initialContent.split('\\n').map(line => ({
          type: "paragraph",
          data: { text: line }
        }));
        data = { blocks: blocks.length > 0 ? blocks : [{ type: "paragraph", data: { text: "" } }] };
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
        <div className="flex justify-between items-center border-b border-zinc-200 p-3">
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
              <button
                onClick={handleExportWord}
                disabled={isExportingWord}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5"
              >
                {isExportingWord ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileEdit className="w-3.5 h-3.5" />}
                Xuất ra Word
              </button>
              <button
                onClick={() => setShowFindReplace(!showFindReplace)}
                className={`px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5 ${showFindReplace ? "bg-black text-white border-black" : ""}`}
              >
                <Search className="w-3.5 h-3.5" />
                Tìm & Thay thế
              </button>
              <button
                onClick={() => setShowPageSetup(true)}
                className="px-4 py-1.5 border border-zinc-200 text-zinc-600 text-xs font-bold active:scale-[0.98] flex items-center gap-1.5"
              >
                <FileEdit className="w-3.5 h-3.5" />
                Bố cục trang
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

        <div className={`h-full overflow-y-auto flex justify-center bg-zinc-50 py-8 ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"}`}>
          <div 
            className="relative w-[800px] max-w-full bg-white border border-zinc-200 flex flex-col"
            style={{ padding: `${pageMargin}px`, minHeight: '1056px' }}
          >
            {pageHeader && (
              <div className="absolute top-4 left-0 right-0 text-center text-xs text-zinc-400 font-medium whitespace-pre-wrap">
                {pageHeader}
              </div>
            )}
            <div ref={containerRef} className="flex-1 w-full" />
            {pageFooter && (
              <div className="absolute bottom-4 left-0 right-0 text-center text-xs text-zinc-400 font-medium whitespace-pre-wrap">
                {pageFooter}
              </div>
            )}
          </div>
        </div>
        
        {activeSidebar !== "none" && (
          <div className="w-1/3 h-full border-l border-zinc-200 bg-zinc-50 flex flex-col">
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
    
      {showPageSetup && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm">
          <div className="bg-white p-6 border border-zinc-200 w-[400px]">
            <h3 className="text-sm font-bold uppercase tracking-tight mb-4">Bố cục trang</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] text-zinc-400 font-bold uppercase mb-1">Căn lề (Margin - px)</label>
                <input
                  type="number"
                  value={pageMargin}
                  onChange={(e) => {
                    setPageMargin(Number(e.target.value));
                    if (editorRef.current) {
                      editorRef.current.save().then((saved: any) => {
                        const payload = { ...saved, pageSetup: { margin: Number(e.target.value), header: pageHeader, footer: pageFooter } };
                        const val = JSON.stringify(payload);
                        lastContentRef.current = val;
                        onSave?.(val);
                      });
                    }
                  }}
                  className="w-full px-3 py-2 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black"
                />
              </div>
              <div>
                <label className="block text-[10px] text-zinc-400 font-bold uppercase mb-1">Tiêu đề (Header)</label>
                <input
                  type="text"
                  value={pageHeader}
                  onChange={(e) => {
                    setPageHeader(e.target.value);
                    if (editorRef.current) {
                      editorRef.current.save().then((saved: any) => {
                        const payload = { ...saved, pageSetup: { margin: pageMargin, header: e.target.value, footer: pageFooter } };
                        const val = JSON.stringify(payload);
                        lastContentRef.current = val;
                        onSave?.(val);
                      });
                    }
                  }}
                  placeholder="Ví dụ Luận văn"
                  className="w-full px-3 py-2 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black"
                />
              </div>
              <div>
                <label className="block text-[10px] text-zinc-400 font-bold uppercase mb-1">Chân trang (Footer)</label>
                <input
                  type="text"
                  value={pageFooter}
                  onChange={(e) => {
                    setPageFooter(e.target.value);
                    if (editorRef.current) {
                      editorRef.current.save().then((saved: any) => {
                        const payload = { ...saved, pageSetup: { margin: pageMargin, header: pageHeader, footer: e.target.value } };
                        const val = JSON.stringify(payload);
                        lastContentRef.current = val;
                        onSave?.(val);
                      });
                    }
                  }}
                  placeholder="Ví dụ Trang 1"
                  className="w-full px-3 py-2 border border-zinc-200 text-xs font-medium focus:outline-none focus:border-black"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowPageSetup(false)}
                className="px-4 py-2 bg-black text-white text-xs font-bold active:scale-[0.98]"
              >
                Xác nhận
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
