"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import ReaderTools from "./ReaderTools";
import {
  getBookHighlightsAPI,
  createHighlightAPI,
  deleteHighlightAPI,
  updateHighlightNoteAPI,
  exportHighlightsMarkdownAPI,
} from "@/app/lib/api";
import { Highlighter, X, Trash2, PenTool, Download } from "lucide-react";

const HIGHLIGHT_COLORS = [
  { value: "#e4e4e7", label: "Nhạt", className: "bg-zinc-200" },
  { value: "#71717a", label: "Vừa", className: "bg-zinc-500" },
  { value: "#18181b", label: "Đậm", className: "bg-zinc-900" },
];

interface Highlight {
  id: string;
  text: string;
  color: string;
  start_offset: number;
  end_offset: number;
  note: string;
  chapter_slug: string;
  created_at: string;
}

interface ReaderViewProps {
  content: string;
  title: string;
  bookId?: string;
}

export default function ReaderView({ content, title, bookId }: ReaderViewProps) {
  const [fontSize, setFontSize] = useState(18);
  const [theme, setTheme] = useState<"light" | "sepia" | "night">("light");
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [selectionPopup, setSelectionPopup] = useState<{ x: number; y: number; text: string } | null>(null);
  const [editingNote, setEditingNote] = useState<{ id: string; note: string } | null>(null);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(false);
  const [autoScrollSpeed, setAutoScrollSpeed] = useState(2);
  const [searchQuery, setSearchQuery] = useState("");
  const [toastMsg, setToastMsg] = useState<{ text: string; type: "error" | "success" } | null>(null);
  const articleRef = useRef<HTMLElement>(null);
  const scrollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const themeClasses = {
    light: "bg-white text-zinc-900",
    sepia: "bg-[#f4ecd8] text-[#5b4636]",
    night: "bg-[#1a1a1a] text-zinc-300",
  };

  useEffect(() => {
    if (autoScrollEnabled) {
      scrollIntervalRef.current = setInterval(() => {
        window.scrollBy({ top: autoScrollSpeed, behavior: "smooth" });
      }, 50);
    } else {
      if (scrollIntervalRef.current) {
        clearInterval(scrollIntervalRef.current);
        scrollIntervalRef.current = null;
      }
    }
    return () => {
      if (scrollIntervalRef.current) clearInterval(scrollIntervalRef.current);
    };
  }, [autoScrollEnabled, autoScrollSpeed]);

  const fetchHighlights = useCallback(async () => {
    if (!bookId) return;
    try {
      const data = await getBookHighlightsAPI(bookId);
      setHighlights(data);
    } catch (e: any) {
      console.error("Lỗi lấy highlight:", e);
      setToastMsg({ text: e.message || "Không thể tải highlight.", type: "error" });
      setTimeout(() => setToastMsg(null), 3000);
    }
  }, [bookId]);

  useEffect(() => {
    fetchHighlights();
  }, [fetchHighlights]);

  const handleCreateHighlight = async (color: string) => {
    if (!selectionPopup || !bookId) return;
    try {
      await createHighlightAPI(bookId, {
        text: selectionPopup.text,
        color,
        chapter_slug: "",
        start_offset: 0,
        end_offset: 0,
        note: "",
      });
      setSelectionPopup(null);
      window.getSelection()?.removeAllRanges();
      fetchHighlights();
    } catch (e: any) {
      console.error("Lỗi tạo highlight:", e);
      setToastMsg({ text: e.message || "Tạo highlight thất bại.", type: "error" });
      setTimeout(() => setToastMsg(null), 3000);
    }
  };

  const handleDeleteHighlight = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      fetchHighlights();
    } catch (e: any) {
      console.error("Lỗi xóa highlight:", e);
      setToastMsg({ text: e.message || "Xóa highlight thất bại.", type: "error" });
      setTimeout(() => setToastMsg(null), 3000);
    }
  };

  const handleUpdateNote = async (highlightId: string, note: string) => {
    try {
      await updateHighlightNoteAPI(highlightId, note);
      setEditingNote(null);
      fetchHighlights();
    } catch (e: any) {
      console.error("Lỗi cập nhật ghi chú:", e);
      setToastMsg({ text: e.message || "Cập nhật ghi chú thất bại.", type: "error" });
      setTimeout(() => setToastMsg(null), 3000);
    }
  };

  const handleExportMarkdown = async () => {
    if (!bookId) return;
    try {
      const data = await exportHighlightsMarkdownAPI(bookId);
      const blob = new Blob([data.markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error("Lỗi xuất Markdown:", e);
      setToastMsg({ text: e.message || "Trích xuất Markdown thất bại.", type: "error" });
      setTimeout(() => setToastMsg(null), 3000);
    }
  };

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return;
    }
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    setSelectionPopup({
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      text: selection.toString().trim(),
    });
  }, []);

  useEffect(() => {
    document.addEventListener("mouseup", handleTextSelection);
    return () => document.removeEventListener("mouseup", handleTextSelection);
  }, [handleTextSelection]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest("[data-highlight-popup]") && !window.getSelection()?.toString().trim()) {
        setSelectionPopup(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const renderContentWithHighlights = () => {
    if (highlights.length === 0) return content;

    let result = content;
    const sortedHighlights = [...highlights].sort(
      (a, b) => b.text.length - a.text.length
    );

    const parts: { text: string; highlight?: Highlight }[] = [];
    let remaining = result;

    if (sortedHighlights.length > 0) {
      const allIndices: { start: number; end: number; highlight: Highlight }[] = [];

      for (const h of sortedHighlights) {
        let searchFrom = 0;
        while (true) {
          const idx = remaining.indexOf(h.text, searchFrom);
          if (idx === -1) break;
          allIndices.push({ start: idx, end: idx + h.text.length, highlight: h });
          searchFrom = idx + h.text.length;
        }
      }

      allIndices.sort((a, b) => a.start - b.start);

      const filtered: typeof allIndices = [];
      for (const idx of allIndices) {
        if (filtered.length === 0 || idx.start >= filtered[filtered.length - 1].end) {
          filtered.push(idx);
        }
      }

      let cursor = 0;
      for (const f of filtered) {
        if (f.start > cursor) {
          parts.push({ text: remaining.slice(cursor, f.start) });
        }
        parts.push({ text: remaining.slice(f.start, f.end), highlight: f.highlight });
        cursor = f.end;
      }
      if (cursor < remaining.length) {
        parts.push({ text: remaining.slice(cursor) });
      }
    } else {
      parts.push({ text: remaining });
    }

    return (
      <>
        {parts.map((part, i) =>
          part.highlight ? (
            <mark
              key={i}
              className="relative cursor-pointer transition-opacity duration-150 hover:opacity-80 rounded-none px-0.5"
              style={{
                backgroundColor: part.highlight.color + "40",
                borderBottom: `2px solid ${part.highlight.color}`,
              }}
              title={part.highlight.note || "Bấm để xem chi tiết"}
              onClick={() =>
                setEditingNote({
                  id: part.highlight!.id,
                  note: part.highlight!.note,
                })
              }
            >
              {part.text}
            </mark>
          ) : (
            <span key={i}>{part.text}</span>
          )
        )}
      </>
    );
  };

  return (
    <div className={`min-h-screen transition-all duration-500 ${themeClasses[theme]}`}>
      <div className="max-w-[800px] mx-auto px-8 py-20">
        <header className="mb-16 border-b border-current/10 pb-12">
           <h1 className="text-4xl font-bold tracking-tighter mb-4">{title}</h1>
           <div className="text-[12px] font-bold tracking-widest opacity-40">
             Bản đọc trực tuyến
             {highlights.length > 0 && (
               <span className="ml-4 text-foreground/60">{highlights.length} ghi chú</span>
             )}
           </div>
        </header>

        <article
          ref={articleRef}
          className="leading-relaxed prose-lg whitespace-pre-wrap font-sans"
          style={{ fontSize: `${fontSize}px` }}
        >
          {renderContentWithHighlights()}
        </article>

        {highlights.length > 0 && (
          <div className="mt-16 pt-12 border-t border-current/10 animate-in fade-in duration-300">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[12px] font-bold tracking-widest opacity-40">
                Danh sách ghi chú ({highlights.length})
              </h3>
              <button
                onClick={handleExportMarkdown}
                className="flex items-center gap-2 py-2 px-3 border border-current/10 text-[12px] font-bold tracking-widest opacity-60 hover:opacity-100 transition-all duration-150 hover:border-current/30"
                title="Xuất thành tập tin"
              >
                <Download className="w-3.5 h-3.5" />
                Xuất Markdown
              </button>
            </div>
            <div className="space-y-3">
              {highlights.map((h) => (
                <div
                  key={h.id}
                  className="flex gap-4 items-start p-4 border border-current/10 transition-all duration-150 hover:border-current/20 group"
                >
                  <div
                    className="w-3 h-3 rounded-none shrink-0 mt-1.5"
                    style={{ backgroundColor: h.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{h.text}</p>
                    {h.note && (
                      <p className="text-xs opacity-60 mt-1">{h.note}</p>
                    )}
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 shrink-0">
                    <button
                      onClick={() => setEditingNote({ id: h.id, note: h.note })}
                      className="p-1.5 hover:bg-current/10 transition-colors"
                      title="Chỉnh sửa ghi chú"
                    >
                      <PenTool className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteHighlight(h.id)}
                      className="p-1.5 hover:bg-current/10 transition-colors"
                      title="Xoá"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <footer className="mt-20 pt-12 border-t border-current/10 text-center opacity-40">
           <p className="text-[12px] font-bold tracking-widest">Hết nội dung</p>
        </footer>
      </div>

      {selectionPopup && (
        <div
          data-highlight-popup
          className="fixed z-[200] flex gap-1 bg-zinc-900 border border-zinc-700 p-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200"
          style={{
            left: `${selectionPopup.x}px`,
            top: `${selectionPopup.y}px`,
            transform: "translate(-50%, -100%)",
          }}
        >
          <div className="flex items-center gap-1 pr-2 border-r border-zinc-700">
            <Highlighter className="w-3.5 h-3.5 text-zinc-400 mr-1" />
            {HIGHLIGHT_COLORS.map((c) => (
              <button
                key={c.value}
                onClick={() => handleCreateHighlight(c.value)}
                className={`w-6 h-6 rounded-none border border-zinc-600 hover:border-white transition-all duration-150 hover:scale-110 ${c.className}`}
                title={c.label}
              />
            ))}
          </div>
          <button
            onClick={() => {
              setSelectionPopup(null);
              window.getSelection()?.removeAllRanges();
            }}
            className="p-1 text-zinc-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {editingNote && (
        <div className="fixed inset-0 z-[300] bg-black/60 flex items-center justify-center animate-in fade-in duration-200">
          <div className="bg-white border border-zinc-200 w-full max-w-md mx-4 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-4 border-b border-zinc-100">
              <span className="text-[12px] font-bold tracking-widest text-zinc-400">Ghi chú</span>
              <button
                onClick={() => setEditingNote(null)}
                className="p-1 hover:bg-zinc-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4">
              <textarea
                className="w-full border border-zinc-200 p-3 text-sm outline-none resize-none focus:border-zinc-400 transition-colors"
                rows={4}
                placeholder="Them ghi chu cho doan highlight nay"
                value={editingNote.note}
                onChange={(e) => setEditingNote({ ...editingNote, note: e.target.value })}
                autoFocus
              />
            </div>
            <div className="flex gap-2 p-4 pt-0">
              <button
                onClick={() => handleUpdateNote(editingNote.id, editingNote.note)}
                className="flex-1 py-2.5 bg-zinc-900 text-white text-[12px] font-bold tracking-widest hover:bg-zinc-800 transition-colors"
              >
                Luu ghi chu
              </button>
              <button
                onClick={() => handleDeleteHighlight(editingNote.id)}
                className="py-2.5 px-4 border border-zinc-200 text-[12px] font-bold tracking-widest hover:border-zinc-400 transition-colors"
              >
                Xoá đánh dấu
              </button>
            </div>
          </div>
        </div>
      )}

      <ReaderTools
        textContent={content}
        onFontSizeChange={setFontSize}
        onThemeChange={setTheme}
        onAutoScrollToggle={setAutoScrollEnabled}
        onScrollSpeedChange={setAutoScrollSpeed}
        onSearchQuery={setSearchQuery}
      />
      {toastMsg && (
        <div className={`fixed bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 border text-sm z-[9999] shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-300 ${toastMsg.type === 'error' ? 'bg-zinc-100 text-zinc-900 border-zinc-300 font-medium' : 'bg-zinc-900 text-zinc-100 border-zinc-700'}`}>
          {toastMsg.text}
        </div>
      )}
    </div>
  );
}
