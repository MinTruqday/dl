import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibParagraph implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Text",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" y1="6" x2="3" y2="6"></line><line x1="21" y1="12" x2="9" y2="12"></line><line x1="21" y1="18" x2="7" y2="18"></line></svg>',
    };
  }
  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return true;
  }
  static get sanitize() {
    return {
      text: {
        br: true,
        b: true,
        i: true,
        a: true,
        span: true,
        mark: true,
        code: true,
        u: true,
        s: true,
        sup: true,
        sub: true,
      },
    };
  }
  static get conversionConfig() {
    return { export: "text", import: "text" };
  }

  static get pasteConfig() {
    return { tags: ["P"] };
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
    this.data = { text: data?.text || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-paragraph");

    if (!this.readOnly) {
      this.wrapper.contentEditable = "true";
      this.wrapper.dataset.placeholder = 'DocLib Input"/" for commands';
    }

    this.wrapper.innerHTML = this.data.text;

    if (!document.getElementById("doclib-paragraph-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-paragraph-styles";
      style.innerHTML = `
            .doclib-paragraph { line-height: 1.6em; outline: none; padding: 4px 0; margin-bottom: 8px; }
            .doclib-paragraph[data-placeholder]:empty::before { content: attr(data-placeholder); color: #94a3b8; pointer-events: none; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.addEventListener("input", () => {
      if (this.wrapper) this.data.text = this.wrapper.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { text: blockContent.innerHTML };
  }

  merge(data: { text: string }) {
    if (!this.wrapper) return;
    this.data.text += data.text || "";
    this.wrapper.innerHTML = this.data.text;
  }

  onPaste(event: any) {
    const data = {
      text: event.detail.data.innerHTML,
    };
    this.data = data;
    if (this.wrapper) {
      this.wrapper.innerHTML = this.data.text;
    }
  }
}
