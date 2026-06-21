import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFooterBlock implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Footer Block",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h16"/><path d="M4 22v-4h16v4H4z"/><path d="M12 18V2"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-footer-block { padding: 16px 24px; border-top: 2px solid #cbd5e1; margin-top: 32px; color: #475569; font-size: 14px; font-weight: 500; font-style: italic; outline: none; display: flex; align-items: center; justify-content: space-between; position: relative; }
      .doclib-footer-block::after { content: "FOOTER"; position: absolute; bottom: -10px; left: 0; font-size: 10px; font-weight: 700; color: #94a3b8; background: #fff; padding: 0 4px; font-style: normal; }
      .doclib-footer-block:empty::before { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; font-style: normal; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-footer-block");
    container.innerText = this.data.text;

    if (!this.readOnly) {
      container.contentEditable = "true";
      container.addEventListener("input", () => {
        this.data.text = container.innerText;
      });
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
    };
  }
}
