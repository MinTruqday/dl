import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";

export type DocumentCommand = {
  id: string;
  title: string;
  category: string;
  mode: string;
  requiresSelection: boolean;
  implementation: "direct" | "bridge";
};

export type DocumentCommandState = {
  schemaVersion?: 1;
  commands: Record<
    string,
    {
      mode: string;
      enabled: boolean;
      appliedAt: number;
      parameters?: Record<string, unknown>;
    }
  >;
};

export type DocumentOutputData = OutputData & {
  documentCommandState?: DocumentCommandState;
};

const states = new WeakMap<EditorJS, DocumentCommandState>();
const verifiedPersistentCommands = new Set([
  "DocLibAutoSaveSwitch",
  "DocLibAutoScroll",
  "DocLibAllMarkup",
  "DocLibBalloons",
  "DocLibAutoCorrectCapsLockOff",
  "DocLibAutoCorrectInitialCaps",
  "DocLibAutoCorrectSentenceCaps",
  "DocLibAutoCorrectSmartQuotes",
  "DocLibAutoFormatAsYouType",
  "DocLibColumnsOne",
  "DocLibColumnsTwo",
  "DocLibColumnsThree",
  "DocLibCustomWatermark",
  "DocLibDontHyphenate",
  "DocLibKeepLinesTogether",
  "DocLibLineSpacing",
  "DocLibOrientation",
  "DocLibPaperSize",
  "DocLibParagraphSpacingSet",
  "DocLibWidowOrphanControl",
  "DocLibZoom",
]);
const verifiedInteractiveCommands = new Set([
  "DocLibAutoSaveSwitch",
  "DocLibAutoScroll",
  "DocLibAllMarkup",
  "DocLibBalloons",
  "DocLibAutoCorrectCapsLockOff",
  "DocLibAutoCorrectInitialCaps",
  "DocLibAutoCorrectSentenceCaps",
  "DocLibAutoCorrectSmartQuotes",
  "DocLibAutoFormatAsYouType",
  "DocLibClearFormatting",
  "DocLibAllCaps",
  "DocLibAccessibilityChecker",
  "DocLibAlignCenter",
  "DocLibAlignJustify",
  "DocLibAlignLeft",
  "DocLibAlignRight",
  "DocLibBlankPage",
  "DocLibActiveXCheckBox",
  "DocLibActiveXComboBox",
  "DocLibActiveXCommandButton",
  "DocLibActiveXListBox",
  "DocLibActiveXTextBox",
  "DocLibActiveXToggleButton",
  "DocLib3DModels",
  "DocLib3DRotation",
  "DocLibAlignObjects",
  "DocLibAutoFit",
  "DocLibAltText",
  "DocLibArtisticEffects",
  "DocLibBevel",
  "DocLibAutoCheckForErrors",
  "DocLibBold",
  "DocLibColumnBreak",
  "DocLibColumnsOne",
  "DocLibColumnsTwo",
  "DocLibColumnsThree",
  "DocLibCustomWatermark",
  "DocLibDontHyphenate",
  "DocLibDocumentInspector",
  "DocLibKeepLinesTogether",
  "DocLibLineSpacing",
  "DocLibOrientation",
  "DocLibPaperSize",
  "DocLibParagraphSpacingSet",
  "DocLibConvertTableToText",
  "DocLibConvertTextToTable",
  "DocLibInsertAbove",
  "DocLibInsertBelow",
  "DocLibItalic",
  "DocLibWordUnderline",
  "DocLibTextHighlightColorPicker",
  "DocLibReadAloud",
  "DocLibZoom",
  "DocLibWordCount",
  "DocLibWidowOrphanControl",
]);

export function isVerifiedDocumentCommand(command: DocumentCommand) {
  return verifiedInteractiveCommands.has(command.id);
}
export function registerDocumentCommandState(editor: EditorJS, state?: DocumentCommandState) {
  const commands = Object.fromEntries(
    Object.entries(state?.commands ?? {}).filter(
      ([id, value]) =>
        verifiedPersistentCommands.has(id) &&
        value &&
        typeof value.mode === "string" &&
        typeof value.enabled === "boolean" &&
        Number.isFinite(value.appliedAt),
    ),
  );
  states.set(editor, { schemaVersion: 1, commands });
}

