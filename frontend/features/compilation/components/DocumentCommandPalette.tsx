"use client";

import { useMemo, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import catalog from "./document-command-catalog.generated.json";
import {
  executeDocumentCommand,
  type DocumentCommand,
} from "./document-command-engine";
import SegmentedTabs from "@/app/_components/SegmentedTabs";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

const commands = catalog as DocumentCommand[];
const categories = [
  ["all", "Tất cả"],
  ["format", "Định dạng"],
  ["insert", "Chèn"],
  ["layout", "Bố cục"],
  ["table", "Bảng"],
  ["review", "Kiểm tra"],
  ["reference", "Tham chiếu"],
  ["view", "Hiển thị"],
  ["media", "Đa phương tiện"],
  ["mailing", "Trộn thư"],
  ["automation", "Tự động hóa"],
  ["ai", "Trí tuệ nhân tạo"],
  ["security", "Bảo mật"],
] as const;

export default function DocumentCommandPalette({
  open,
  close,
  editorRef,
  onSave,
}: {
  open: boolean;
  close: () => void;
  editorRef: React.MutableRefObject<EditorJS | null>;
  onSave: (value: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [running, setRunning] = useState("");
  const [notice, setNotice] = useState("");
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return commands.filter(
      (command) =>
        (category === "all" || command.category === category) &&
        (!normalized || command.title.toLowerCase().includes(normalized) || command.id.toLowerCase().includes(normalized)),
    );
  }, [category, query]);
  const run = async (command: DocumentCommand) => {
    const editor = editorRef.current;
    if (!editor) return setNotice("Trình soạn thảo chưa sẵn sàng");
    if (command.requiresSelection && !window.getSelection()?.toString().trim())
      return setNotice("Chọn nội dung trước khi thực hiện");
    setRunning(command.id);
    setNotice("");
    try {
      const result = await executeDocumentCommand(editor, command);
      onSave(JSON.stringify(result.data));
      setNotice(result.effect);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : "Không thể thực hiện chức năng");
    } finally {
      setRunning("");
    }
  };
  return (
    <Modal isOpen={open} onClose={close} className="max-w-3xl">
      <ModalHeader><ModalTitle>Chức năng tài liệu</ModalTitle></ModalHeader>
      <ModalContent>
        <div className="space-y-4">
          <input value={query} onChange={(event) => setQuery(event.target.value)} className="apple-input w-full" placeholder="Tìm chức năng" />
          <SegmentedTabs label="Nhóm chức năng" value={category} onChange={setCategory} tabs={categories.map(([id, label]) => ({ id, label }))} />
          <div className="flex items-center justify-between text-[12px] text-ink-muted">
            <span>{filtered.length.toLocaleString("vi-VN")} chức năng</span>
            <span>Hiển thị tối đa 100 kết quả</span>
          </div>
          <div className="max-h-[420px] divide-y divide-border overflow-y-auto border-y border-border">
            {filtered.slice(0, 100).map((command) => (
              <button key={command.id} type="button" disabled={Boolean(running)} onClick={() => void run(command)} className="flex w-full items-center justify-between gap-4 px-2 py-3 text-left hover:bg-surface-quiet disabled:opacity-50">
                <span className="min-w-0">
                  <span className="block truncate text-[13px] font-semibold text-ink">{command.title}</span>
                  <span className="block text-[11px] text-ink-muted">{command.category}</span>
                </span>
                <span className="text-[11px] text-ink-muted">{running === command.id ? "Đang chạy" : command.implementation === "direct" ? "Trực tiếp" : "Tài liệu"}</span>
              </button>
            ))}
          </div>
          {notice && <p role="status" className="text-[13px] text-ink">{notice}</p>}
        </div>
      </ModalContent>
      <ModalFooter><Button variant="secondary" onClick={close}>Đóng</Button></ModalFooter>
    </Modal>
  );
}
