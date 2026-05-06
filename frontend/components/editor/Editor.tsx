"use client";

import React, { useEffect, useRef, useState } from "react";
import EditorJS, { OutputData } from "@editorjs/editorjs";
import { useToast } from "@/contexts/ToastContext";
import { compilePreviewAPI, grammarCheckAPI, getSynonymsAPI } from "@/services/editor.service";
import { Sparkles, CheckSquare, FileText, Download, Loader2 } from "lucide-react";

export default function Editor({
  initialContent,
  onSave,
}: {
  initialContent?: string;
  onSave?: (data: string) => void;
}) {
  const editorRef = useRef<EditorJS | null>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    if (editorRef.current === null) {
      const Header = require("@editorjs/header");
      const List = require("@editorjs/list");
      const NestedList = require("@editorjs/nested-list");
      const Checklist = require("@editorjs/checklist");
      const NestedChecklist = require("@calumk/editorjs-nested-checklist");
      const Quote = require("@editorjs/quote");
      const CychannQuote = require("@cychann/editorjs-quote");
      const Warning = require("@editorjs/warning");
      const Marker = require("@editorjs/marker");
      const CodeTool = require("@editorjs/code");
      const CodeMirror = require("editorjs-codemirror");
      const CodeCup = require("@calumk/editorjs-codecup");
      const Delimiter = require("@editorjs/delimiter");
      const CoolbytesDelimiter = require("@coolbytes/editorjs-delimiter");
      const InlineCode = require("@editorjs/inline-code");
      const LinkTool = require("@editorjs/link");
      const Embed = require("@editorjs/embed");
      const Table = require("@editorjs/table");
      const EditorjsTable = require("editorjs-table");
      const SimpleImage = require("@editorjs/simple-image");
      const Attaches = require("@editorjs/attaches");
      const RawTool = require("@editorjs/raw");
      const Paragraph = require("@editorjs/paragraph");
      const LineBreakableParagraph = require("@calumk/editorjs-paragraph-linebreakable");
      const Alert = require("editorjs-alert");
      const ColorPicker = require("editorjs-color-picker");
      const TextStyle = require("@skchawala/editorjs-text-style");
      const Underline = require("@editorjs/underline");
      const Tooltip = require("editorjs-tooltip");
      const Strikethrough = require("@sotaproject/strikethrough");
      const Button = require("editorjs-button");
      const Undo = require("editorjs-undo");
      const DragDrop = require("editorjs-drag-drop");
      const ToggleBlock = require("editorjs-toggle-block");
      const TitleEditorjs = require("title-editorjs");
      const InlineImage = require("editorjs-inline-image");
      const Video = require("@weekwood/editorjs-video");
      const Latex = require("editorjs-latex");
      const Mermaid = require("editorjs-mermaid");
      const Gallery = require("editorjs-gallery");
      const TelegramPost = require("editorjs-telegram-post");
      const AudioPlayer = require("editorjs-audio-player");
      const HTMLAudio = require("@furison-tech/editorjs-audio");
      const GroupImage = require("@cychann/editorjs-group-image");
      const ImageCrop = require("editorjs-image-crop-resize");
      const Chart = require("editorjs-chart");
      const ChartJs = require("editorjs-chartjs");
      const AceCode = require("ace-code-editorjs");
      const RxpmCode = require("@rxpm/editor-js-code");
      const Layout = require("editorjs-layout");
      const Columns = require("@calumk/editorjs-columns");
      const Collapsible = require("editorjs-collapsible-block");
      const LinkAutocomplete = require("@editorjs/link-autocomplete");
      const Hyperlink = require("editorjs-hyperlink");
      const InlineSpoiler = require("editorjs-inline-spoiler-tool");
      const InlineTool = require("editorjs-inline-tool");
      const Inline = require("editorjs-inline");
      const InlineTemplate = require("editorjs-inline-template");
      const Style = require("editorjs-style");
      const ChangeCase = require("editorjs-change-case");
      const TextColor = require("editorjs-text-color-plugin");
      const Annotation = require("editorjs-annotation");
      const Comment = require("editorjs-comment");
      const InlineHotkey = require("editorjs-inline-hotkey");
      const TextVariantTune = require("@editorjs/text-variant-tune");
      const AnchorTune = require("editorjs-anchor");
      const NoticeTune = require("editorjs-notice");
      const IndentTune = require("editorjs-indent-tune");
      const CoolbytesAnchor = require("@coolbytes/editorjs-anchor");
      const AlignmentTune = require("editor-js-alignment-tune");

      let data: OutputData | undefined;
      if (initialContent) {
        try {
          data = JSON.parse(initialContent);
        } catch (e) {
          data = {
            time: new Date().getTime(),
            blocks: [
              {
                type: "raw",
                data: {
                  html: initialContent
                }
              }
            ],
            version: "2.29.1"
          };
        }
      }

      const editor = new EditorJS({
        holder: "editorjs",
        tools: {
          textVariant: TextVariantTune,
          anchorTune: AnchorTune,
          noticeTune: NoticeTune,
          indentTune: IndentTune,
          coolbytesAnchor: CoolbytesAnchor,
          alignmentTune: AlignmentTune,
          
          paragraph: {
            class: Paragraph,
            inlineToolbar: true,
            tunes: ["alignmentTune", "textVariant", "indentTune"]
          },
          lineBreakableParagraph: LineBreakableParagraph,
          header: {
            class: Header,
            inlineToolbar: true,
            tunes: ["alignmentTune", "anchorTune"]
          },
          title: TitleEditorjs,
          
          list: {
            class: List,
            inlineToolbar: true,
            tunes: ["alignmentTune"]
          },
          nestedList: NestedList,
          checklist: {
            class: Checklist,
            inlineToolbar: true
          },
          nestedChecklist: NestedChecklist,
          
          quote: {
            class: Quote,
            inlineToolbar: true
          },
          cychannQuote: CychannQuote,
          warning: Warning,
          
          delimiter: Delimiter,
          coolbytesDelimiter: CoolbytesDelimiter,
          
          marker: Marker,
          
          code: CodeTool,
          codeMirror: CodeMirror,
          codeCup: CodeCup,
          aceCode: AceCode,
          rxpmCode: RxpmCode,
          
          inlineCode: InlineCode,
          linkTool: LinkTool,
          linkAutocomplete: LinkAutocomplete,
          hyperlink: Hyperlink,
          
          embed: Embed,
          table: Table,
          editorjsTable: EditorjsTable,
          chart: Chart,
          chartJs: ChartJs,
          
          image: SimpleImage,
          inlineImage: InlineImage,
          gallery: Gallery,
          groupImage: GroupImage,
          imageCrop: ImageCrop,
          video: Video,
          
          attaches: Attaches,
          audioPlayer: AudioPlayer,
          htmlAudio: HTMLAudio,
          mermaid: Mermaid,
          latex: Latex,
          telegramPost: TelegramPost,
          
          raw: RawTool,
          alert: Alert,
          colorPicker: ColorPicker,
          textStyle: TextStyle,
          underline: Underline,
          tooltip: Tooltip,
          strikethrough: Strikethrough,
          button: Button,
          
          toggleBlock: ToggleBlock,
          layout: Layout,
          columns: Columns,
          collapsible: Collapsible,
          
          inlineSpoiler: InlineSpoiler,
          inlineTool: InlineTool,
          inline: Inline,
          inlineTemplate: InlineTemplate,
          style: Style,
          changeCase: ChangeCase,
          textColor: TextColor,
          annotation: Annotation,
          comment: Comment,
          inlineHotkey: InlineHotkey
        },
        data,
        placeholder: "Bắt đầu soạn thảo nội dung",
        onChange: async () => {
          try {
            const content = await editor.save();
            onSave?.(JSON.stringify(content));
          } catch (e) {
            showToast("Lưu nội dung thất bại", "error");
          }
        },
        onReady: () => {
          try {
            new Undo({ editor });
            new DragDrop(editor);
          } catch (e) {
            showToast("Khởi tạo công cụ phụ trợ thất bại", "error");
          }
        }
      });
      editorRef.current = editor;
    }

    return () => {
      if (editorRef.current && editorRef.current.destroy) {
        editorRef.current.destroy();
        editorRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (initialContent && editorRef.current) {
      editorRef.current.isReady.then(() => {
        try {
          const data = JSON.parse(initialContent);
          editorRef.current?.render(data);
        } catch(e) {}
      });
    }
  }, [initialContent]);

  const handleCompile = async () => {
    if (!editorRef.current) return;
    setIsCompiling(true);
    try {
      const data = await editorRef.current.save();
      let latexContent = "";
      data.blocks.forEach((block: any) => {
        if (block.type === "paragraph" || block.type === "header") {
          latexContent += block.data.text + "\n\n";
        }
      });
      
      const blob = await compilePreviewAPI(latexContent, true);
      const url = URL.createObjectURL(blob);
      setPreviewPdfUrl(`${url}#view=FitH&toolbar=0`);
      setIsPreview(true);
    } catch (error) {
      showToast("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau", "error");
    } finally {
      setIsCompiling(false);
    }
  };

  const handleGrammarCheck = async () => {
    if (!editorRef.current) return;
    try {
      const data = await editorRef.current.save();
      let text = "";
      data.blocks.forEach((b: any) => {
        if (b.data && b.data.text) text += b.data.text + " ";
      });
      if (!text || text.length < 50) {
        showToast("Vui lòng viết thêm nội dung tối thiểu 50 từ để kiểm tra ngữ pháp", "info");
        return;
      }
      showToast("Đang phân tích ngữ pháp bằng trí tuệ nhân tạo", "info");
      const res = await grammarCheckAPI(text);
      showToast(`Kết quả: ${res.message} - Điểm: ${res.score}/100`, "success");
    } catch (err: any) {
      showToast(err.message || "Lỗi kết nối máy chủ", "error");
    }
  };

  const handleSynonyms = async () => {
    if (!editorRef.current) return;
    setIsSuggesting(true);
    try {
      const data = await editorRef.current.save();
      let text = "";
      data.blocks.forEach((b: any) => {
        if (b.data && b.data.text) text += b.data.text + " ";
      });
      
      if (!text || text.length < 10) {
        showToast("Vui lòng nhập thêm văn bản để hệ thống gợi ý từ đồng nghĩa", "info");
        setIsSuggesting(false);
        return;
      }

      const words = text.split(" ").filter((w: string) => w.trim().length > 0);
      const targetWord = words[words.length - 1];

      const res = await getSynonymsAPI(targetWord, text);
      if (res.synonyms && res.synonyms.length > 0) {
        showToast(`Gợi ý cho ${targetWord}: ${res.synonyms.join(", ")}`, "info");
      } else {
        showToast("Không tìm thấy từ đồng nghĩa phù hợp", "info");
      }
    } catch (err: any) {
      showToast(err.message || "Không thể lấy gợi ý lúc này", "error");
    } finally {
      setIsSuggesting(false);
    }
  };

  return (
    <div className="flex flex-col w-full h-full mx-auto bg-white relative font-sans">
      <div className="flex justify-between items-center bg-white border-b border-zinc-200 p-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-black uppercase tracking-widest px-2">Khu vực soạn thảo</span>
        </div>
        <div className="flex gap-2 ml-2">
          <button
            onClick={handleSynonyms}
            disabled={isSuggesting}
            className="px-4 py-1.5 border border-zinc-200 text-black hover:bg-zinc-50 flex gap-2 items-center text-xs font-bold transition-colors rounded-none disabled:opacity-50"
          >
            {isSuggesting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Gợi ý từ ngữ
          </button>
          <button
            onClick={handleGrammarCheck}
            className="px-4 py-1.5 bg-black text-white hover:bg-zinc-800 flex gap-2 items-center text-xs font-bold transition-colors rounded-none"
          >
            <CheckSquare className="w-4 h-4 text-zinc-400" />
            Kiểm tra ngữ pháp
          </button>
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            className="px-4 py-1.5 bg-black text-white hover:bg-zinc-800 flex gap-2 items-center text-xs font-bold transition-colors rounded-none disabled:opacity-50"
          >
            {isCompiling ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4 text-zinc-400" />}
            Bản xem trước
          </button>
        </div>
      </div>

      <div className="flex-1 w-full flex overflow-hidden relative bg-white">
        <div className={`h-full overflow-y-auto ease-in-out ${isPreview ? "w-1/2 border-r border-zinc-200" : "w-full"} scrollbar-thin scrollbar-thumb-zinc-100`}>
          <div className="w-full max-w-4xl mx-auto min-h-full animate-in fade-in p-10">
            <div id="editorjs" className="prose prose-sm sm:prose lg:prose-lg xl:prose-xl max-w-none font-sans text-black" />
          </div>
        </div>

        {isPreview && previewPdfUrl && (
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative animate-in slide-in-from-right-8 fade-in duration-300">
            <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center z-10">
              <div className="flex items-center gap-3">
                <div className="p-1.5 bg-zinc-800 rounded-none">
                  <FileText className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold tracking-tight flex flex-col">
                  Bản in PDF
                  <span className="text-[11px] text-zinc-400 font-medium">Đã hoàn thành biên dịch</span>
                </span>
              </div>
              <div className="flex gap-2">
                <a href={previewPdfUrl} download="doclib-preview.pdf" className="p-1.5 transition-colors text-zinc-300 hover:text-white" title="Tải xuống">
                  <Download className="w-4 h-4" />
                </a>
              </div>
            </div>
            <div className="flex-1 bg-zinc-100 overflow-hidden relative p-4 lg:p-8 flex justify-center items-start">
              <iframe src={previewPdfUrl} className="w-full max-w-[850px] aspect-[1/1.414] bg-white border border-zinc-200 transition-transform rounded-none" style={{ minHeight: "100%" }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
