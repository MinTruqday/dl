"use client";

import React, { useEffect, useRef, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";

interface StandardEditorProps {
  initialContent?: string;
  onSave?: (data: string) => void;
  documentId?: string;
  setReadingTime?: (time: number) => void;
  setStats?: (setter: any) => void;
  setLastKeystroke?: (time: number) => void;
  setTocData?: (data: any) => void;
  setSaveStatus?: (status: string) => void;
  showToast?: (msg: string, type?: "success" | "error" | "info" | "warning") => void;
  editorRef?: React.MutableRefObject<EditorJS | null>;
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

export default function StandardEditor({ 
  initialContent, 
  onSave, 
  documentId,
  setReadingTime,
  setStats,
  setLastKeystroke,
  setTocData,
  setSaveStatus,
  showToast,
  editorRef
}: StandardEditorProps) {
  const defaultEditorRef = useRef<EditorJS | null>(null);
  const actualEditorRef = editorRef || defaultEditorRef;
  const containerRef = useRef<HTMLDivElement>(null);
  const lastContentRef = useRef<string>(initialContent || "");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
          const blocks = initialContent.split("\n").map((line: string) => ({
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
            if (setSaveStatus) setSaveStatus("Đang lưu");
            const saved = await editor.save();
            const text = saved.blocks.map(b => b.data?.text || "").join(" ");
            const words = text.trim().split(/\s+/).length;
            
            let lastKeystroke = Date.now();
            if (setStats) {
                setStats((prev: any) => ({ 
                    ...prev, 
                    charCount: text.length,
                    wpm: Math.round((words / ((Date.now() - (prev?.lastKeystroke || lastKeystroke - 1000)) / 60000)) || 0)
                }));
            }
            if (setLastKeystroke) setLastKeystroke(lastKeystroke);
            if (setReadingTime) setReadingTime(Math.max(1, Math.floor(words / 200)));
            
            if (setTocData) {
                const toc = saved.blocks.filter(b => b.type === "header").map(b => ({
                   id: b.id || "",
                   text: b.data?.text || "",
                   level: b.data?.level || 1
                }));
                setTocData(toc);
            }

            const val = JSON.stringify(saved);
            lastContentRef.current = val;
            if (onSave) onSave(val);
            
            if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
            saveTimeoutRef.current = setTimeout(async () => {
               if (documentId) {
                  try {
                     const { autoSaveDraftAPI } = await import("@/features/editor/services/editor.service");
                     await autoSaveDraftAPI(documentId, saved);
                     if (setSaveStatus) setSaveStatus("Đã lưu");
                  } catch (e: any) {
                     if (setSaveStatus) setSaveStatus("Lỗi lưu");
                  }
               } else {
                  if (setSaveStatus) setSaveStatus("Đã lưu");
               }
            }, 2000);
          } catch (err: any) { 
            if (setSaveStatus) setSaveStatus("Lỗi lưu");
            if (showToast) showToast("Lỗi khi tự động lưu nội dung: " + (err.message || ""), "error"); 
          }
        },
      });

      if (!cancelled) {
        actualEditorRef.current = editor;
      } else {
        editor.isReady.then(() => editor.destroy()).catch((err) => { console.error(err); });
        holderDiv.remove();
      }
    };

    init();

    return () => {
      cancelled = true;
      if (actualEditorRef.current && actualEditorRef.current.destroy) {
        actualEditorRef.current.destroy();
        actualEditorRef.current = null;
      }
      if (holderDiv && holderDiv.parentNode) holderDiv.remove();
    };
  }, []);

  return <div ref={containerRef} className="w-full flex-1 min-h-[500px]" />;
}
