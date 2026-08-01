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
  commands: Record<string, { mode: string; enabled: boolean; appliedAt: number }>;
};

export type DocumentOutputData = OutputData & {
  documentCommandState?: DocumentCommandState;
};

const states = new WeakMap<EditorJS, DocumentCommandState>();
const commandEvents = [
  "doclib-editor-command",
  "doclib-review-command",
  "doclib-word-automation",
  "doclib-reference-command",
  "doclib-ai-command",
  "doclib-table-command",
  "doclib-format-command",
  "doclib-layout-command",
  "doclib-view-command",
  "doclib-mailing-command",
  "doclib-screen-capture",
  "doclib-security-command",
  "doclib-insert-text-file",
];

export function registerDocumentCommandState(editor: EditorJS, state?: DocumentCommandState) {
  states.set(editor, state ?? { commands: {} });
}

export function attachDocumentCommandState(editor: EditorJS, data: OutputData): DocumentOutputData {
  return { ...data, documentCommandState: states.get(editor) ?? { commands: {} } };
}

function currentHolder(editor: EditorJS) {
  const index = editor.blocks.getCurrentBlockIndex();
  return index >= 0 ? editor.blocks.getBlockByIndex(index)?.holder ?? null : null;
}

function selectionCommand(mode: string) {
  const normalized = mode.toLowerCase();
  if (normalized.includes("bold")) return "bold";
  if (normalized.includes("italic")) return "italic";
  if (normalized.includes("underline")) return "underline";
  if (normalized.includes("strikethrough")) return "strikeThrough";
  if (normalized.includes("superscript")) return "superscript";
  if (normalized.includes("subscript")) return "subscript";
  if (normalized.includes("alignleft")) return "justifyLeft";
  if (normalized.includes("aligncenter")) return "justifyCenter";
  if (normalized.includes("alignright")) return "justifyRight";
  if (normalized.includes("alignjustify")) return "justifyFull";
  if (normalized === "undo") return "undo";
  if (normalized === "redo") return "redo";
  if (normalized.includes("selectall")) return "selectAll";
  if (normalized.includes("indent")) return "indent";
  if (normalized.includes("outdent")) return "outdent";
  return "";
}

function applyBridgeCommand(editor: EditorJS, command: DocumentCommand) {
  const browserCommand = selectionCommand(command.mode);
  if (browserCommand) {
    document.execCommand(browserCommand);
    return `Đã áp dụng ${command.title}`;
  }
  const root = document.querySelector<HTMLElement>(".codex-editor");
  const holder = currentHolder(editor);
  const normalized = command.mode.toLowerCase();
  if (normalized.includes("zoom")) {
    const number = Number(command.mode.match(/\d+/)?.[0] ?? 100);
    if (root) root.style.zoom = `${Math.min(200, Math.max(50, number))}%`;
    return `Đã đặt tỷ lệ ${Math.min(200, Math.max(50, number))}%`;
  }
  if (normalized.includes("linespacing") && holder) {
    const number = Number(command.mode.match(/\d+(?:\.\d+)?/)?.[0] ?? 1.5);
    holder.style.lineHeight = String(number > 3 ? number / 10 : number);
    return `Đã đặt giãn dòng ${number}`;
  }
  if (normalized.includes("pagebreak")) {
    editor.blocks.insert("originalDelimiter", {});
    return "Đã chèn ngắt trang";
  }
  if (root) root.dataset.documentMode = command.mode;
  return `Đã cập nhật thiết lập ${command.title}`;
}

export async function executeDocumentCommand(editor: EditorJS, command: DocumentCommand) {
  let effect = "";
  const listener = (rawEvent: Event) => {
    const event = rawEvent as CustomEvent<{ command: string }>;
    if (event.detail?.command !== command.id) return;
    event.preventDefault();
    effect = applyBridgeCommand(editor, command);
  };
  commandEvents.forEach((eventName) => window.addEventListener(eventName, listener));
  try {
    const module = await import(`./${command.id}`);
    const CommandClass = module.default;
    const instance = new CommandClass();
    await instance.execute(editor);
    if (!effect) effect = `Đã thực hiện ${command.title}`;
  } catch (reason) {
    if (command.implementation === "direct") {
      effect = applyBridgeCommand(editor, command);
    } else {
      throw reason;
    }
  } finally {
    commandEvents.forEach((eventName) => window.removeEventListener(eventName, listener));
  }
  const state = states.get(editor) ?? { commands: {} };
  const previous = state.commands[command.id];
  state.commands[command.id] = {
    mode: command.mode,
    enabled: !previous?.enabled,
    appliedAt: Date.now(),
  };
  states.set(editor, state);
  return {
    data: attachDocumentCommandState(editor, await editor.save()),
    effect,
  };
}
