"use client";

import React, { useEffect } from "react";
import MonacoEditor from "@monaco-editor/react";

interface LatexEditorProps {
  initialContent?: string;
  documentId?: string;
  onChange?: (data: string) => void;
  setReadingTime?: (time: number) => void;
  setStats?: (stats: any) => void;
  setLastKeystroke?: (time: number) => void;
}

import {
  cloudAutoSaveAPI,
  cleanTempFilesAPI,
  getLatexDraftAPI,
} from "@/features/compilation/services/latex.service";
import { useToast } from "@/shared/contexts/ToastContext";

export default function LatexEditor({
  initialContent,
  documentId,
  onChange,
  setReadingTime,
  setStats,
  setLastKeystroke,
}: LatexEditorProps) {
  const { showToast } = useToast();
  const editorRef = React.useRef<any>(null);
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const autoSaveTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const initContent = async () => {
      try {
        const draftRes = await getLatexDraftAPI();
        const draftContent = draftRes?.data?.content;
        const targetContent = draftContent || initialContent || "";
        if (
          editorRef.current &&
          editorRef.current.getValue() !== targetContent
        ) {
          editorRef.current.setValue(targetContent);
        }
      } catch (err) {
        if (editorRef.current && initialContent !== undefined) {
          if (editorRef.current.getValue() !== initialContent) {
            editorRef.current.setValue(initialContent);
          }
        }
      }
    };
    if (editorRef.current) {
      initContent();
    }
  }, [initialContent]);

  useEffect(() => {
    return () => {
      // Clean temp files on unmount
      cleanTempFilesAPI().catch(() => {});
    };
  }, []);

  const handleEditorDidMount = async (editor: any, monaco: any) => {
    editorRef.current = editor;
    try {
      const draftRes = await getLatexDraftAPI();
      const draftContent = draftRes?.data?.content;
      const targetContent = draftContent || initialContent || "";
      if (editor.getValue() !== targetContent) {
        editor.setValue(targetContent);
      }
    } catch (err) {
      // fallback to initialContent
    }
  };

  const handleLatexChange = (value: string | undefined) => {
    const text = value || "";

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
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

    if (documentId) {
      autoSaveTimeoutRef.current = setTimeout(() => {
        cloudAutoSaveAPI(documentId, text)
          .then(() => showToast("Đã lưu nháp LaTeX lên đám mây", "success"))
          .catch(() => {});
      }, 5000); // 5 seconds auto save
    }
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
