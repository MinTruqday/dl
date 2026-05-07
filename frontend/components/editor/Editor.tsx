"use client";

import React, { useEffect, useRef, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
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
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPreview, setIsPreview] = useState(false);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
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
            onSave?.(JSON.stringify(saved));
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
    if (!editorRef.current || !initialContent) return;
    editorRef.current.isReady.then(() => {
      let data: OutputData;
      try {
        data = JSON.parse(initialContent);
        if (!data.blocks || data.blocks.length === 0) {
          data = { blocks: [{ type: "paragraph", data: { text: "" } }] };
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

  return (
    <div className="flex flex-col w-full h-full bg-white relative font-sans">
      <div className="flex justify-between items-center border-b border-zinc-200 p-3">
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
              onClick={handleGrammarCheck}
              className="px-4 py-1.5 bg-black text-white flex gap-2 items-center text-xs font-bold active:scale-[0.98]"
            >
              <CheckSquare className="w-4 h-4 text-zinc-400" />
              Kiểm tra ngữ pháp
            </button>
          </div>
        </div>
      </div>
      <div className="flex-1 w-full flex overflow-hidden relative bg-white">
        <div className={`h-full overflow-y-auto ${isPreview ? "w-1/2 border-r border-zinc-200" : "w-full"} p-12`}>
          <div ref={containerRef} />
        </div>
        {isPreview && previewPdfUrl && (
          <div className="w-1/2 h-full border-l border-zinc-200 overflow-hidden bg-white flex flex-col relative animate-in slide-in-from-right-8 fade-in duration-300">
            <div className="px-4 py-3 bg-black text-white text-xs flex justify-between items-center">
              <span className="font-bold">Bản in PDF</span>
              <a href={previewPdfUrl} download="doclib-preview.pdf" className="p-1.5 text-zinc-300 hover:text-white"><Download className="w-4 h-4" /></a>
            </div>
            <div className="flex-1 bg-zinc-100 p-4">
              <iframe src={previewPdfUrl} className="w-full h-full bg-white border border-zinc-200" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
