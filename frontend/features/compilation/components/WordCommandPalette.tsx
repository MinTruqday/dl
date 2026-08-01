"use client";

import React, { useEffect, useMemo, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import { Search, X } from "lucide-react";
import { WORD_COMMANDS } from "./word-command-catalog";
import {
  executeWordCommand,
  type WordCommandCategory,
} from "./word-command-engine";

interface WordCommandPaletteProps {
  editorRef: React.MutableRefObject<EditorJS | null>;
  onSave?: (data: string) => void;
  showToast?: (
    message: string,
    type?: "success" | "error" | "info" | "warning",
  ) => void;
}

const categories: Array<WordCommandCategory | "all"> = [
  "all",
  "format",
  "insert",
  "layout",
  "table",
  "review",
  "reference",
  "mailing",
  "view",
  "media",
  "security",
  "automation",
  "ai",
];

export default function WordCommandPalette({
  editorRef,
  onSave,
  showToast,
}: WordCommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<WordCommandCategory | "all">("all");
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key.toLowerCase() === "p") {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const commands = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return WORD_COMMANDS.filter(
      (command) =>
        (category === "all" || command.category === category) &&
        (!normalized ||
          command.title.toLowerCase().includes(normalized) ||
          command.id.toLowerCase().includes(normalized)),
    );
  }, [category, query]);

  const run = async (commandId: string) => {
    const editor = editorRef.current;
    const command = WORD_COMMANDS.find((item) => item.id === commandId);
    if (!editor || !command) {
      showToast?.("Editor is not ready", "error");
      return;
    }
    if (
      command.requiresSelection &&
      !window.getSelection()?.toString().trim()
    ) {
      showToast?.("Select text before running this command", "info");
      return;
    }
    setRunning(command.id);
    try {
      const data = await executeWordCommand(editor, command);
      onSave?.(JSON.stringify(data));
      showToast?.(`${command.title} applied`, "success");
      setOpen(false);
      setQuery("");
    } catch (error) {
      showToast?.(
        error instanceof Error ? error.message : "Command failed",
        "error",
      );
    } finally {
      setRunning(null);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="px-4 py-1.5 border border-border text-ink-muted text-xs font-bold active:scale-[0.98] whitespace-nowrap shrink-0 rounded-lg hover:bg-surface-raised flex items-center gap-1.5"
        title="Word commands"
      >
        <Search className="w-3.5 h-3.5" />
        Word features
        <span className="text-ink-faint">2296 commands 2449 features</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-[80] bg-ink/30 flex items-start justify-center pt-[10vh]">
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Word features"
            className="w-[min(760px,92vw)] max-h-[80vh] bg-white border border-border-strong rounded-xl shadow-2xl flex flex-col overflow-hidden"
          >
            <div className="p-4 border-b border-border flex items-center gap-3">
              <Search className="w-4 h-4 text-ink-faint" />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search 2296 DocLib commands"
                className="flex-1 text-sm outline-none"
              />
              <span className="text-xs text-ink-faint">{commands.length}</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="p-1 text-ink-muted"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-4 py-3 border-b border-border flex gap-2 overflow-x-auto">
              {categories.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() => setCategory(item)}
                  className={`px-3 py-1 text-xs rounded-full capitalize whitespace-nowrap ${
                    category === item
                      ? "bg-ink text-white"
                      : "bg-surface-quiet text-ink-muted"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto p-2">
              {commands.map((command) => (
                <button
                  type="button"
                  key={command.id}
                  disabled={running !== null}
                  onClick={() => run(command.id)}
                  className="w-full px-3 py-2.5 flex items-center justify-between text-left rounded-lg hover:bg-surface-quiet disabled:opacity-50"
                >
                  <span>
                    <span className="block text-sm font-medium text-ink">
                      {command.title}
                    </span>
                    <span className="block text-xs text-ink-faint capitalize">
                      {command.category}
                    </span>
                  </span>
                  <span className="text-xs text-ink-faint">
                    {running === command.id ? "Running" : "Run"}
                  </span>
                </button>
              ))}
              {commands.length === 0 && (
                <div className="p-10 text-center text-sm text-ink-faint">
                  No matching feature
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
