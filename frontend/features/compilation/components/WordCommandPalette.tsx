"use client";

import React, { useEffect, useMemo, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import { Search } from "lucide-react";
import { WORD_COMMANDS } from "./word-command-catalog";
import {
  executeWordCommand,
  type WordCommandCategory,
} from "./word-command-engine";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

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

const categoryLabels: Record<WordCommandCategory | "all", string> = {
  all: "Tất cả",
  format: "Định dạng",
  insert: "Chèn",
  layout: "Bố cục",
  table: "Bảng",
  review: "Rà soát",
  reference: "Tham chiếu",
  mailing: "Thư",
  view: "Hiển thị",
  media: "Nội dung",
  security: "Bảo mật",
  automation: "Tự động hóa",
  ai: "Metis",
};

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
      showToast?.("Trình soạn thảo chưa sẵn sàng", "error");
      return;
    }
    if (
      command.requiresSelection &&
      !window.getSelection()?.toString().trim()
    ) {
      showToast?.("Chọn nội dung trước khi chạy lệnh", "info");
      return;
    }
    setRunning(command.id);
    try {
      const data = await executeWordCommand(editor, command);
      onSave?.(JSON.stringify(data));
      showToast?.(`Đã chạy ${command.title}`, "success");
      setOpen(false);
      setQuery("");
    } catch (error) {
      showToast?.(
        error instanceof Error ? error.message : "Không thể chạy lệnh",
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
        className="button-secondary shrink-0 gap-2"
        title="Lệnh soạn thảo"
      >
        <Search className="w-3.5 h-3.5" />
        Lệnh soạn thảo
      </button>

      <Modal
        isOpen={open}
        onClose={() => setOpen(false)}
        className="max-w-[760px]"
      >
        <ModalHeader>
          <ModalTitle>Lệnh soạn thảo</ModalTitle>
        </ModalHeader>
        <ModalContent>
            <div className="flex items-center gap-3">
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Tìm lệnh"
                className="field-control min-w-0 flex-1"
              />
              <span className="text-[13px] text-[var(--ink-muted)]">
                {commands.length}
              </span>
            </div>

            <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
              {categories.map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() => setCategory(item)}
                  className={`whitespace-nowrap rounded-[var(--radius-control)] px-3 py-1.5 text-[12px] ${
                    category === item
                      ? "bg-[var(--brand-soft)] text-[var(--brand)]"
                      : "bg-[var(--surface-quiet)] text-[var(--ink-muted)]"
                  }`}
                >
                  {categoryLabels[item]}
                </button>
              ))}
            </div>

            <div className="mt-2 max-h-[52dvh] overflow-y-auto">
              {commands.map((command) => (
                <button
                  type="button"
                  key={command.id}
                  disabled={running !== null}
                  onClick={() => run(command.id)}
                  className="flex w-full items-center justify-between rounded-[var(--radius-control)] px-3 py-2.5 text-left hover:bg-[var(--surface-quiet)] disabled:opacity-50"
                >
                  <span>
                    <span className="block text-[14px] font-medium text-[var(--ink)]">
                      {command.title}
                    </span>
                    <span className="block text-[12px] text-[var(--ink-muted)]">
                      {categoryLabels[command.category]}
                    </span>
                  </span>
                  <span className="text-[12px] text-[var(--ink-muted)]">
                    {running === command.id ? "Đang chạy" : "Chạy"}
                  </span>
                </button>
              ))}
              {commands.length === 0 && (
                <div className="p-10 text-center text-[14px] text-[var(--ink-muted)]">
                  Không có lệnh phù hợp
                </div>
              )}
            </div>
        </ModalContent>
      </Modal>
    </>
  );
}
