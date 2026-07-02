import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTextWrappingBreak implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Text Wrapping Break",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v-6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2"></path><polyline points="14 12 10 16 14 20"></polyline></svg>',
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
      .doclib-wrapbreak { position: relative; width: 100%; text-align: left; margin: 16px 0; border-top: 1px dashed #cbd5e1; }
      .doclib-wrapbreak::after { content: "DocLib Text Wrapping Break"; position: absolute; top: -10px; left: 24px; background: #f8fafc; padding: 0 12px; color: #cbd5e1; font-size: 11px; font-family: sans-serif; text-transform: uppercase; border-radius: 12px; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-wrapbreak");
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
