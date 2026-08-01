import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibCode implements BlockTool {
  static readonly feature = {
    id: "DocLibCode",
    title: "DocLib Code",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="cb14d0970ace5475"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,7 8,19 14,6 20,19 13,5 8,12"/></svg>',
    product: "doclib",
  } as const;

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
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="cb14d0970ace5475"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,7 8,19 14,6 20,19 13,5 8,12"/></svg>',
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
    this.textarea.style.border = "1px solid hsl(var(--border))";
    this.textarea.style.borderRadius = "3px";
    this.textarea.style.resize = "vertical";
    this.textarea.style.fontFamily =
      "Menlo, Monaco, Consolas, Courier New, monospace";
    this.textarea.style.fontSize = "14px";
    this.textarea.style.lineHeight = "1.6";
    this.textarea.style.backgroundColor = "hsl(var(--surface-quiet))";
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
