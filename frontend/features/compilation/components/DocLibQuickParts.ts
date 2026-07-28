import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibQuickParts implements BlockTool {
  static readonly feature = {
    id: "DocLibQuickParts",
    title: "DocLib QuickParts",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="70cc678281f933ea"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,4 5,15 14,15 4,17 12,19 15,4"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Quick Parts",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="70cc678281f933ea"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,4 5,15 14,15 4,17 12,19 15,4"/></svg>',
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
      content: data?.content || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-quickp { font-family: sans-serif; padding: 16px; border: 1px dashed #cbd5e1; border-radius: 8px; background: #f8fafc; margin: 16px 0; position: relative; }
      .doclib-quickp::before { content: "DocLib Quick Part"; position: absolute; top: -10px; left: 16px; background: #fff; padding: 0 8px; color: #64748b; font-size: 11px; font-weight: bold; border-radius: 12px; border: 1px solid #cbd5e1; text-transform: uppercase; }
      .doclib-quickp-text { outline: none; min-height: 50px; font-size: 14px; color: #1e293b; line-height: 1.5; }
      .doclib-quickp-text:empty:before { content: "DocLib Insert reusable text here"; color: #94a3b8; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-quickp");

    const text = document.createElement("div");
    text.classList.add("doclib-quickp-text");
    text.innerText = this.data.content;

    if (!this.readOnly) {
      text.contentEditable = "true";
      text.addEventListener("input", () => {
        this.data.content = text.innerText;
      });
    }

    container.appendChild(text);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