export function attachDocumentCommandState(editor: EditorJS, data: OutputData): DocumentOutputData {
  return {
    ...data,
    documentCommandState: states.get(editor) ?? { schemaVersion: 1, commands: {} },
  };
}

function latestEnabledCommand(
  state: DocumentCommandState,
  ids: string[],
) {
  return ids
    .map((id) => ({ id, value: state.commands[id] }))
    .filter(({ value }) => value?.enabled)
    .sort((left, right) => right.value.appliedAt - left.value.appliedAt)[0];
}

function updatePersistentCommandState(
  state: DocumentCommandState,
  command: DocumentCommand,
) {
  const previous = state.commands[command.id];
  const appliedAt = Date.now();
  if (command.id.startsWith("DocLibColumns")) {
    for (const id of ["DocLibColumnsOne", "DocLibColumnsTwo", "DocLibColumnsThree"]) {
      if (state.commands[id]) state.commands[id].enabled = false;
    }
    const count = command.id.endsWith("One") ? 1 : command.id.endsWith("Two") ? 2 : 3;
    state.commands[command.id] = {
      mode: command.mode,
      enabled: true,
      appliedAt,
      parameters: { count },
    };
    return;
  }
  if (command.id === "DocLibZoom") {
    const values = [125, 150, 200, 100];
    const current = Number(previous?.parameters?.percent ?? 100);
    state.commands[command.id] = {
      mode: command.mode,
      enabled: true,
      appliedAt,
      parameters: { percent: values[(values.indexOf(current) + 1) % values.length] },
    };
    return;
  }
  if (command.id === "DocLibLineSpacing") {
    const values = [1.15, 1.5, 2];
    const current = Number(previous?.parameters?.value ?? 1);
    state.commands[command.id] = {
      mode: command.mode,
      enabled: true,
      appliedAt,
      parameters: { value: values[(values.indexOf(current) + 1) % values.length] },
    };
    return;
  }
  if (command.id === "DocLibOrientation") {
    const current = String(previous?.parameters?.value ?? "portrait");
    state.commands[command.id] = {
      mode: command.mode,
      enabled: true,
      appliedAt,
      parameters: { value: current === "portrait" ? "landscape" : "portrait" },
    };
    return;
  }
  if (command.id === "DocLibPaperSize") {
    const values = ["Letter", "Legal", "A4"];
    const current = String(previous?.parameters?.value ?? "A4");
    state.commands[command.id] = {
      mode: command.mode,
      enabled: true,
      appliedAt,
      parameters: { value: values[(values.indexOf(current) + 1) % values.length] },
    };
    return;
  }
  state.commands[command.id] = {
    mode: command.mode,
    enabled: !previous?.enabled,
    appliedAt,
    parameters: previous?.parameters,
  };
}

