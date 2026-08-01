"use client";

import { useEffect, useRef } from "react";
import MonacoEditor from "@monaco-editor/react";

type LatexEditorProps = {
  initialContent?: string;
  documentId?: string;
  onChange?: (data: string) => void;
  setReadingTime?: (time: number) => void;
  setStats?: (stats: any) => void;
  setLastKeystroke?: (time: number) => void;
};

export default function LatexEditor({
  initialContent = "",
  onChange,
  setReadingTime,
  setStats,
  setLastKeystroke,
}: LatexEditorProps) {
  const editorRef = useRef<any>(null);
  const changeTimer = useRef<number | null>(null);

  useEffect(() => {
    const editor = editorRef.current;
    if (editor && editor.getValue() !== initialContent) {
      editor.setValue(initialContent);
    }
  }, [initialContent]);

  useEffect(
    () => () => {
      if (changeTimer.current) window.clearTimeout(changeTimer.current);
    },
    [],
  );

  const handleChange = (value: string | undefined) => {
    const text = value || "";
    if (changeTimer.current) window.clearTimeout(changeTimer.current);
    changeTimer.current = window.setTimeout(() => {
      setLastKeystroke?.(Date.now());
      onChange?.(text);
      const words = text.trim() ? text.trim().split(/\s+/).length : 0;
      setStats?.({
        words,
        charCount: text.length,
        wpm: Math.round(words / 1.5),
      });
      setReadingTime?.(Math.max(1, Math.ceil(words / 200)));
    }, 500);
  };

  return (
    <div className="h-[calc(100dvh-250px)] min-h-[560px] w-full overflow-hidden border border-border bg-surface">
      <MonacoEditor
        height="100%"
        language="latex"
        theme="light"
        defaultValue={initialContent}
        onMount={(editor) => {
          editorRef.current = editor;
        }}
        onChange={handleChange}
        options={{
          wordWrap: "on",
          minimap: { enabled: false },
          fontSize: 14,
          lineHeight: 23,
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: "smooth",
          overviewRulerBorder: false,
          padding: { top: 20, bottom: 20 },
          scrollbar: {
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
          },
        }}
      />
    </div>
  );
}
