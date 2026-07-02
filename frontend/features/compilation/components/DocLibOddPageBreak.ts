import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibOddPageBreak implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Odd Page Break",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="12" x2="21" y2="12"></line><circle cx="12" cy="6" r="2"></circle></svg>',
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
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-oddbreak { position: relative; width: 100%; margin: 24px 0; border-top: 2px double #cbd5e1; }
      .doclib-oddbreak::after { content: "DocLib Section Break (Odd Page)"; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #f8fafc; padding: 0 12px; color: #64748b; font-size: 11px; font-family: sans-serif; letter-spacing: 1px; border-radius: 4px; border: 1px solid #cbd5e1; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-oddbreak");
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