export function applyPersistentDocumentCommandState(editor: EditorJS) {
  const root = document.querySelector<HTMLElement>(".codex-editor");
  if (!root) throw new Error("Trình soạn thảo chưa sẵn sàng");
  const content =
    root.querySelector<HTMLElement>(".codex-editor__redactor") ?? root;
  const state = states.get(editor) ?? { schemaVersion: 1 as const, commands: {} };
  root.dataset.autoSave = state.commands.DocLibAutoSaveSwitch?.enabled === false ? "false" : "true";
  root.dataset.autoScroll = state.commands.DocLibAutoScroll?.enabled === false ? "false" : "true";
  root.dataset.reviewMarkup = state.commands.DocLibAllMarkup?.enabled === false ? "false" : "true";
  root.dataset.reviewBalloons = state.commands.DocLibBalloons?.enabled === false ? "false" : "true";
  [
    "DocLibAutoCorrectCapsLockOff",
    "DocLibAutoCorrectInitialCaps",
    "DocLibAutoCorrectSentenceCaps",
    "DocLibAutoCorrectSmartQuotes",
    "DocLibAutoFormatAsYouType",
  ].forEach((commandId) => {
    const setting = state.commands[commandId];
    if (setting?.parameters?.setting) {
      root.dataset[setting.parameters.setting as string] = setting.enabled === false ? "false" : "true";
    }
  });

  const columns = latestEnabledCommand(state, [
    "DocLibColumnsOne",
    "DocLibColumnsTwo",
    "DocLibColumnsThree",
  ]);
  const defaultColumnCount = columns?.id.endsWith("One")
    ? 1
    : columns?.id.endsWith("Two")
      ? 2
      : 3;
  const columnCount = columns
    ? Number(columns.value.parameters?.count ?? defaultColumnCount)
    : 1;
  content.style.columnCount = String(Math.min(3, Math.max(1, columnCount)));

  const zoom = state.commands.DocLibZoom;
  const zoomPercent = zoom?.enabled
    ? Number(zoom.parameters?.percent ?? 100)
    : 100;
  root.style.zoom = `${Math.min(200, Math.max(50, zoomPercent))}%`;
  const lineSpacing = state.commands.DocLibLineSpacing;
  const lineHeight = lineSpacing?.enabled
    ? Number(lineSpacing.parameters?.value ?? 1.5)
    : 1.5;
  content.style.lineHeight = String(Math.min(3, Math.max(1, lineHeight)));
  const widowOrphan = state.commands.DocLibWidowOrphanControl;
  const protectedLines = widowOrphan?.enabled
    ? Number(widowOrphan.parameters?.lines ?? 2)
    : 2;
  content.style.setProperty("widows", String(Math.min(4, Math.max(2, protectedLines))));
  content.style.setProperty("orphans", String(Math.min(4, Math.max(2, protectedLines))));
  const keepLinesTogether = state.commands.DocLibKeepLinesTogether?.enabled === true;
  content.querySelectorAll<HTMLElement>(".ce-block").forEach((block) => {
    block.style.breakInside = keepLinesTogether ? "avoid" : "auto";
  });
  content.style.hyphens = state.commands.DocLibDontHyphenate?.enabled
    ? "none"
    : "manual";
  const paragraphSpacing = state.commands.DocLibParagraphSpacingSet;
  const paragraphBefore = paragraphSpacing?.enabled
    ? Number(paragraphSpacing.parameters?.before ?? 0)
    : 0;
  const paragraphAfter = paragraphSpacing?.enabled
    ? Number(paragraphSpacing.parameters?.after ?? 8)
    : 0;
  content.querySelectorAll<HTMLElement>(".ce-paragraph").forEach((paragraph) => {
    paragraph.style.marginBlockStart = `${Math.min(72, Math.max(0, paragraphBefore))}px`;
    paragraph.style.marginBlockEnd = `${Math.min(72, Math.max(0, paragraphAfter))}px`;
  });
  const orientation = state.commands.DocLibOrientation;
  const orientationValue = orientation?.enabled
    ? String(orientation.parameters?.value ?? "landscape")
    : "portrait";
  const paperSize = state.commands.DocLibPaperSize;
  const paperSizeValue = paperSize?.enabled
    ? String(paperSize.parameters?.value ?? "A4")
    : "A4";
  const pageWidths: Record<string, { portrait: number; landscape: number }> = {
    A4: { portrait: 794, landscape: 1123 },
    Letter: { portrait: 816, landscape: 1056 },
    Legal: { portrait: 816, landscape: 1344 },
  };
  const dimensions = pageWidths[paperSizeValue] ?? pageWidths.A4;
  root.style.maxWidth = `${dimensions[orientationValue === "landscape" ? "landscape" : "portrait"]}px`;
  root.style.marginInline = "auto";

  root.querySelector("[data-doclib-watermark]")?.remove();
  const watermark = state.commands.DocLibCustomWatermark;
  if (watermark?.enabled) {
    const layer = document.createElement("div");
    layer.dataset.doclibWatermark = "true";
    layer.textContent = String(watermark.parameters?.text ?? "TÀI LIỆU").slice(0, 120);
    layer.setAttribute("aria-hidden", "true");
    Object.assign(layer.style, {
      position: "absolute",
      inset: "35% 0 auto",
      zIndex: "0",
      pointerEvents: "none",
      textAlign: "center",
      fontSize: "64px",
      fontWeight: "700",
      color: "rgba(100, 116, 139, 0.14)",
      transform: "rotate(-30deg)",
    });
    if (getComputedStyle(root).position === "static") root.style.position = "relative";
    root.prepend(layer);
  }
}

