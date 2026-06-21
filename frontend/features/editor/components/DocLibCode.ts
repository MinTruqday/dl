import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCode implements BlockTool {
  private api: API;
  private data: { code: string };
  private wrapper: HTMLElement | null = null;
  private textarea: HTMLTextAreaElement | null = null;
  private _CSS: {
    block: string;
    wrapper: string;
    textarea: string;
  };

  static get toolbox() {
    return {
      title: "DocLib Code",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
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
      code: data.code || "",
    };

    this._CSS = {
      block: this.api.styles.block,
      wrapper: "cdx-code",
      textarea: "cdx-code__textarea",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this._CSS.wrapper);
    this.wrapper.classList.add(this._CSS.block);

    this.textarea = document.createElement("textarea");
    this.textarea.classList.add(this._CSS.textarea);
    this.textarea.value = this.data.code;
    this.textarea.placeholder = "DocLib Code";

    this.wrapper.style.position = "relative";
    this.textarea.style.minHeight = "150px";
    this.textarea.style.width = "100%";
    this.textarea.style.padding = "10px";
    this.textarea.style.border = "1px solid #eaeaea";
    this.textarea.style.borderRadius = "3px";
    this.textarea.style.resize = "vertical";
    this.textarea.style.fontFamily =
      "Menlo, Monaco, Consolas, Courier New, monospace";
    this.textarea.style.fontSize = "14px";
    this.textarea.style.lineHeight = "1.6";
    this.textarea.style.backgroundColor = "#f8f9fa";
    this.textarea.style.outline = "none";

    this.wrapper.appendChild(this.textarea);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      code: this.textarea ? this.textarea.value : "",
    };
  }

  static get sanitize() {
    return {
      code: true,
    };
  }
}
