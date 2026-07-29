import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDiffViewer implements BlockTool {
  static readonly feature = {
    id: "DocLibDiffViewer",
    title: "DocLib Diff Viewer",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f75688e7b6039bd1"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="13,5 4,14 16,7 6,9 16,5 7,12"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { oldCode: string; newCode: string; language: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Diff Viewer",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f75688e7b6039bd1"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="13,5 4,14 16,7 6,9 16,5 7,12"/></svg>',
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
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      oldCode: data?.oldCode || "",
      newCode: data?.newCode || "",
      language: data?.language || "",
    };
  }

  private computeDiff(
    oldText: string,
    newText: string,
  ): { type: "del" | "add" | "eq"; text: string }[] {
    const oldLines = oldText.split("\n");
    const newLines = newText.split("\n");
    const result: { type: "del" | "add" | "eq"; text: string }[] = [];
    const maxLen = Math.max(oldLines.length, newLines.length);
    for (let i = 0; i < maxLen; i++) {
      const o = oldLines[i];
      const n = newLines[i];
      if (o === undefined) {
        result.push({ type: "add", text: n });
      } else if (n === undefined) {
        result.push({ type: "del", text: o });
      } else if (o === n) {
        result.push({ type: "eq", text: o });
      } else {
        result.push({ type: "del", text: o });
        result.push({ type: "add", text: n });
      }
    }
    return result;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-diff-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-diff-styles";
      style.innerHTML = `
        .doclib-diff-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 12px 0; }
        .doclib-diff-header { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; }
        .doclib-diff-lang { font-size: 12px; font-weight: 600; color: #64748b; }
        .doclib-diff-edit-area { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid #e2e8f0; }
        .doclib-diff-col { display: flex; flex-direction: column; }
        .doclib-diff-col:first-child { border-right: 1px solid #e2e8f0; }
        .doclib-diff-col-label { padding: 6px 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .doclib-diff-col:first-child .doclib-diff-col-label { background: #fef2f2; color: #ef4444; }
        .doclib-diff-col:last-child .doclib-diff-col-label { background: #f0fdf4; color: #22c55e; }
        .doclib-diff-textarea { width: 100%; border: none; outline: none; padding: 12px; font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.6; resize: vertical; min-height: 140px; background: transparent; box-sizing: border-box; }
        .doclib-diff-output { background: #0f172a; padding: 16px; overflow-x: auto; }
        .doclib-diff-line { font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.6; padding: 1px 6px; white-space: pre; }
        .doclib-diff-line.del { background: rgba(239,68,68,0.15); color: #fca5a5; }
        .doclib-diff-line.del::before { content: "- "; color: #ef4444; }
        .doclib-diff-line.add { background: rgba(34,197,94,0.12); color: #86efac; }
        .doclib-diff-line.add::before { content: "+ "; color: #22c55e; }
        .doclib-diff-line.eq { color: #94a3b8; }
        .doclib-diff-line.eq::before { content: "  "; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private renderDiff(output: HTMLElement) {
    output.innerHTML = "";
    const diff = this.computeDiff(this.data.oldCode, this.data.newCode);
    diff.forEach(({ type, text }) => {
      const line = document.createElement("div");
      line.classList.add("doclib-diff-line", type);
      line.innerText = text;
      output.appendChild(line);
    });
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-diff-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-diff-header");

    const langLabel = document.createElement("span");
    langLabel.classList.add("doclib-diff-lang");
    langLabel.innerText = `Diff — ${this.data.language}`;
    header.appendChild(langLabel);

    if (!this.readOnly) {
      const langs = [
        "javascript",
        "typescript",
        "python",
        "go",
        "java",
        "rust",
        "css",
        "html",
        "sql",
        "bash",
      ];
      const sel = document.createElement("select");
      sel.style.cssText =
        "font-size:12px;border:1px solid #e2e8f0;border-radius:4px;padding:4px 8px;outline:none;background:#fff;";
      langs.forEach((l) => {
        const opt = document.createElement("option");
        opt.value = l;
        opt.innerText = l;
        if (l === this.data.language) opt.selected = true;
        sel.appendChild(opt);
      });
      sel.addEventListener("change", () => {
        this.data.language = sel.value;
        langLabel.innerText = `Diff — ${this.data.language}`;
      });
      header.appendChild(sel);
    }

    this.wrapper.appendChild(header);

    const output = document.createElement("div");
    output.classList.add("doclib-diff-output");

    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-diff-edit-area");

      const oldCol = document.createElement("div");
      oldCol.classList.add("doclib-diff-col");
      const oldLabel = document.createElement("div");
      oldLabel.classList.add("doclib-diff-col-label");
      oldLabel.innerText = "Old version";
      const oldTA = document.createElement("textarea");
      oldTA.classList.add("doclib-diff-textarea");
      oldTA.value = this.data.oldCode;
      let timeout: ReturnType<typeof setTimeout>;
      oldTA.addEventListener("input", () => {
        this.data.oldCode = oldTA.value;
        clearTimeout(timeout);
        timeout = setTimeout(() => this.renderDiff(output), 400);
      });
      oldCol.appendChild(oldLabel);
      oldCol.appendChild(oldTA);

      const newCol = document.createElement("div");
      newCol.classList.add("doclib-diff-col");
      const newLabel = document.createElement("div");
      newLabel.classList.add("doclib-diff-col-label");
      newLabel.innerText = "New version";
      const newTA = document.createElement("textarea");
      newTA.classList.add("doclib-diff-textarea");
      newTA.value = this.data.newCode;
      newTA.addEventListener("input", () => {
        this.data.newCode = newTA.value;
        clearTimeout(timeout);
        timeout = setTimeout(() => this.renderDiff(output), 400);
      });
      newCol.appendChild(newLabel);
      newCol.appendChild(newTA);

      editArea.appendChild(oldCol);
      editArea.appendChild(newCol);
      this.wrapper.appendChild(editArea);
    }

    this.wrapper.appendChild(output);
    this.renderDiff(output);
  }

  save() {
    return this.data;
  }
}