function escapeEditorText(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function plainEditorValue(value: unknown): string {
  if (typeof value === "string") {
    const template = document.createElement("template");
    template.innerHTML = value;
    return template.content.textContent ?? "";
  }
  if (Array.isArray(value)) return value.map(plainEditorValue).join(" ");
  if (value && typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .filter(([key]) => ["text", "content", "title", "caption", "items"].includes(key))
      .map(([, item]) => plainEditorValue(item))
      .join(" ");
  }
  return "";
}

async function executeNativeDocumentCommand(
  editor: EditorJS,
  command: DocumentCommand,
) {
  if (["DocLibBlankPage", "DocLibColumnBreak"].includes(command.id)) {
    editor.blocks.insert("pageBreak", {
      kind: command.id === "DocLibColumnBreak" ? "ColumnBreak" : "BlankPage",
    });
    return command.id === "DocLibColumnBreak" ? "Đã chèn ngắt cột" : "Đã chèn trang trắng";
  }
  const insertedBlocks: Record<string, { type: string; data: Record<string, unknown> }> = {
    DocLib3DModels: { type: "shape", data: { title: command.title, effect: "3DModels", url: "" } },
    DocLib3DRotation: { type: "shape", data: { title: command.title, effect: "3DRotation", url: "" } },
    DocLibAlignObjects: { type: "image", data: { title: command.title, effect: "AlignObjects", url: "" } },
    DocLibActiveXCheckBox: { type: "formCheckBox", data: { label: command.title, checked: false } },
    DocLibActiveXComboBox: { type: "formDropdown", data: { label: command.title, options: [] } },
    DocLibActiveXCommandButton: { type: "formButton", data: { label: command.title } },
    DocLibActiveXListBox: { type: "formList", data: { label: command.title, options: [] } },
    DocLibActiveXTextBox: { type: "formText", data: { label: command.title, value: "" } },
    DocLibActiveXToggleButton: { type: "formToggle", data: { label: command.title, checked: false } },
    DocLibAltText: { type: "image", data: { title: command.title, effect: "AltText", url: "" } },
    DocLibArtisticEffects: { type: "image", data: { title: command.title, effect: "ArtisticEffects", url: "" } },
    DocLibBevel: { type: "image", data: { title: command.title, effect: "Bevel", url: "" } },
  };
  const insert = insertedBlocks[command.id];
  if (insert) {
    editor.blocks.insert(insert.type, insert.data);
    return "Đã chèn nội dung vào tài liệu";
  }
  if (command.id === "DocLibAutoFit") {
    const table = document.getSelection()?.anchorNode instanceof HTMLElement
      ? document.getSelection()?.anchorNode?.parentElement?.closest("table")
      : null;
    if (!table) throw new Error("Chọn bảng trước khi tự động điều chỉnh");
    table.style.width = "auto";
    table.dispatchEvent(new InputEvent("input", { bubbles: true }));
    return "Đã tự động điều chỉnh bảng";
  }
  if (["DocLibBold", "DocLibItalic"].includes(command.id)) {
    const browserCommand = command.id === "DocLibBold" ? "bold" : "italic";
    if (!document.execCommand(browserCommand))
      throw new Error("Chọn nội dung văn bản trước khi định dạng");
    return command.id === "DocLibItalic" ? "Đã in nghiêng" : "Đã in đậm";
  }
  if (command.id === "DocLibWordUnderline" || command.id === "DocLibTextHighlightColorPicker") {
    const browserCommand = command.id === "DocLibWordUnderline" ? "underline" : "hiliteColor";
    const value = command.id === "DocLibTextHighlightColorPicker" ? "#fef08a" : "";
    if (!document.execCommand(browserCommand, false, value ?? ""))
      throw new Error("Trình duyệt không áp dụng được định dạng đã chọn");
    return command.id === "DocLibWordUnderline" ? "Đã gạch chân" : "Đã tô sáng nội dung";
  }
  if (command.id === "DocLibReadAloud") {
    if (!("speechSynthesis" in window))
      throw new Error("Trình duyệt không hỗ trợ đọc thành tiếng");
    const data = await editor.save();
    const text = data.blocks.map((block) => plainEditorValue(block.data)).join("\n").trim();
    if (!text) throw new Error("Tài liệu chưa có nội dung để đọc");
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "vi-VN";
    window.speechSynthesis.speak(utterance);
    return "Đang đọc nội dung tài liệu";
  }
  if (command.id === "DocLibClearFormatting") {
    if (!document.execCommand("removeFormat"))
      throw new Error("Không thể xóa định dạng của nội dung đã chọn");
    return "Đã xóa định dạng";
  }
  if (command.id === "DocLibAllCaps") {
    const selection = window.getSelection()?.toString() ?? "";
    if (!selection || !document.execCommand("insertText", false, selection.toUpperCase()))
      throw new Error("Không thể chuyển nội dung đã chọn thành chữ hoa");
    return "Đã chuyển thành chữ hoa";
  }
  if (
    [
      "DocLibAccessibilityChecker",
      "DocLibAutoCheckForErrors",
      "DocLibDocumentInspector",
      "DocLibWordCount",
    ].includes(command.id)
  ) {
    const data = await editor.save();
    const text = data.blocks.map((block) => plainEditorValue(block.data)).join("\n");
    const words = text.match(/\b[\p{L}\p{N}_]+\b/gu) ?? [];
    if (command.id === "DocLibWordCount")
      return `${words.length.toLocaleString("vi-VN")} từ · ${text.length.toLocaleString("vi-VN")} ký tự`;
    const missingAlt = data.blocks.filter(
      (block) =>
        ["image", "simpleImage", "imageCrop", "imageWithLink"].includes(block.type) &&
        !String(block.data?.alt ?? block.data?.caption ?? "").trim(),
    ).length;
    if (command.id === "DocLibAccessibilityChecker")
      return missingAlt
        ? `Phát hiện ${missingAlt} ảnh chưa có văn bản thay thế`
        : "Không phát hiện lỗi trợ năng cơ bản";
    if (command.id === "DocLibAutoCheckForErrors") {
      const repeatedWords = text.match(/\b([\p{L}\p{N}_]+)\s+\1\b/giu) ?? [];
      const spacing = text.match(/ {2,}|\s+[,.!?;:]/g) ?? [];
      const count = repeatedWords.length + spacing.length;
      return count
        ? `Phát hiện ${count} lỗi khoảng trắng hoặc từ lặp`
        : "Không phát hiện lỗi văn bản cơ bản";
    }
    const rawBlocks = data.blocks.filter((block) => ["raw", "html"].includes(block.type)).length;
    return `Đã kiểm tra ${data.blocks.length} khối · ${missingAlt} ảnh thiếu mô tả · ${rawBlocks} khối HTML thô`;
  }
  const alignments: Record<string, "left" | "center" | "right" | "justify"> = {
    DocLibAlignLeft: "left",
    DocLibAlignCenter: "center",
    DocLibAlignRight: "right",
    DocLibAlignJustify: "justify",
  };
  if (alignments[command.id]) {
    const index = editor.blocks.getCurrentBlockIndex();
    const block = index >= 0 ? editor.blocks.getBlockByIndex(index) : undefined;
    if (!block) throw new Error("Chọn khối văn bản trước khi căn chỉnh");
    const saved = await block.save();
    if (!saved || !["paragraph", "header", "quote"].includes(block.name))
      throw new Error("Khối hiện tại không hỗ trợ căn chỉnh");
    await editor.blocks.update(block.id, {
      ...saved.data,
      alignment: alignments[command.id],
    });
    return `Đã căn ${
      alignments[command.id] === "left"
        ? "trái"
        : alignments[command.id] === "right"
          ? "phải"
          : alignments[command.id] === "center"
            ? "giữa"
            : "đều"
    }`;
  }
  if (command.id === "DocLibConvertTextToTable") {
    const selection = window.getSelection()?.toString() ?? "";
    if (!selection.trim()) throw new Error("Chọn văn bản cần chuyển thành bảng");
    const content = selection
      .split(/\r?\n/)
      .filter((row) => row.length > 0)
      .map((row) => row.split("\t"));
    if (!document.execCommand("delete"))
      throw new Error("Không thể xóa văn bản gốc sau khi chuyển đổi");
    const index = editor.blocks.getCurrentBlockIndex();
    editor.blocks.insert(
      "table",
      { content, withHeadings: false },
      undefined,
      index + 1,
      true,
    );
    return "Đã chuyển văn bản thành bảng";
  }
  if (
    ![
      "DocLibConvertTableToText",
      "DocLibInsertAbove",
      "DocLibInsertBelow",
    ].includes(command.id)
  ) {
    return null;
  }
  const index = editor.blocks.getCurrentBlockIndex();
  const block = index >= 0 ? editor.blocks.getBlockByIndex(index) : undefined;
  if (!block || block.name !== "table")
    throw new Error("Chọn một ô trong bảng trước khi thực hiện");
  const saved = await block.save();
  if (!saved) throw new Error("Không thể đọc dữ liệu bảng");
  const content = saved.data?.content;
  if (!Array.isArray(content) || !content.every(Array.isArray))
    throw new Error("Dữ liệu bảng không hợp lệ");

  if (command.id === "DocLibConvertTableToText") {
    const text = content
      .map((row) => row.map((cell) => escapeEditorText(String(cell ?? ""))).join("\t"))
      .join("<br>");
    editor.blocks.delete(index);
    editor.blocks.insert("paragraph", { text }, undefined, index, true);
    return "Đã chuyển bảng thành văn bản";
  }

  const selectedRow = window.getSelection()?.anchorNode?.parentElement?.closest("tr");
  const domRowIndex = selectedRow instanceof HTMLTableRowElement
    ? selectedRow.rowIndex
    : command.id === "DocLibInsertBelow"
      ? content.length - 1
      : 0;
  const targetIndex = command.id === "DocLibInsertBelow"
    ? Math.min(content.length, domRowIndex + 1)
    : Math.max(0, domRowIndex);
  const columnCount = Math.max(1, ...content.map((row) => row.length));
  const nextContent = content.map((row) => [...row]);
  nextContent.splice(targetIndex, 0, Array(columnCount).fill(""));
  await editor.blocks.update(block.id, { ...saved.data, content: nextContent });
  return command.id === "DocLibInsertBelow"
    ? "Đã chèn hàng bên dưới"
    : "Đã chèn hàng bên trên";
}

export async function executeDocumentCommand(editor: EditorJS, command: DocumentCommand) {
  if (!isVerifiedDocumentCommand(command)) {
    throw new Error("Chức năng này chưa vượt qua kiểm thử hành vi");
  }
  if (verifiedPersistentCommands.has(command.id)) {
    const state = states.get(editor) ?? { schemaVersion: 1 as const, commands: {} };
    updatePersistentCommandState(state, command);
    states.set(editor, state);
    applyPersistentDocumentCommandState(editor);
    return {
      data: attachDocumentCommandState(editor, await editor.save()),
      effect: `Đã áp dụng ${command.title}`,
    };
  }
  const effect = await executeNativeDocumentCommand(editor, command);
  if (!effect)
    throw new Error("Chức năng chưa có bộ thực thi đã được xác minh");
  return {
    data: attachDocumentCommandState(editor, await editor.save()),
    effect,
  };
}
