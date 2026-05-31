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
    getVersionDiffAPI,
    summarizeDocumentAPI,
    extractSmartTagsAPI,
    exportToEpubAPI,
    checkDeepPlagiarismAPI
} from "@/services/editor.service";
import { grammarCheckAPI, getSynonymsAPI } from "@/services/inference.service";
import { API_URL, getAuthHeaders } from "@/services/authentication.service";
import { Sparkles, CheckSquare, FileText, Download, Loader2, Maximize2, Minimize2, MessageSquare, History, Wand2, X, Brain, Bot, ShieldCheck, Languages, Binary, CheckCheck, Scale, PenLine, Network, Clock, Search, FileEdit, List } from "lucide-react";

interface EditorProps {
  documentId?: string;
  initialContent?: string;
  contentFormat?: string;
  onSave?: (data: string) => void;
}

class PremiumTune {
  api: any;
  data: any;
  block: any;
  wrapper: HTMLElement | null = null;
  static get isTune() { return true; }
  constructor({ api, data, config, block }: any) {
    this.api = api;
    this.data = data || { isPremium: false };
    this.block = block;
  }
  render() {
    const wrapper = document.createElement('div');
    wrapper.classList.add('ce-popover-item');
    wrapper.innerHTML = `<div class="ce-popover-item__icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div><div class="ce-popover-item__title">Đánh dấu Trả phí</div>`;
    wrapper.addEventListener('click', () => {
      this.data.isPremium = !this.data.isPremium;
      wrapper.classList.toggle('ce-popover-item--active', this.data.isPremium);
      const idx = this.api.blocks.getCurrentBlockIndex();
      if (idx !== undefined && idx >= 0) {
        const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
        if (blockContent) {
          if (this.data.isPremium) {
            blockContent.style.border = '1px dashed black';
            blockContent.style.opacity = '0.8';
          } else {
            blockContent.style.border = '';
            blockContent.style.opacity = '';
          }
        }
      }
    });
    setTimeout(() => {
      if (this.data.isPremium) {
        wrapper.classList.add('ce-popover-item--active');
        const idx = this.api.blocks.getCurrentBlockIndex();
        if (idx !== undefined && idx >= 0) {
          const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
          if (blockContent) {
            blockContent.style.border = '1px dashed black';
            blockContent.style.opacity = '0.8';
          }
        }
      }
    }, 100);
    this.wrapper = wrapper;
    return wrapper;
  }
  save() { return this.data; }
}



