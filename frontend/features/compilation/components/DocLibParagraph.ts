import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibParagraph implements BlockTool {
  static readonly feature = {
    id: "DocLibParagraph",
    title: "Paragraph",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="74148f2156b4ed92"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="18,7 11,20 5,14 20,14 17,5 14,18"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "Paragraph",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="74148f2156b4ed92"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="18,7 11,20 5,14 20,14 17,5 14,18"/></svg>',
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
