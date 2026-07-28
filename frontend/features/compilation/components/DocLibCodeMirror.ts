import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCodeMirror implements BlockTool {
  static readonly feature = {
    id: "DocLibCodeMirror",
    title: "DocLib CodeMirror",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8a9968b687612ac5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="6,4 6,16 20,16 12,14 7,8 13,17"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string; language: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib CodeMirror",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8a9968b687612ac5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="6,4 6,16 20,16 12,14 7,8 13,17"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      code: data.code || "",
      language: data.language || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-codemirror-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-codemirror-styles";
      style.innerHTML = `
            .doclib-cm-wrapper { background: #1e293b; border-radius: 8px; padding: 16px; margin: 16px 0; display: flex; flex-direction: column; gap: 8px; }
            .doclib-cm-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 8px; }
            .doclib-cm-dots { display: flex; gap: 6px; }
            .doclib-cm-dot { width: 12px; height: 12px; border-radius: 50%; }
            .doclib-cm-lang { color: #94a3b8; font-size: 12px; font-family: monospace; text-transform: uppercase; outline: none; }
            .doclib-cm-lang:empty::before { content: 'LANGUAGE'; }
            .doclib-cm-editor { color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 14px; line-height: 1.5; outline: none; min-height: 100px; white-space: pre-wrap; word-break: break-all; }
            .doclib-cm-editor:empty::before { content: 'Enter source code here'; color: #475569; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-cm-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-cm-header");

    const dots = document.createElement("div");
    dots.classList.add("doclib-cm-dots");
    ["#ef4444", "#f59e0b", "#10b981"].forEach((c) => {
      const dot = document.createElement("div");
      dot.classList.add("doclib-cm-dot");
      dot.style.backgroundColor = c;
      dots.appendChild(dot);
    });

    const lang = document.createElement("div");
    lang.classList.add("doclib-cm-lang");
    lang.contentEditable = !this.readOnly ? "true" : "false";
    lang.innerHTML = this.data.language;
    lang.addEventListener("input", () => (this.data.language = lang.innerHTML));

    header.appendChild(dots);
    header.appendChild(lang);

    const editor = document.createElement("div");
    editor.classList.add("doclib-cm-editor");
    editor.contentEditable = !this.readOnly ? "true" : "false";
    editor.innerHTML = this.data.code;
    editor.addEventListener("input", () => (this.data.code = editor.innerHTML));

    editor.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        document.execCommand("insertText", false, "  ");
      }
    });

    container.appendChild(header);
    container.appendChild(editor);
    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