export default function Editor({
  documentId,
  initialContent,
  contentFormat = "json",
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

  useEffect(() => {
    if (!documentId) return;
    let wsUrl = API_URL.replace("http", "ws") + `/soan-thao/o-cam-crdt/${documentId}`;
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

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.classList.contains("ce-paragraph")) {
        const plusButton = document.querySelector(".ce-toolbar__plus") as HTMLElement;
        if (plusButton) plusButton.click();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    if (contentFormat === "latex") {
      setLocalText(initialContent || "");
      return;
    }

    const holderDiv = document.createElement("div");
    holderDiv.className = "prose prose-zinc max-w-4xl mx-auto min-h-full";
    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(holderDiv);

    let cancelled = false;

    const init = async () => {
      const EditorJSModule = (await import("@editorjs/editorjs")).default;
      const DocLibHeader = (await import("./DocLibHeader")).default;
      const DocLibParagraph = (await import("./DocLibParagraph")).default;
      const DocLibList = (await import("./DocLibList")).default;
      const DocLibQuote = (await import("./DocLibQuote")).default;
      const DocLibWarning = (await import("./DocLibWarning")).default;
      const DocLibMarker = (await import("./DocLibMarker")).default;
      const DocLibCode = (await import("./DocLibCode")).default;
      const DocLibDelimiter = (await import("./DocLibDelimiter")).default;
      const DocLibInlineCode = (await import("./DocLibInlineCode")).default;
      const DocLibEmbed = (await import("./DocLibEmbed")).default;
      const DocLibTable = (await import("./DocLibTable")).default;
      const DocLibSimpleImage = (await import("./DocLibSimpleImage")).default;
      const DocLibRaw = (await import("./DocLibRaw")).default;
      const DocLibUnderline = (await import("./DocLibUnderline")).default;
      const DocLibChecklist = (await import("./DocLibChecklist")).default;
      const DocLibLinkPreview = (await import("./DocLibLinkPreview")).default;
      const DocLibStrikethrough = (await import("./DocLibStrikethrough")).default;
      const DocLibAlignmentTune = (await import("./DocLibAlignment")).default;
      const DocLibColumns = (await import("./DocLibColumns")).default;
      const DocLibFile = (await import("./DocLibFile")).default;
      const DocLibTooltip = (await import("./DocLibTooltip")).default;
      const DocLibAlert = (await import("./DocLibAlert")).default;
      const DocLibButton = (await import("./DocLibButton")).default;
      const DocLibMermaid = (await import("./DocLibMermaid")).default;

      const DocLibLatex = (await import("./DocLibLatex")).default;
      const DocLibColorPicker = (await import("./DocLibTextColor")).default;
      const DocLibIndentTune = (await import("./DocLibIndent")).default;
      const DocLibSpoiler = (await import("./DocLibSpoiler")).default;
      const DocLibChangeCase = (await import("./DocLibChangeCase")).default;
      const DocLibTextVariant = (await import("./DocLibTextVariant")).default;
      const DocLibCodeBox = (await import("./DocLibCodeBox")).default;
      const DocLibAnchor = (await import("./DocLibAnchor")).default;
      const DocLibGroupImage = (await import("./DocLibGroupImage")).default;
      const DocLibImage = (await import("./DocLibImage")).default;
      const DocLibAudio = (await import("./DocLibAudio")).default;
      const DocLibTextStyle = (await import("./DocLibTextStyle")).default;
      const DocLibVideo = (await import("./DocLibVideo")).default;
      const DocLibAnnotation = (await import("./DocLibAnnotation")).default;
      const DocLibChart = (await import("./DocLibChart")).default;
      const DocLibGallery = (await import("./DocLibGallery")).default;
      const DocLibHyperlink = (await import("./DocLibHyperlink")).default;
      const DocLibTelegramPost = (await import("./DocLibTelegramPost")).default;
      const DocLibTitle = (await import("./DocLibTitle")).default;
      const DocLibStyleTune = (await import("./DocLibStyleTune")).default;
      const DocLibNestedChecklist = (await import("./DocLibNestedChecklist")).default;

      const DocLibAudioPlayer = (await import("./DocLibAudioPlayer")).default;

      const DocLibComment = (await import("./DocLibComment")).default;
      const DocLibImageCrop = (await import("./DocLibImageCrop")).default;
      const DocLibTemplate = (await import("./DocLibTemplate")).default;
      const DocLibNotice = (await import("./DocLibNotice")).default;
      const DocLibFootnote = (await import("./DocLibFootnote")).default;
      const DocLibBreakLine = (await import("./DocLibBreakLine")).default;
      const DocLibGist = (await import("./DocLibGist")).default;

      const DocLibPersonality = (await import("./DocLibPersonality")).default;
      const DocLibCarousel = (await import("./DocLibCarousel")).default;
      const DocLibQuiz = (await import("./DocLibQuiz")).default;
      const DocLibSuperscript = (await import("./DocLibSuperscript")).default;
      const DocLibSubscript = (await import("./DocLibSubscript")).default;
      const DocLibToggle = (await import("./DocLibToggle")).default;
      
      const DocLibAiText = (await import("./DocLibAiText")).default;

      
      const DocLibDrawing = (await import("./DocLibDrawing")).default;
      const DocLibGif = (await import("./DocLibGif")).default;
      const DocLibImageWithLink = (await import("./DocLibImageWithLink")).default;
      const DocLibFlipbox = (await import("./DocLibFlipbox")).default;
      
      const DocLibNestedList = (await import("./DocLibNestedList")).default;
      const DocLibLinkSearch = (await import("./DocLibLinkSearch")).default;
      const DocLibTimeline = (await import("./DocLibTimeline")).default;
      const DocLibPricing = (await import("./DocLibPricing")).default;
      const DocLibTestimonial = (await import("./DocLibTestimonial")).default;
      const DocLibMath = (await import("./DocLibMath")).default;
      const DocLibKanban = (await import("./DocLibKanban")).default;
      const DocLibCodeMirror = (await import("./DocLibCodeMirror")).default;
      const DocLibUndo = (await import("./DocLibUndo")).default;
      const DocLibDragDrop = (await import("./DocLibDragDrop")).default;
      const DocLibMultiBlockSelection = (await import("./DocLibMultiBlockSelection")).default;
      
      const DocLibCallout = (await import("./DocLibCallout")).default;
      const DocLibBookmark = (await import("./DocLibBookmark")).default;
      const DocLibCountdown = (await import("./DocLibCountdown")).default;
      const DocLibProgressBar = (await import("./DocLibProgressBar")).default;
      const DocLibSteps = (await import("./DocLibSteps")).default;
      const DocLibPoll = (await import("./DocLibPoll")).default;
      const DocLibIframeEmbed = (await import("./DocLibIframeEmbed")).default;
      const DocLibDivider = (await import("./DocLibDivider")).default;
      const DocLibBadge = (await import("./DocLibBadge")).default;
      const DocLibKeyboard = (await import("./DocLibKeyboard")).default;
      
      
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
          const blocks = initialContent.split('\\n').map(line => ({
            type: "paragraph",
            data: { text: line }
          }));
          data = { blocks: blocks.length > 0 ? blocks : [{ type: "paragraph", data: { text: "" } }] };
        }
      }

      const tools: Record<string, any> = {};
      
      tools.premium = { class: PremiumTune };
      const commonTunes = ['textVariant', 'styleTune'];
      if (DocLibAlignmentTune) { tools.alignment = { class: DocLibAlignmentTune }; commonTunes.push('alignment'); }
      tools.indent = { class: DocLibIndentTune }; 
      commonTunes.push('indent');
      if (DocLibStyleTune) { tools.style = DocLibStyleTune; commonTunes.push('style'); }
      
      if (DocLibNotice) { tools.notice = DocLibNotice; commonTunes.push('notice'); }
      if (DocLibAnchor) { tools.anchor = { class: DocLibAnchor, config: { theme: 'light' } }; commonTunes.push('anchor'); }
      const paragraphTunes = [...commonTunes];
      if (DocLibStyleTune) tools.styleTune = DocLibStyleTune;
      if (DocLibTextVariant) tools.textVariant = DocLibTextVariant;
      const indentTunes = ['indent'];
      const alignTunes = DocLibAlignmentTune ? ['alignment'] : [];

      if (DocLibTitle) tools.title = DocLibTitle;
      if (DocLibHeader) {
        tools.header = { class: DocLibHeader, inlineToolbar: true, config: { placeholder: 'Nhập tiêu đề...', levels: [1, 2, 3, 4, 5, 6], defaultLevel: 2 }, tunes: commonTunes };
      }
      
      if (DocLibParagraph) tools.paragraph = { class: DocLibParagraph, inlineToolbar: true, tunes: paragraphTunes };
      if (DocLibQuote) tools.originalQuote = { class: DocLibQuote, inlineToolbar: true };
      if (DocLibWarning) tools.warning = DocLibWarning;
      if (DocLibAlert) tools.alert = { class: DocLibAlert, inlineToolbar: true };
      if (DocLibDelimiter) tools.originalDelimiter = DocLibDelimiter;
      if (DocLibAiText) tools.aiText = DocLibAiText;

      if (DocLibTable) tools.table = { class: DocLibTable, inlineToolbar: true };
      if (DocLibToggle) tools.toggle = { class: DocLibToggle, inlineToolbar: true };
      if (DocLibBreakLine) tools.breakLine = { class: DocLibBreakLine, inlineToolbar: true };
      
      if (DocLibList) tools.list = { class: DocLibList, inlineToolbar: true, tunes: indentTunes };
      if (DocLibChecklist) tools.checklist = { class: DocLibChecklist, inlineToolbar: true, tunes: indentTunes };
      if (DocLibNestedChecklist) tools.nestedChecklist = { class: DocLibNestedChecklist, inlineToolbar: true, tunes: indentTunes };
      
      if (DocLibImage) tools.image = { class: DocLibImage, config: { endpoints: { byFile: '/api/uploadFile', byUrl: '/api/fetchUrl' } } };

      if (DocLibImageCrop) tools.imageCrop = DocLibImageCrop;
      if (DocLibGroupImage) tools.groupImage = DocLibGroupImage;
      if (DocLibGallery) tools.gallery = DocLibGallery;
      if (DocLibCarousel) tools.carousel = DocLibCarousel;
      if (DocLibFile) tools.attaches = { class: DocLibFile };
      if (DocLibEmbed) tools.embed = DocLibEmbed;
      if (DocLibMermaid) tools.mermaid = DocLibMermaid;
      if (DocLibDrawing) tools.drawing = DocLibDrawing;
      if (DocLibGif) tools.gif = DocLibGif;
      if (DocLibImageWithLink) tools.imageWithLink = DocLibImageWithLink;
      if (DocLibFlipbox) tools.flipbox = DocLibFlipbox;
      if (DocLibLatex) {
        tools.latex = DocLibLatex;
      }
      if (DocLibAudio) tools.audio = DocLibAudio;
      if (DocLibAudioPlayer) tools.audioPlayer = DocLibAudioPlayer;
      if (DocLibVideo) tools.video = DocLibVideo;
      if (DocLibTelegramPost) tools.telegramPost = DocLibTelegramPost;
      
      if (DocLibCode) tools.code = DocLibCode;
      if (DocLibRaw) tools.raw = DocLibRaw;
      if (DocLibCodeBox) tools.codeBox = DocLibCodeBox;
      if (DocLibCodeMirror) tools.codeMirror = DocLibCodeMirror;
      if (DocLibGist) tools.gist = DocLibGist;
    


      if (DocLibChart) tools.chart = DocLibChart;
      

      if (DocLibButton) tools.button = DocLibButton;
      

      if (DocLibColumns) tools.columns = DocLibColumns;
      
      if (DocLibNestedList) tools.nestedList = { class: DocLibNestedList, inlineToolbar: true };
      if (DocLibTimeline) tools.timeline = DocLibTimeline;
      if (DocLibPricing) tools.pricing = DocLibPricing;
      if (DocLibTestimonial) tools.testimonial = DocLibTestimonial;
      if (DocLibMath) tools.math = DocLibMath;
      if (DocLibKanban) tools.kanban = DocLibKanban;
      
      if (DocLibCallout) tools.callout = DocLibCallout;
      if (DocLibBookmark) tools.bookmark = DocLibBookmark;
      if (DocLibCountdown) tools.countdown = DocLibCountdown;
      if (DocLibProgressBar) tools.progress = DocLibProgressBar;
      if (DocLibSteps) tools.steps = DocLibSteps;
      if (DocLibPoll) tools.poll = DocLibPoll;
      if (DocLibIframeEmbed) tools.iframe = DocLibIframeEmbed;
      if (DocLibDivider) tools.divider = { class: DocLibDivider, inlineToolbar: true };
      

      if (DocLibFootnote) tools.footnotes = DocLibFootnote;

      if (DocLibPersonality) tools.personality = { class: DocLibPersonality, config: { endpoint: '/api/uploadFile' } };
      if (DocLibQuiz) tools.quiz = DocLibQuiz;
      

      if (DocLibMarker) tools.marker = DocLibMarker;
      if (DocLibInlineCode) tools.inlineCode = DocLibInlineCode;
      if (DocLibUnderline) tools.underline = DocLibUnderline;
      if (DocLibLinkPreview) tools.linkTool = DocLibLinkPreview;
      if (DocLibLinkSearch) tools.linkSearch = DocLibLinkSearch;
      if (DocLibBadge) tools.badge = DocLibBadge;
      if (DocLibKeyboard) tools.keyboard = DocLibKeyboard;
      if (DocLibHyperlink) tools.hyperlink = { class: DocLibHyperlink };
      if (DocLibSpoiler) tools.spoiler = DocLibSpoiler;
      if (DocLibChangeCase) tools.changeCase = DocLibChangeCase;
      if (DocLibTooltip) tools.tooltip = { class: DocLibTooltip };
      if (DocLibStrikethrough) tools.strikethrough = DocLibStrikethrough;
      if (DocLibColorPicker) tools.textColor = { class: DocLibColorPicker, config: { type: 'text' } };
      if (DocLibColorPicker) tools.colorPicker = { class: DocLibColorPicker, config: { type: 'marker' } };
      if (DocLibAnnotation) tools.annotation = DocLibAnnotation;
      if (DocLibComment) tools.comment = DocLibComment;
      if (DocLibTemplate) tools.template = DocLibTemplate;
      if (DocLibSuperscript) tools.superscript = DocLibSuperscript;
      if (DocLibSubscript) tools.subscript = DocLibSubscript;
      if (DocLibTextStyle) tools.textStyle = DocLibTextStyle;
      
      const editor = new EditorJSModule({
        holder: holderDiv,
        tools,
        data,
        placeholder: "Bắt đầu soạn thảo",
        onReady: () => {
          if (DocLibUndo) new DocLibUndo({ editor });
          if (DocLibDragDrop) new DocLibDragDrop(editor);
          if (DocLibMultiBlockSelection) new DocLibMultiBlockSelection(editor);
        },
        onChange: async () => {
          try {
            setSaveStatus("Đang lưu");
            const saved = await editor.save();
            const text = saved.blocks.map(b => b.data?.text || "").join(" ");
            const words = text.trim().split(/\s+/).length;
            setStats(prev => ({ 
                ...prev, 
                charCount: text.length,
                wpm: Math.round((words / ((Date.now() - lastKeystroke) / 60000)) || 0)
            }));
            setLastKeystroke(Date.now());
            setReadingTime(Math.max(1, Math.floor(words / 200)));
            
            const toc = saved.blocks.filter(b => b.type === "header").map(b => ({
               id: b.id || "",
               text: b.data?.text || "",
               level: b.data?.level || 1
            }));
            setTocData(toc);

            const val = JSON.stringify(saved);
            lastContentRef.current = val;
            onSave?.(val);
            
            if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
            saveTimeoutRef.current = setTimeout(async () => {
               if (documentId) {
                  try {
                     const { autoSaveDraftAPI } = await import("@/services/editor.service");
                     await autoSaveDraftAPI(documentId, saved);
                     setSaveStatus("Đã lưu");
                  } catch (e: any) {
                     setSaveStatus("Lỗi lưu");
                  }
               } else {
                  setSaveStatus("Đã lưu");
               }
            }, 2000);
          } catch (err: any) { 
            setSaveStatus("Lỗi lưu");
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
      if (holderDiv && holderDiv.parentNode) holderDiv.remove();
    };
  }, [contentFormat]);

  const [localText, setLocalText] = useState("");
  
  useEffect(() => {
    if (contentFormat === "latex" && initialContent !== undefined && initialContent !== lastContentRef.current) {
       setLocalText(initialContent);
       lastContentRef.current = initialContent;
    }
  }, [initialContent, contentFormat]);

  const handleLatexChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setLocalText(val);
    setSaveStatus("Đang lưu");
    
    const words = val.trim().split(/\s+/).length;
    setStats(prev => ({ 
        ...prev, 
        charCount: val.length,
        wpm: Math.round((words / ((Date.now() - lastKeystroke) / 60000)) || 0)
    }));
    setLastKeystroke(Date.now());
    setReadingTime(Math.max(1, Math.floor(words / 200)));
    
    lastContentRef.current = val;
    onSave?.(val);
    
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
       if (documentId) {
          try {
             const { autoSaveDraftAPI } = await import("@/services/editor.service");
             await autoSaveDraftAPI(documentId, { content: val });
             setSaveStatus("Đã lưu");
          } catch (e: any) {
             setSaveStatus("Lỗi lưu");
          }
       } else {
          setSaveStatus("Đã lưu");
       }
    }, 2000);
  };

  useEffect(() => {
    if (contentFormat === "latex" || !editorRef.current || !initialContent || initialContent === lastContentRef.current) return;
    
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
        } else if (b.type === "monacoLatex") {
          latexCode += (b.data?.code || "") + "\n\n";
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
      showToast(`Quét hoàn tất: ${score}% trùng lặp.`, score > 20 ? "warning" : "success");
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

        <div className={`h-full overflow-y-auto flex justify-center bg-white ${isPreview ? "w-1/2 border-r border-zinc-200" : activeSidebar !== "none" ? "w-2/3" : "w-full"}`}>
          {contentFormat === "latex" ? (
            <textarea
              value={localText}
              onChange={handleLatexChange}
              placeholder="Nhập mã LaTeX tại đây"
              className="w-full h-full p-12 bg-zinc-50 border-none outline-none resize-none font-mono text-sm leading-relaxed text-black"
            />
          ) : (
            <div className="w-full max-w-[900px] px-12 py-20 flex flex-col">
              <div ref={containerRef} className="flex-1 w-full" />
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
