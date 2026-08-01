"use client";

import { useEffect, useRef } from "react";
import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";
import { sanitizeEditorData } from "./editorjs-sanitizer";

type StandardEditorProps = {
  initialContent?: string;
  onSave?: (data: string) => void;
  documentId?: string;
  setReadingTime?: (time: number) => void;
  setStats?: (stats: any) => void;
  setLastKeystroke?: (time: number) => void;
  setTocData?: (data: any[]) => void;
  setSaveStatus?: (status: string) => void;
  showToast?: (
    message: string,
    type?: "success" | "error" | "info" | "warning",
  ) => void;
  editorRef?: React.MutableRefObject<EditorJS | null>;
};

function initialData(content: string): OutputData {
  if (!content.trim()) {
    return { blocks: [{ type: "paragraph", data: { text: "" } }] };
  }
  try {
    const parsed = JSON.parse(content);
    if (Array.isArray(parsed.blocks)) return sanitizeEditorData(parsed);
  } catch {}
  return {
    blocks: content.split("\n").map((text) => ({
      type: "paragraph",
      data: { text },
    })),
  };
}

export default function StandardEditor({
  initialContent = "",
  onSave,
  setReadingTime,
  setStats,
  setLastKeystroke,
  setTocData,
  setSaveStatus,
  showToast,
  editorRef,
}: StandardEditorProps) {
  const localEditorRef = useRef<EditorJS | null>(null);
  const activeEditorRef = editorRef || localEditorRef;
  const containerRef = useRef<HTMLDivElement>(null);
  const changeTimer = useRef<number | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;
    const holder = document.createElement("div");
    holder.className = "doclib-editor prose prose-zinc min-h-full max-w-none";
    containerRef.current.replaceChildren(holder);

    const initialize = async () => {
      const EditorJSModule = (await import("@editorjs/editorjs")).default;
      const [
        paragraph,
        header,
        list,
        checklist,
        table,
        quote,
        code,
        raw,
        delimiter,
        image,
        file,
        alert,
        toggle,
        math,
        mermaid,
        embed,
        marker,
        inlineCode,
        underline,
        strikethrough,
        highlight,
        alignment,
        indent,
      ] = await Promise.all([
        import("./DocLibParagraph").then((module) => module.default),
        import("./DocLibHeader").then((module) => module.default),
        import("./DocLibList").then((module) => module.default),
        import("./DocLibChecklist").then((module) => module.default),
        import("./DocLibTable").then((module) => module.default),
        import("./DocLibQuote").then((module) => module.default),
        import("./DocLibCode").then((module) => module.default),
        import("./DocLibRaw").then((module) => module.default),
        import("./DocLibDelimiter").then((module) => module.default),
        import("./DocLibImage").then((module) => module.default),
        import("./DocLibFile").then((module) => module.default),
        import("./DocLibAlert").then((module) => module.default),
        import("./DocLibToggle").then((module) => module.default),
        import("./DocLibMath").then((module) => module.default),
        import("./DocLibMermaid").then((module) => module.default),
        import("./DocLibEmbed").then((module) => module.default),
        import("./DocLibMarker").then((module) => module.default),
        import("./DocLibInlineCode").then((module) => module.default),
        import("./DocLibUnderline").then((module) => module.default),
        import("./DocLibStrikethrough").then((module) => module.default),
        import("./DocLibTextHighlight").then((module) => module.default),
        import("./DocLibAlignment").then((module) => module.default),
        import("./DocLibIndent").then((module) => module.default),
      ]);

      if (cancelled) return;
      const commonTunes = ["alignment", "indent"];
      const editor = new EditorJSModule({
        holder,
        data: initialData(initialContent),
        placeholder: "Bắt đầu viết",
        tools: {
          paragraph: {
            class: paragraph,
            inlineToolbar: true,
            tunes: commonTunes,
          },
          header: {
            class: header,
            inlineToolbar: true,
            config: {
              placeholder: "Tiêu đề",
              levels: [1, 2, 3, 4],
              defaultLevel: 2,
            },
            tunes: commonTunes,
          },
          list: { class: list, inlineToolbar: true, tunes: ["indent"] },
          checklist: {
            class: checklist,
            inlineToolbar: true,
            tunes: ["indent"],
          },
          table: { class: table, inlineToolbar: true },
          originalQuote: { class: quote as any, inlineToolbar: true },
          code,
          raw,
          originalDelimiter: delimiter,
          image,
          attaches: file,
          alert: { class: alert, inlineToolbar: true },
          toggle: { class: toggle, inlineToolbar: true },
          math,
          mermaid,
          embed,
          marker,
          inlineCode,
          underline,
          strikethrough,
          textHighlight: highlight,
          alignment: { class: alignment },
          indent: { class: indent },
        },
        onChange: () => {
          if (changeTimer.current) window.clearTimeout(changeTimer.current);
          setSaveStatus?.("Đang lưu");
          changeTimer.current = window.setTimeout(async () => {
            try {
              const data = sanitizeEditorData(await editor.save());
              const text = data.blocks
                .map((block) => block.data?.text || block.data?.code || "")
                .join(" ");
              const words = text.trim() ? text.trim().split(/\s+/).length : 0;
              setStats?.({ words, charCount: text.length });
              setReadingTime?.(Math.max(1, Math.ceil(words / 200)));
              setLastKeystroke?.(Date.now());
              setTocData?.(
                data.blocks
                  .filter((block) => block.type === "header")
                  .map((block) => ({
                    id: block.id || "",
                    text: block.data?.text || "",
                    level: block.data?.level || 2,
                  })),
              );
              onSave?.(JSON.stringify(data));
              setSaveStatus?.("Đã lưu");
            } catch (reason) {
              setSaveStatus?.("Chưa lưu");
              showToast?.(
                reason instanceof Error
                  ? reason.message
                  : "Không thể lưu bản thảo",
                "error",
              );
            }
          }, 300);
        },
      });
      activeEditorRef.current = editor;
    };

    void initialize();
    return () => {
      cancelled = true;
      if (changeTimer.current) window.clearTimeout(changeTimer.current);
      const editor = activeEditorRef.current;
      activeEditorRef.current = null;
      if (editor) void editor.isReady.then(() => editor.destroy()).catch(() => undefined);
      holder.remove();
    };
  }, []);

  return <div ref={containerRef} className="min-h-[560px] w-full" />;
}
