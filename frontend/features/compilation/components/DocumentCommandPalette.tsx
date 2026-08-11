"use client";

import { useMemo, useState } from "react";
import type EditorJS from "@editorjs/editorjs";
import catalog from "./document-command-catalog.generated.json";
import {
  executeDocumentCommand,
  isVerifiedDocumentCommand,
  type DocumentCommand,
} from "./document-command-engine";
import SegmentedTabs from "@/shared/components/navigation/SegmentedTabs";
import { Button } from "@/shared/components/ui/Button";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";

const commandLabels: Record<string, string> = {
  DocLibAccessibilityChecker: "Kiểm tra trợ năng",
  DocLibAlignCenter: "Căn giữa",
  DocLibAlignJustify: "Căn đều",
  DocLibAlignLeft: "Căn trái",
  DocLibAlignRight: "Căn phải",
  DocLibClearFormatting: "Xóa định dạng",
  DocLibAllCaps: "Viết hoa toàn bộ",
  DocLibBold: "In đậm",
  DocLibItalic: "In nghiêng",
  DocLibWordUnderline: "Gạch chân",
  DocLibTextHighlightColorPicker: "Tô sáng",
  DocLibFormatPainter: "Sao chép định dạng",
  DocLibBlankPage: "Chèn trang trắng",
  DocLibActiveXCheckBox: "Chèn ô chọn",
  DocLibActiveXComboBox: "Chèn danh sách chọn",
  DocLibActiveXCommandButton: "Chèn nút lệnh",
  DocLibActiveXListBox: "Chèn hộp danh sách",
  DocLibActiveXTextBox: "Chèn ô văn bản",
  DocLibActiveXToggleButton: "Chèn nút bật tắt",
  DocLib3DModels: "Chèn mô hình ba chiều",
  DocLib3DRotation: "Xoay mô hình ba chiều",
  DocLibAlignObjects: "Căn đối tượng",
  DocLibAutoFit: "Tự động điều chỉnh bảng",
  DocLibAutoSaveSwitch: "Tự động lưu",
  DocLibAutoScroll: "Tự động cuộn",
  DocLibAllMarkup: "Hiện toàn bộ đánh dấu",
  DocLibBalloons: "Hiện chú thích bên cạnh",
  DocLibAutoCorrectCapsLockOff: "Tự sửa khi bật Caps Lock",
  DocLibAutoCorrectInitialCaps: "Tự sửa chữ cái đầu",
  DocLibAutoCorrectSentenceCaps: "Tự viết hoa đầu câu",
  DocLibAutoCorrectSmartQuotes: "Tự đổi dấu ngoặc kép",
  DocLibAutoFormatAsYouType: "Tự định dạng khi nhập",
  DocLibAltText: "Văn bản thay thế",
  DocLibArtisticEffects: "Chèn hình có hiệu ứng nghệ thuật",
  DocLibBevel: "Chèn hình nổi",
  DocLibColumnBreak: "Ngắt cột",
  DocLibColumnsOne: "Một cột",
  DocLibColumnsTwo: "Hai cột",
  DocLibColumnsThree: "Ba cột",
  DocLibContinuousSectionBreak: "Ngắt phần liên tục",
  DocLibLineNumbersContinuous: "Đánh số dòng liên tục",
  DocLibLineSpacing: "Giãn dòng",
  DocLibOrientation: "Hướng giấy",
  DocLibPaperSize: "Khổ giấy",
  DocLibCustomWatermark: "Tạo hình mờ",
  DocLibDontHyphenate: "Không ngắt từ",
  DocLibKeepLinesTogether: "Giữ các dòng cùng nhau",
  DocLibParagraphSpacingSet: "Khoảng cách đoạn",
  DocLibWidowOrphanControl: "Kiểm soát dòng góa và mồ côi",
  DocLibConvertTableToText: "Chuyển bảng thành văn bản",
  DocLibConvertTextToTable: "Chuyển văn bản thành bảng",
  DocLibInsertAbove: "Chèn hàng phía trên",
  DocLibInsertBelow: "Chèn hàng phía dưới",
  DocLibGridlines: "Hiện đường lưới",
  DocLibAutoCheckForErrors: "Kiểm tra lỗi tự động",
  DocLibDictation: "Nhập liệu bằng giọng nói",
  DocLibAutoCorrect: "Tự động sửa",
  DocLibDatePickerControl: "Chèn bộ chọn ngày",
  DocLibDocumentInspector: "Kiểm tra tài liệu",
  DocLibDraftView: "Chế độ bản thảo",
  DocLibFocusMode: "Chế độ tập trung",
  DocLibReadAloud: "Đọc thành tiếng",
  DocLibZoom: "Thu phóng",
  DocLibWordCount: "Đếm từ",
};
const commands = (catalog as DocumentCommand[])
  .filter(
    (command) =>
      commandLabels[command.id] &&
      isVerifiedDocumentCommand(command),
  )
  .map((command) => ({ ...command, title: commandLabels[command.id] }));
const categories = [
  ["all", "Tất cả"],
  ["format", "Định dạng"],
  ["insert", "Chèn"],
  ["layout", "Bố cục"],
  ["table", "Bảng"],
  ["review", "Kiểm tra"],
  ["view", "Hiển thị"],
  ["media", "Đa phương tiện"],
  ["automation", "Tự động hóa"],
  ["ai", "Trí tuệ nhân tạo"],
] as const;
const categoryLabels = Object.fromEntries(categories) as Record<string, string>;

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
  const { showToast } = useToast();
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
    if (!editor) return showToast("Trình soạn thảo chưa sẵn sàng", "error");
    if (command.requiresSelection && !window.getSelection()?.toString().trim())
      return showToast("Chọn nội dung trước khi thực hiện", "info");
    setRunning(command.id);
    try {
      const result = await executeDocumentCommand(editor, command);
      onSave(JSON.stringify(result.data));
      showToast(result.effect, "success");
    } catch (reason) {
      showToast(
        reason instanceof Error ? reason.message : "Không thể thực hiện chức năng",
        "error",
      );
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
          <p className="text-[12px] text-ink-muted">
            {filtered.length.toLocaleString("vi-VN")} chức năng
          </p>
          <div className="max-h-[420px] divide-y divide-border overflow-y-auto border-y border-border">
            {filtered.slice(0, 100).map((command) => (
              <button key={command.id} type="button" disabled={Boolean(running)} onClick={() => void run(command)} className="flex w-full items-center justify-between gap-4 px-2 py-3 text-left hover:bg-surface-quiet disabled:opacity-50">
                <span className="min-w-0">
                  <span className="block truncate text-[13px] font-semibold text-ink">{command.title}</span>
                  <span className="block text-[11px] text-ink-muted">{categoryLabels[command.category] || command.category}</span>
                </span>
                {running === command.id && (
                  <span className="text-[11px] text-ink-muted">Đang thực hiện</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </ModalContent>
      <ModalFooter><Button variant="secondary" onClick={close}>Đóng</Button></ModalFooter>
    </Modal>
  );
}
