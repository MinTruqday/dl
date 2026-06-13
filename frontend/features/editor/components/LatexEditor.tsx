"use client";

import React, { useEffect } from "react";
import MonacoEditor from "@monaco-editor/react";

interface LatexEditorProps {
  initialContent?: string;
  onChange?: (data: string) => void;
  setReadingTime?: (time: number) => void;
  setStats?: (stats: any) => void;
  setLastKeystroke?: (time: number) => void;
}

export default function LatexEditor({
  initialContent,
  onChange,
  setReadingTime,
  setStats,
  setLastKeystroke,
}: LatexEditorProps) {
  const editorRef = React.useRef<any>(null);
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (editorRef.current && initialContent !== undefined) {
      if (editorRef.current.getValue() !== initialContent) {
        editorRef.current.setValue(initialContent);
      }
    }
  }, [initialContent]);

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
  };

  const handleLatexChange = (value: string | undefined) => {
    const text = value || "";

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      if (setLastKeystroke) setLastKeystroke(Date.now());
      if (onChange) onChange(text);

      if (setStats || setReadingTime) {
        const words = text
          .trim()
          .split(/\s+/)
          .filter((w) => w.length > 0).length;
        if (setStats)
          setStats({
            words,
            charCount: text.length,
            wpm: Math.round(words / 1.5),
          });
        if (setReadingTime) setReadingTime(Math.max(1, Math.ceil(words / 200)));
      }
    }, 1000);
  };

  return (
    <div className="w-full max-w-[900px] px-12 py-6 flex flex-col h-full">
      <MonacoEditor
        height="100%"
        language="latex"
        theme="light"
        defaultValue={initialContent || ""}
        onMount={handleEditorDidMount}
        onChange={handleLatexChange}
        options={{
          wordWrap: "on",
          minimap: { enabled: false },
          fontSize: 14,
          lineHeight: 24,
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: "smooth",
          overviewRulerBorder: false,
          scrollbar: {
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
          },
        }}
        className="border-none focus:outline-none bg-transparent"
      />
    </div>
  );
}
