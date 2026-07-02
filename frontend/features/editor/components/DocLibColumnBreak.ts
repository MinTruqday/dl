import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibColumnBreak implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Column Break",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"></path><path d="M18 15l-3 3-3-3"></path><path d="M15 6v12"></path></svg>',
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
      .doclib-colbreak { position: relative; width: 100%; text-align: center; margin: 16px 0; border-top: 1px dotted #94a3b8; }
      .doclib-colbreak::after { content: "DocLib Column Break"; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #f8fafc; padding: 0 12px; color: #94a3b8; font-size: 12px; font-family: sans-serif; font-style: italic; border-radius: 12px; border: 1px dotted #94a3b8; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-colbreak");
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
