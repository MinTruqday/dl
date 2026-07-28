"use client";

import React, { useEffect, useRef, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import { sanitizeEditorData } from "./editorjs-sanitizer";

interface StandardEditorProps {
  initialContent?: string;
  onSave?: (data: string) => void;
  documentId?: string;
  setReadingTime?: (time: number) => void;
  setStats?: (setter: any) => void;
  setLastKeystroke?: (time: number) => void;
  setTocData?: (data: any) => void;
  setSaveStatus?: (status: string) => void;
  showToast?: (
    msg: string,
    type?: "success" | "error" | "info" | "warning",
  ) => void;
  editorRef?: React.MutableRefObject<EditorJS | null>;
}

class PremiumTune {
  api: any;
  data: any;
  block: any;
  wrapper: HTMLElement | null = null;
  static get isTune() {
    return true;
  }
  constructor({ api, data, config, block }: any) {
    this.api = api;
    this.data = data || { isPremium: false };
    this.block = block;
  }
  render() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("ce-popover-item");
    wrapper.innerHTML = `<div class="ce-popover-item__icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div><div class="ce-popover-item__title">Mark as premium</div>`;
    wrapper.addEventListener("click", () => {
      this.data.isPremium = !this.data.isPremium;
      wrapper.classList.toggle("ce-popover-item--active", this.data.isPremium);
      const idx = this.api.blocks.getCurrentBlockIndex();
      if (idx !== undefined && idx >= 0) {
        const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
        if (blockContent) {
          if (this.data.isPremium) {
            blockContent.style.border = "1px dashed black";
            blockContent.style.opacity = "0.8";
          } else {
            blockContent.style.border = "";
            blockContent.style.opacity = "";
          }
        }
      }
    });
    setTimeout(() => {
      if (this.data.isPremium) {
        wrapper.classList.add("ce-popover-item--active");
        const idx = this.api.blocks.getCurrentBlockIndex();
        if (idx !== undefined && idx >= 0) {
          const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
          if (blockContent) {
            blockContent.style.border = "1px dashed black";
            blockContent.style.opacity = "0.8";
          }
        }
      }
    }, 100);
    this.wrapper = wrapper;
    return wrapper;
  }
  save() {
    return this.data;
  }
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
  editorRef,
}: StandardEditorProps) {
  const defaultEditorRef = useRef<EditorJS | null>(null);
  const actualEditorRef = editorRef || defaultEditorRef;
  const containerRef = useRef<HTMLDivElement>(null);
  const lastContentRef = useRef<string>(initialContent || "");
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "/" &&
        document.activeElement?.classList.contains("ce-paragraph")
      ) {
        const plusButton = document.querySelector(
          ".ce-toolbar__plus",
        ) as HTMLElement;
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
    const pluginInstances: Array<{ destroy?: () => void }> = [];

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
      const DocLibTextHighlight = (await import("./DocLibTextHighlight")).default;
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
      const DocLibImage = (await import("./DocLibImage")).default;
      const DocLibAudio = (await import("./DocLibAudio")).default;
      const DocLibTextStyle = (await import("./DocLibTextStyle")).default;
      const DocLibVideo = (await import("./DocLibVideo")).default;
      const DocLibAnnotation = (await import("./DocLibAnnotation")).default;
      const DocLibChart = (await import("./DocLibChart")).default;
      const DocLibGallery = (await import("./DocLibGallery")).default;
      const DocLibHyperlink = (await import("./DocLibHyperlink")).default;
      const DocLibTitle = (await import("./DocLibTitle")).default;
      const DocLibStyleTune = (await import("./DocLibStyleTune")).default;
      const DocLibNestedChecklist = (await import("./DocLibNestedChecklist"))
        .default;

      const DocLibAudioPlayer = (await import("./DocLibAudioPlayer")).default;

      const DocLibComment = (await import("./DocLibComment")).default;
      const DocLibImageCrop = (await import("./DocLibImageCrop")).default;
      const DocLibTemplate = (await import("./DocLibTemplate")).default;
      const DocLibFootnote = (await import("./DocLibFootnote")).default;
      const DocLibBreakLine = (await import("./DocLibBreakLine")).default;

      const DocLibSuperscript = (await import("./DocLibSuperscript")).default;
      const DocLibSubscript = (await import("./DocLibSubscript")).default;
      const DocLibToggle = (await import("./DocLibToggle")).default;
      const DocLibAiText = (await import("./DocLibAiText")).default;
      const DocLibDrawing = (await import("./DocLibDrawing")).default;
      const DocLibNestedList = (await import("./DocLibNestedList")).default;
      const DocLibTimeline = (await import("./DocLibTimeline")).default;
      const DocLibMath = (await import("./DocLibMath")).default;
      const DocLibKanban = (await import("./DocLibKanban")).default;
      const DocLibCodeMirror = (await import("./DocLibCodeMirror")).default;
      const DocLibUndo = (await import("./DocLibUndo")).default;
      const DocLibDragDrop = (await import("./DocLibDragDrop")).default;
      const DocLibMultiBlockSelection = (await import("./DocLibMultiBlockSelection")).default;
      const DocLibBookmark = (await import("./DocLibBookmark")).default;
      const DocLibIframeEmbed = (await import("./DocLibIframeEmbed")).default;
      const DocLibDivider = (await import("./DocLibDivider")).default;
      const DocLibKeyboard = (await import("./DocLibKeyboard")).default;
      const DocLibCitation = (await import("./DocLibCitation")).default;
      const DocLibDiffViewer = (await import("./DocLibDiffViewer")).default;
      const DocLibGantt = (await import("./DocLibGantt")).default;
      const DocLibColorPalette = (await import("./DocLibColorPalette")).default;
      const DocLibMindMap = (await import("./DocLibMindMap")).default;
      const DocLibSignature = (await import("./DocLibSignature")).default;
      const DocLibKanbanBoard = (await import("./DocLibKanbanBoard")).default;
      const DocLibVerticalTimeline = (await import("./DocLibVerticalTimeline")).default;
      const DocLibPageBreak = (await import("./DocLibPageBreak")).default;
      const DocLibWatermark = (await import("./DocLibWatermark")).default;
      const DocLibTableOfContents = (await import("./DocLibTableOfContents")).default;
      const DocLibMailMerge = (await import("./DocLibMailMerge")).default;
      const DocLibBibliography = (await import("./DocLibBibliography")).default;
      const DocLibDropCap = (await import("./DocLibDropCap")).default;
      const DocLibIndex = (await import("./DocLibIndex")).default;
      const DocLibCoverPage = (await import("./DocLibCoverPage")).default;
      const DocLibTableOfFigures = (await import("./DocLibTableOfFigures")).default;
      const DocLibCrossReference = (await import("./DocLibCrossReference")).default;
      const DocLibTextDirection = (await import("./DocLibTextDirection")).default;
      const DocLibShape = (await import("./DocLibShape")).default;
      const DocLibPageBorder = (await import("./DocLibPageBorder")).default;
      const DocLibLetterhead = (await import("./DocLibLetterhead")).default;
      const DocLibBordersAndShading = (await import("./DocLibBordersAndShading")).default;
      const DocLibPageNumber = (await import("./DocLibPageNumber")).default;
      const DocLibHeaderBlock = (await import("./DocLibHeaderBlock")).default;
      const DocLibFooterBlock = (await import("./DocLibFooterBlock")).default;
      const DocLibPageColor = (await import("./DocLibPageColor")).default;
      const DocLibSectionBreak = (await import("./DocLibSectionBreak")).default;
      const DocLibLineNumbers = (await import("./DocLibLineNumbers")).default;
      const DocLibTextBox = (await import("./DocLibTextBox")).default;
      const DocLibWordArt = (await import("./DocLibWordArt")).default;
      const DocLibSmartArtCycle = (await import("./DocLibSmartArtCycle")).default;
      const DocLibSmartArtHierarchy = (await import("./DocLibSmartArtHierarchy")).default;
      const DocLibWatermarkImage = (await import("./DocLibWatermarkImage")).default;
      const DocLibDateAndTime = (await import("./DocLibDateAndTime")).default;
      const DocLibFormCheckBox = (await import("./DocLibFormCheckBox")).default;
      const DocLibFormDropdown = (await import("./DocLibFormDropdown")).default;
      const DocLibMacroButton = (await import("./DocLibMacroButton")).default;
      const DocLibDirectoryTree = (await import("./DocLibDirectoryTree")).default;
      const DocLibJsonViewer = (await import("./DocLibJsonViewer")).default;
      const DocLibMarkdownBlock = (await import("./DocLibMarkdownBlock")).default;
      const DocLibFormRadioButton = (await import("./DocLibFormRadioButton")).default;
      const DocLibFormComboBox = (await import("./DocLibFormComboBox")).default;
      const DocLibFormListBox = (await import("./DocLibFormListBox")).default;
      const DocLibFormToggleButton = (await import("./DocLibFormToggleButton")).default;
      const DocLibFormSpinButton = (await import("./DocLibFormSpinButton")).default;
      const DocLibDatePicker = (await import("./DocLibDatePicker")).default;
      const DocLibAddressBlock = (await import("./DocLibAddressBlock")).default;
      const DocLibGreetingLine = (await import("./DocLibGreetingLine")).default;
      const DocLibEnvelope = (await import("./DocLibEnvelope")).default;
      const DocLibLabelConfig = (await import("./DocLibLabelConfig")).default;
      const DocLibEvenPageBreak = (await import("./DocLibEvenPageBreak")).default;
      const DocLibOddPageBreak = (await import("./DocLibOddPageBreak")).default;
      const DocLibPrintPreview = (await import("./DocLibPrintPreview")).default;
      const DocLibHyphenation = (await import("./DocLibHyphenation")).default;
      const DocLibSmartArtProcess = (await import("./DocLibSmartArtProcess")).default;
      const DocLibSmartArtList = (await import("./DocLibSmartArtList")).default;
      const DocLibSmartArtMatrix = (await import("./DocLibSmartArtMatrix")).default;
      const DocLibSmartArtPyramid = (await import("./DocLibSmartArtPyramid")).default;
      const DocLibSmartArtRelationship = (await import("./DocLibSmartArtRelationship")).default;
      const DocLibDocumentProperty = (await import("./DocLibDocumentProperty")).default;
      const DocLibDocumentStats = (await import("./DocLibDocumentStats")).default;
      const DocLibTrackChanges = (await import("./DocLibTrackChanges")).default;
      const DocLibCombineDocuments = (await import("./DocLibCombineDocuments")).default;
      const DocLibProtectDocument = (await import("./DocLibProtectDocument")).default;
      const DocLibDigitalSignature = (await import("./DocLibDigitalSignature")).default;
      const DocLibCompatibilityChecker = (await import("./DocLibCompatibilityChecker")).default;
      const DocLibVersionHistory = (await import("./DocLibVersionHistory")).default;
      const DocLibTableOfAuthorities = (await import("./DocLibTableOfAuthorities")).default;
      const DocLibCaption = (await import("./DocLibCaption")).default;
      const DocLibQuickParts = (await import("./DocLibQuickParts")).default;
      const DocLibMasterDocument = (await import("./DocLibMasterDocument")).default;
      const DocLibSubdocument = (await import("./DocLibSubdocument")).default;
      const DocLibOutlineLevel = (await import("./DocLibOutlineLevel")).default;
      const DocLibTranslation = (await import("./DocLibTranslation")).default;
      const DocLibThesaurus = (await import("./DocLibThesaurus")).default;
      const DocLibEquationArray = (await import("./DocLibEquationArray")).default;

      if (cancelled) {
        holderDiv.remove();
        return;
      }

      let data: OutputData = {
        blocks: [{ type: "paragraph", data: { text: "" } }],
      };
      if (initialContent) {
        try {
          const parsed = JSON.parse(initialContent);
          if (parsed.blocks && parsed.blocks.length > 0)
            data = sanitizeEditorData(parsed);
        } catch (err: any) {
          const blocks = initialContent.split("\n").map((line: string) => ({
            type: "paragraph",
            data: { text: line },
          }));
          data = {
            blocks:
              blocks.length > 0
                ? blocks
                : [{ type: "paragraph", data: { text: "" } }],
          };
        }
      }

      const tools: Record<string, any> = {};

      tools.premium = { class: PremiumTune };
      const commonTunes = ["textVariant", "styleTune"];
      if (DocLibAlignmentTune) {
        tools.alignment = { class: DocLibAlignmentTune };
        commonTunes.push("alignment");
      }
      tools.indent = { class: DocLibIndentTune };
      commonTunes.push("indent");
      if (DocLibStyleTune) {
        tools.style = DocLibStyleTune;
        commonTunes.push("style");
      }
      if (DocLibAnchor) {
        tools.anchor = { class: DocLibAnchor, config: { theme: "light" } };
        commonTunes.push("anchor");
      }
      const paragraphTunes = [...commonTunes];
      if (DocLibStyleTune) tools.styleTune = DocLibStyleTune;
      if (DocLibTextVariant) tools.textVariant = DocLibTextVariant;
      const indentTunes = ["indent"];
      const alignTunes = DocLibAlignmentTune ? ["alignment"] : [];

      if (DocLibTitle) tools.title = DocLibTitle;
      if (DocLibHeader) {
        tools.header = {
          class: DocLibHeader,
          inlineToolbar: true,
          config: {
            placeholder: "Enter a title",
            levels: [1, 2, 3, 4, 5, 6],
            defaultLevel: 2,
          },
          tunes: commonTunes,
        };
      }

      if (DocLibParagraph)
        tools.paragraph = {
          class: DocLibParagraph,
          inlineToolbar: true,
          tunes: paragraphTunes,
        };
      if (DocLibQuote)
        tools.originalQuote = { class: DocLibQuote, inlineToolbar: true };
      if (DocLibWarning) tools.warning = DocLibWarning;
      if (DocLibAlert)
        tools.alert = { class: DocLibAlert, inlineToolbar: true };
      if (DocLibDelimiter) tools.originalDelimiter = DocLibDelimiter;
      if (DocLibAiText) tools.aiText = DocLibAiText;

      if (DocLibTable)
        tools.table = { class: DocLibTable, inlineToolbar: true };
      if (DocLibToggle)
        tools.toggle = { class: DocLibToggle, inlineToolbar: true };
      if (DocLibBreakLine)
        tools.breakLine = { class: DocLibBreakLine, inlineToolbar: true };

      if (DocLibList)
        tools.list = {
          class: DocLibList,
          inlineToolbar: true,
          tunes: indentTunes,
        };
      if (DocLibChecklist)
        tools.checklist = {
          class: DocLibChecklist,
          inlineToolbar: true,
          tunes: indentTunes,
        };
      if (DocLibNestedChecklist)
        tools.nestedChecklist = {
          class: DocLibNestedChecklist,
          inlineToolbar: true,
          tunes: indentTunes,
        };

      if (DocLibImage)
        tools.image = {
          class: DocLibImage,
          config: {
            endpoints: { byFile: "/api/uploadFile", byUrl: "/api/fetchUrl" },
          },
        };

      if (DocLibImageCrop) tools.imageCrop = DocLibImageCrop;
      if (DocLibGallery) tools.gallery = DocLibGallery;
      if (DocLibFile) tools.attaches = { class: DocLibFile };
      if (DocLibEmbed) tools.embed = DocLibEmbed;
      if (DocLibMermaid) tools.mermaid = DocLibMermaid;
      if (DocLibDrawing) tools.drawing = DocLibDrawing;
      if (DocLibLatex) {
        tools.latex = DocLibLatex;
      }
      if (DocLibAudio) tools.audio = DocLibAudio;
      if (DocLibAudioPlayer) tools.audioPlayer = DocLibAudioPlayer;
      if (DocLibVideo) tools.video = DocLibVideo;

      if (DocLibCode) tools.code = DocLibCode;
      if (DocLibRaw) tools.raw = DocLibRaw;
      if (DocLibCodeBox) tools.codeBox = DocLibCodeBox;
      if (DocLibCodeMirror) tools.codeMirror = DocLibCodeMirror;

      if (DocLibChart) tools.chart = DocLibChart;

      if (DocLibButton) tools.button = DocLibButton;

      if (DocLibColumns) tools.columns = DocLibColumns;

      if (DocLibNestedList)
        tools.nestedList = { class: DocLibNestedList, inlineToolbar: true };
      if (DocLibTimeline) tools.timeline = DocLibTimeline;
      if (DocLibMath) tools.math = DocLibMath;
      if (DocLibKanban) tools.kanban = DocLibKanban;

      if (DocLibBookmark) tools.bookmark = DocLibBookmark;
      if (DocLibIframeEmbed) tools.iframe = DocLibIframeEmbed;
      if (DocLibDivider)
        tools.divider = { class: DocLibDivider, inlineToolbar: true };

      if (DocLibFootnote) tools.footnotes = DocLibFootnote;
      if (DocLibMarker) tools.marker = DocLibMarker;
      if (DocLibTextHighlight) tools.textHighlight = DocLibTextHighlight;
      if (DocLibInlineCode) tools.inlineCode = DocLibInlineCode;
      if (DocLibUnderline) tools.underline = DocLibUnderline;
      if (DocLibLinkPreview) tools.linkTool = DocLibLinkPreview;
      if (DocLibKeyboard) tools.keyboard = DocLibKeyboard;
      if (DocLibHyperlink) tools.hyperlink = { class: DocLibHyperlink };
      if (DocLibSpoiler) tools.spoiler = DocLibSpoiler;
      if (DocLibChangeCase) tools.changeCase = DocLibChangeCase;
      if (DocLibTooltip) tools.tooltip = { class: DocLibTooltip };
      if (DocLibStrikethrough) tools.strikethrough = DocLibStrikethrough;
      if (DocLibColorPicker)
        tools.textColor = {
          class: DocLibColorPicker,
          config: { type: "text" },
        };
      if (DocLibColorPicker)
        tools.colorPicker = {
          class: DocLibColorPicker,
          config: { type: "marker" },
        };
      if (DocLibAnnotation) tools.annotation = DocLibAnnotation;
      if (DocLibComment) tools.comment = DocLibComment;
      if (DocLibTemplate) tools.template = DocLibTemplate;
      if (DocLibSuperscript) tools.superscript = DocLibSuperscript;
      if (DocLibSubscript) tools.subscript = DocLibSubscript;
      if (DocLibTextStyle) tools.textStyle = DocLibTextStyle;
      if (DocLibCitation) tools.citation = DocLibCitation;
      if (DocLibDiffViewer) tools.diffViewer = DocLibDiffViewer;
      if (DocLibGantt) tools.gantt = DocLibGantt;
      if (DocLibColorPalette) tools.colorPalette = DocLibColorPalette;
      if (DocLibMindMap) tools.mindMap = DocLibMindMap;
      if (DocLibSignature) tools.signature = DocLibSignature;
      if (DocLibKanbanBoard) tools.kanbanBoard = DocLibKanbanBoard;
      if (DocLibVerticalTimeline)
        tools.verticalTimeline = DocLibVerticalTimeline;
      if (DocLibPageBreak) tools.pageBreak = DocLibPageBreak;
      if (DocLibWatermark) tools.watermark = DocLibWatermark;
      if (DocLibTableOfContents) tools.tableOfContents = DocLibTableOfContents;
      if (DocLibMailMerge) tools.mailMerge = DocLibMailMerge;
      if (DocLibBibliography) tools.bibliography = DocLibBibliography;
      if (DocLibDropCap) tools.dropCap = DocLibDropCap;
      if (DocLibIndex) tools.index = DocLibIndex;
      if (DocLibCoverPage) tools.coverPage = DocLibCoverPage;
      if (DocLibTableOfFigures) tools.tableOfFigures = DocLibTableOfFigures;
      if (DocLibCrossReference) tools.crossReference = DocLibCrossReference;
      if (DocLibTextDirection) tools.textDirection = DocLibTextDirection;
      if (DocLibShape) tools.shape = DocLibShape;
      if (DocLibPageBorder) tools.pageBorder = DocLibPageBorder;
      if (DocLibLetterhead) tools.letterhead = DocLibLetterhead;
      if (DocLibBordersAndShading) tools.bordersAndShading = DocLibBordersAndShading;
      if (DocLibPageNumber) tools.pageNumber = DocLibPageNumber;
      if (DocLibHeaderBlock) tools.headerBlock = DocLibHeaderBlock;
      if (DocLibFooterBlock) tools.footerBlock = DocLibFooterBlock;
      if (DocLibPageColor) tools.pageColor = DocLibPageColor;
      if (DocLibSectionBreak) tools.sectionBreak = DocLibSectionBreak;
      if (DocLibLineNumbers) tools.lineNumbers = DocLibLineNumbers;
      if (DocLibTextBox) tools.textBox = DocLibTextBox;
      if (DocLibWordArt) tools.wordArt = DocLibWordArt;
      if (DocLibSmartArtCycle) tools.smartArtCycle = DocLibSmartArtCycle;
      if (DocLibSmartArtHierarchy) tools.smartArtHierarchy = DocLibSmartArtHierarchy;
      if (DocLibWatermarkImage) tools.watermarkImage = DocLibWatermarkImage;
      if (DocLibDateAndTime) tools.dateAndTime = DocLibDateAndTime;
      if (DocLibFormCheckBox) tools.formCheckBox = DocLibFormCheckBox;
      if (DocLibFormDropdown) tools.formDropdown = DocLibFormDropdown;
      if (DocLibMacroButton) tools.macroButton = DocLibMacroButton;
      if (DocLibSimpleImage) tools.simpleImage = DocLibSimpleImage;

      if (DocLibDirectoryTree) tools.directoryTree = DocLibDirectoryTree;
      if (DocLibJsonViewer) tools.jsonViewer = DocLibJsonViewer;
      if (DocLibMarkdownBlock) tools.markdownBlock = DocLibMarkdownBlock;

      if (DocLibFormRadioButton) tools.formRadioButton = DocLibFormRadioButton;
      if (DocLibFormComboBox) tools.formComboBox = DocLibFormComboBox;
      if (DocLibFormListBox) tools.formListBox = DocLibFormListBox;
      if (DocLibFormToggleButton)
        tools.formToggleButton = DocLibFormToggleButton;
      if (DocLibFormSpinButton) tools.formSpinButton = DocLibFormSpinButton;
      if (DocLibDatePicker) tools.datePicker = DocLibDatePicker;
      if (DocLibAddressBlock) tools.addressBlock = DocLibAddressBlock;
      if (DocLibGreetingLine) tools.greetingLine = DocLibGreetingLine;
      if (DocLibEnvelope) tools.envelope = DocLibEnvelope;
      if (DocLibLabelConfig) tools.labelConfig = DocLibLabelConfig;
      if (DocLibEvenPageBreak) tools.evenPageBreak = DocLibEvenPageBreak;
      if (DocLibOddPageBreak) tools.oddPageBreak = DocLibOddPageBreak;
      if (DocLibPrintPreview) tools.printPreview = DocLibPrintPreview;
      if (DocLibHyphenation) tools.hyphenation = DocLibHyphenation;
      if (DocLibSmartArtProcess) tools.smartArtProcess = DocLibSmartArtProcess;
      if (DocLibSmartArtList) tools.smartArtList = DocLibSmartArtList;
      if (DocLibSmartArtMatrix) tools.smartArtMatrix = DocLibSmartArtMatrix;
      if (DocLibSmartArtPyramid) tools.smartArtPyramid = DocLibSmartArtPyramid;
      if (DocLibSmartArtRelationship)
        tools.smartArtRelationship = DocLibSmartArtRelationship;
      if (DocLibDocumentProperty)
        tools.documentProperty = DocLibDocumentProperty;
      if (DocLibDocumentStats) tools.documentStats = DocLibDocumentStats;
      if (DocLibTrackChanges) tools.trackChanges = DocLibTrackChanges;
      if (DocLibCombineDocuments)
        tools.combineDocuments = DocLibCombineDocuments;
      if (DocLibProtectDocument) tools.protectDocument = DocLibProtectDocument;
      if (DocLibDigitalSignature)
        tools.digitalSignature = DocLibDigitalSignature;
      if (DocLibCompatibilityChecker)
        tools.compatibilityChecker = DocLibCompatibilityChecker;
      if (DocLibVersionHistory) tools.versionHistory = DocLibVersionHistory;
      if (DocLibTableOfAuthorities)
        tools.tableOfAuthorities = DocLibTableOfAuthorities;
      if (DocLibCaption) tools.caption = DocLibCaption;
      if (DocLibQuickParts) tools.quickParts = DocLibQuickParts;
      if (DocLibMasterDocument) tools.masterDocument = DocLibMasterDocument;
      if (DocLibSubdocument) tools.subdocument = DocLibSubdocument;
      if (DocLibOutlineLevel) tools.outlineLevel = DocLibOutlineLevel;
      if (DocLibTranslation) tools.translation = DocLibTranslation;
      if (DocLibThesaurus) tools.thesaurus = DocLibThesaurus;
      if (DocLibEquationArray) tools.equationArray = DocLibEquationArray;

      const editor = new EditorJSModule({
        holder: holderDiv,
        tools,
        data,
        placeholder: "Start writing",
        onReady: () => {
          if (cancelled) return;
          if (DocLibUndo)
            pluginInstances.push(new DocLibUndo({ editor }));
          if (DocLibDragDrop)
            pluginInstances.push(new DocLibDragDrop(editor));
          if (DocLibMultiBlockSelection)
            pluginInstances.push(new DocLibMultiBlockSelection(editor));
        },
        onChange: async () => {
          try {
            if (setSaveStatus) setSaveStatus("Saving");
            const saved = sanitizeEditorData(await editor.save());
            const text = saved.blocks.map((b) => b.data?.text || "").join(" ");
            const words = text.trim().split(/\s+/).length;

            let lastKeystroke = Date.now();
            if (setStats) {
              setStats((prev: any) => ({
                ...prev,
                charCount: text.length,
                wpm: Math.round(
                  words /
                    ((Date.now() -
                      (prev?.lastKeystroke || lastKeystroke - 1000)) /
                      60000) || 0,
                ),
              }));
            }
            if (setLastKeystroke) setLastKeystroke(lastKeystroke);
            if (setReadingTime)
              setReadingTime(Math.max(1, Math.floor(words / 200)));

            if (setTocData) {
              const toc = saved.blocks
                .filter((b) => b.type === "header")
                .map((b) => ({
                  id: b.id || "",
                  text: b.data?.text || "",
                  level: b.data?.level || 1,
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
                  const { autoSaveDraftAPI } =
                    await import("@/features/compilation/services/editorjs.service");
                  await autoSaveDraftAPI(documentId, saved);
                  if (setSaveStatus) setSaveStatus("Saved");
                } catch (e: any) {
                  if (setSaveStatus) setSaveStatus("Save failed");
                }
              } else {
                if (setSaveStatus) setSaveStatus("Saved");
              }
            }, 2000);
          } catch (err: any) {
            if (setSaveStatus) setSaveStatus("Save failed");
            if (showToast)
              showToast(
                "Autosave failed: " + (err.message || ""),
                "error",
              );
          }
        },
      });

      if (!cancelled) {
        actualEditorRef.current = editor;
      } else {
        editor.isReady
          .then(() => editor.destroy())
          .catch((err) => {
            console.error("Error destroying EditorJS instance:", err);
          });
        holderDiv.remove();
      }
    };

    init();

    return () => {
      cancelled = true;
      pluginInstances.forEach((plugin) => plugin.destroy?.());
      if (actualEditorRef.current && actualEditorRef.current.destroy) {
        actualEditorRef.current.destroy();
        actualEditorRef.current = null;
      }
      if (holderDiv && holderDiv.parentNode) holderDiv.remove();
    };
  }, []);

  return <div ref={containerRef} className="w-full flex-1 min-h-[500px]" />;
}
