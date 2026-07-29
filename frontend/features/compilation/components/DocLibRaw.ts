import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibRaw implements BlockTool {
  static readonly feature = {
    id: "DocLibRaw",
    title: "DocLib Raw",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="da44512d08a44d45"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="18,4 17,15 12,15 13,5 16,15 5,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { html: string };
  private wrapper: HTMLElement | null = null;
  private textarea: HTMLTextAreaElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib Raw",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="da44512d08a44d45"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="18,4 17,15 12,15 13,5 16,15 5,19"/></svg>',
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
      html: data.html || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    this.textarea = document.createElement("textarea");
    this.textarea.classList.add(this.api.styles.input);
    this.textarea.value = this.data.html;
    this.textarea.placeholder = "DocLib Code";

    this.textarea.style.minHeight = "150px";
    this.textarea.style.fontFamily = "monospace";
    this.textarea.style.backgroundColor = "#f8f9fa";
    this.textarea.style.resize = "none";
    this.textarea.style.overflow = "hidden";
    this.textarea.style.padding = "10px";

    this.textarea.addEventListener("input", () => {
      if (this.textarea) {
        this.textarea.style.height = "auto";
        this.textarea.style.height = this.textarea.scrollHeight + "px";
      }
    });

    this.wrapper.appendChild(this.textarea);

    setTimeout(() => {
      if (this.textarea) {
        this.textarea.style.height = "auto";
        this.textarea.style.height = this.textarea.scrollHeight + "px";
      }
    }, 100);

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      html: this.textarea ? this.textarea.value : "",
    };
  }

  static get sanitize() {
    return { html: true };
  }
}
