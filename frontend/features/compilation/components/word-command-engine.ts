import type EditorJS from "@editorjs/editorjs";
import type { OutputData } from "@editorjs/editorjs";

export type WordCommandCategory =
  | "format"
  | "insert"
  | "layout"
  | "table"
  | "review"
  | "reference"
  | "mailing"
  | "view"
  | "media"
  | "security"
  | "automation"
  | "ai";

export interface WordCommand {
  id: string;
  title: string;
  category: WordCommandCategory;
  mode: string;
  requiresSelection: boolean;
  execute(editor: EditorJS): void | Promise<void>;
}

export interface WordCommandRecord {
  mode: string;
  category: WordCommandCategory;
  appliedAt: number;
  enabled: boolean;
}

export interface WordCommandSettings {
  commands: Record<string, WordCommandRecord>;
}

export interface WordOutputData extends OutputData {
  wordSettings?: WordCommandSettings;
}

const settingsByEditor = new WeakMap<EditorJS, WordCommandSettings>();

export function registerWordSettings(
  editor: EditorJS,
  settings?: WordCommandSettings,
) {
  settingsByEditor.set(editor, settings || { commands: {} });
}

export function getWordSettings(editor: EditorJS) {
  let settings = settingsByEditor.get(editor);
  if (!settings) {
    settings = { commands: {} };
    settingsByEditor.set(editor, settings);
  }
  return settings;
}

export function attachWordSettings(
  editor: EditorJS,
  data: OutputData,
): WordOutputData {
  return {
    ...data,
    wordSettings: getWordSettings(editor),
  };
}

export async function executeWordCommand(
  editor: EditorJS,
  command: WordCommand,
): Promise<WordOutputData> {
  await command.execute(editor);
  const settings = getWordSettings(editor);
  const previous = settings.commands[command.id];
  settings.commands[command.id] = {
    mode: command.mode,
    category: command.category,
    appliedAt: Date.now(),
    enabled: !previous?.enabled,
  };
  return attachWordSettings(editor, await editor.save());
}
