import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibLatex implements BlockTool {
  static readonly feature = {
    id: "DocLibLatex",
    title: "DocLib Latex",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b81e01f3aab351a8"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="18,17 5,9 4,13 17,19 19,20 19,8"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { code: string };
  private wrapper: HTMLElement | null = null;
  private editor: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib LaTeX",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b81e01f3aab351a8"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="18,17 5,9 4,13 17,19 19,20 19,8"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      code: data.code || data.math || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    this.wrapper.style.padding = "10px 0";

    const label = document.createElement("div");
    label.style.fontSize = "10px";
    label.style.color = "#999";
    label.style.textTransform = "uppercase";
    label.style.marginBottom = "5px";
    label.style.letterSpacing = "1px";
    label.innerText = "DocLib LaTeX";

    this.editor = document.createElement("div");
    this.editor.classList.add(this.api.styles.input);
    this.editor.contentEditable = "true";
    this.editor.textContent = this.data.code;
    this.editor.dataset.placeholder = "DocLib Code";

    this.editor.style.fontFamily = "monospace";
    this.editor.style.minHeight = "60px";
    this.editor.style.backgroundColor = "#f4f4f5";
    this.editor.style.padding = "12px";
    this.editor.style.borderRadius = "6px";
    this.editor.style.border = "1px solid #e4e4e7";
    this.editor.style.lineHeight = "1.6";
    this.editor.style.wordWrap = "break-word";

    this.wrapper.appendChild(label);
    this.wrapper.appendChild(this.editor);

    this.editor.addEventListener("input", () => {
      if (this.editor) {
        this.data.code = this.editor.textContent || "";
      }
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      code: this.editor ? this.editor.textContent || "" : this.data.code,
      math: this.editor ? this.editor.textContent || "" : this.data.code,
    };
  }

  static get sanitize() {
    return {
      code: true,
      math: true,
    };
  }
}
