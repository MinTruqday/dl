"use client";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

import { useState, useEffect, useRef, useCallback } from "react";
import ReaderTools from "./ReaderTools";
import {
  getHighlightsAPI,
  createHighlightAPI,
  deleteHighlightAPI,
  updateHighlightNoteAPI,
  exportHighlightsMarkdownAPI,
} from "@/services/highlight.service";
import {
  Highlighter,
  X,
  Trash2,
  PenTool,
  Download,
  Loader2,
} from "lucide-react";
import { useToast } from "@/contexts/ToastContext";

const HIGHLIGHT_COLORS = [
  { value: "#e4e4e7", label: "Nhạt", className: "bg-zinc-200" },
  { value: "#71717a", label: "Vừa", className: "bg-white0" },
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
  documentId?: string;
}

export default function Read({ content, title, documentId }: ReaderViewProps) {
  const [fontSize, setFontSize] = useState(18);
  const [theme, setTheme] = useState<"light" | "zinc" | "night">("light");
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [selectionPopup, setSelectionPopup] = useState<{
    x: number;
    y: number;
    text: string;
  } | null>(null);
  const [editingNote, setEditingNote] = useState<{
    id: string;
    note: string;
  } | null>(null);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(false);
  const [autoScrollSpeed, setAutoScrollSpeed] = useState(2);
  const [searchQuery, setSearchQuery] = useState("");
  const [notification, setNotification] = useState<{
    text: string;
    type: "error" | "success";
  } | null>(null);
  const articleRef = useRef<HTMLElement>(null);
  const scrollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const themeClasses = {
    light: "bg-white text-zinc-900",
    zinc: "bg-white text-zinc-800",
    night: "bg-black text-zinc-300",
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
    if (!documentId) return;
    try {
      const data = await getHighlightsAPI(documentId);
      setHighlights(data || []);
    } catch (err: any) {
      console.error("Lỗi tải nêu bật:", err);
    }
  }, [documentId]);

  useEffect(() => {
    fetchHighlights();
  }, [fetchHighlights]);

  const handleCreateHighlight = async (color: string) => {
    if (!selectionPopup || !documentId) return;
    try {
      await createHighlightAPI(documentId, {
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
      showToast("Đã lưu nêu bật.", "success");
    } catch (e: any) {
      showToast("Không thể lưu nêu bật lúc này.", "error");
    }
  };

  const handleDeleteHighlight = async (highlightId: string) => {
    try {
      await deleteHighlightAPI(highlightId);
      fetchHighlights();
      setEditingNote(null);
      showToast("Đã xóa nêu bật.", "success");
    } catch (e: any) {
      showToast("Xóa nêu bật thất bại.", "error");
    }
  };

  const handleUpdateNote = async (highlightId: string, note: string) => {
    try {
      await updateHighlightNoteAPI(highlightId, note);
      setEditingNote(null);
      fetchHighlights();
      showToast("Đã lưu ghi chú.", "success");
    } catch (e: any) {
      showToast("Lưu ghi chú thất bại.", "error");
    }
  };

  const handleExportMarkdown = async () => {
    if (!documentId) return;
    try {
      const data = await exportHighlightsMarkdownAPI(documentId);
      const blob = new Blob([data.markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);
      showToast("Đã trích xuất danh sách ghi chú.", "success");
    } catch (e: any) {
      showToast("Xuất dữ liệu thất bại.", "error");
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
      if (
        !target.closest("[data-highlight-popup]") &&
        !window.getSelection()?.toString().trim()
      ) {
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
      (a, b) => b.text.length - a.text.length,
    );

    const parts: { text: string; highlight?: Highlight }[] = [];
    let remaining = result;

    if (sortedHighlights.length > 0) {
      const allIndices: { start: number; end: number; highlight: Highlight }[] =
        [];

      for (const h of sortedHighlights) {
        let searchFrom = 0;
        while (true) {
          const idx = remaining.indexOf(h.text, searchFrom);
          if (idx === -1) break;
          allIndices.push({
            start: idx,
            end: idx + h.text.length,
            highlight: h,
          });
          searchFrom = idx + h.text.length;
        }
      }

      allIndices.sort((a, b) => a.start - b.start);

      const filtered: typeof allIndices = [];
      for (const idx of allIndices) {
        if (
          filtered.length === 0 ||
          idx.start >= filtered[filtered.length - 1].end
        ) {
          filtered.push(idx);
        }
      }

      let cursor = 0;
      for (const f of filtered) {
        if (f.start > cursor) {
          parts.push({ text: remaining.slice(cursor, f.start) });
        }
        parts.push({
          text: remaining.slice(f.start, f.end),
          highlight: f.highlight,
        });
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
              className="relative cursor-pointer rounded-none px-0.5 select-none"
              style={{
                backgroundColor: part.highlight.color + "30",
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
          ),
        )}
      </>
    );
  };

  return (
    <div className={`min-h-screen font-sans ${themeClasses[theme]}`}>
      <div className="max-w-[840px] mx-auto px-8 py-24 md:py-32">
        <header className="mb-20 border-b border-current/10 pb-16">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tighter mb-6 leading-tight">
            {title}
          </h1>
          <div className="text-[11px] font-bold opacity-40 flex items-center gap-4">
            <span>Bản đọc trực tuyến</span>
            {highlights.length > 0 && (
              <>
                <div className="w-1 h-1 bg-current opacity-20" />
                <span>{highlights.length} ghi chú cá nhân</span>
              </>
            )}
          </div>
        </header>

        <article
          ref={articleRef}
          className="leading-relaxed whitespace-pre-wrap font-sans selection:bg-black selection:text-white"
          style={{ fontSize: `${fontSize}px` }}
        >
          {renderContentWithHighlights()}
        </article>

        {highlights.length > 0 && (
          <div className="mt-24 pt-16 border-t border-current/10 animate-in fade-in ">
            <div className="flex items-center justify-between mb-10">
              <h3 className="text-[11px] font-bold opacity-40">
                Danh sách ghi chú ({highlights.length})
              </h3>
              <button
                onClick={handleExportMarkdown}
                className="flex items-center gap-2.5 py-3 px-5 border border-current/10 text-[10px] font-bold active:scale-95"
              >
                <Download className="w-4 h-4" />
                Xuất Markdown
              </button>
            </div>
            <div className="space-y-4">
              {highlights.map((h) => (
                <div
                  key={h.id}
                  className="flex gap-6 items-start p-6 border border-current/5 group bg-current/[0.02]"
                >
                  <div
                    className="w-3.5 h-3.5 shrink-0 mt-1.5"
                    style={{ backgroundColor: h.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate leading-relaxed">
                      {h.text}
                    </p>
                    {h.note && (
                      <p className="text-xs opacity-50 mt-2 leading-relaxed font-medium">
                        {h.note}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1 opacity-0 transition-opacity shrink-0">
                    <button
                      onClick={() => setEditingNote({ id: h.id, note: h.note })}
                      className="p-2 transition-colors"
                      title="Chỉnh sửa"
                    >
                      <PenTool className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteHighlight(h.id)}
                      className="p-2 transition-colors"
                      title="Xóa"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <footer className="mt-32 pt-16 border-t border-current/10 text-center opacity-40">
          <p className="text-[11px] font-bold">Hết nội dung</p>
        </footer>
      </div>

      {selectionPopup && (
        <div
          data-highlight-popup
          className="fixed z-[1000] flex gap-1 bg-black border border-zinc-800 p-2 animate-in fade-in slide-in-from-bottom-2 "
          style={{
            left: `${selectionPopup.x}px`,
            top: `${selectionPopup.y}px`,
            transform: "translate(-50%, -100%)",
          }}
        >
          <div className="flex items-center gap-1.5 pr-2 border-r border-zinc-800">
            <Highlighter className="w-4 h-4 text-zinc-500 mr-1.5 ml-1" />
            {HIGHLIGHT_COLORS.map((c) => (
              <button
                key={c.value}
                onClick={() => handleCreateHighlight(c.value)}
                className={`w-7 h-7 border border-white/10 active:scale-90 ${c.className}`}
                title={c.label}
              />
            ))}
          </div>
          <button
            onClick={() => {
              setSelectionPopup(null);
              window.getSelection()?.removeAllRanges();
            }}
            className="p-1.5 text-zinc-500 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <Modal
        isOpen={!!editingNote}
        onClose={() => setEditingNote(null)}
        className="max-w-lg"
      >
        <ModalHeader>
          <ModalTitle>Ghi chú cá nhân</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <textarea
            className="w-full border border-zinc-100 bg-white p-6 text-sm font-medium outline-none resize-none focus:border-black min-h-[160px] rounded-sm transition-colors"
            placeholder=""
            value={editingNote?.note}
            onChange={(e) =>
              setEditingNote({ ...editingNote, note: e.target.value })
            }
            autoFocus
          />
        </ModalContent>
        <ModalFooter className="flex gap-4">
          <button
            onClick={() =>
              handleUpdateNote(editingNote.id, editingNote.note)
            }
            className="flex-1 h-14 bg-black text-white text-[11px] font-bold uppercase tracking-widest active:scale-95 rounded-sm transition-transform"
          >
            Lưu ghi chú
          </button>
          <button
            onClick={() => handleDeleteHighlight(editingNote.id)}
            className="h-14 px-8 border border-zinc-200 text-[11px] font-bold text-zinc-400 uppercase tracking-widest active:scale-95 rounded-sm transition-transform"
          >
            Xóa nêu bật
          </button>
        </ModalFooter>
      </Modal>

      <ReaderTools
        textContent={content}
        onFontSizeChange={setFontSize}
        onThemeChange={setTheme}
        onAutoScrollToggle={setAutoScrollEnabled}
        onScrollSpeedChange={setAutoScrollSpeed}
        onSearchQuery={setSearchQuery}
      />
    </div>
  );
}
