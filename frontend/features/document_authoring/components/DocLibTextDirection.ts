import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTextDirection implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Text Direction",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="12 4 12 20"/><polyline points="8 8 12 4 16 8"/><line x1="12" y1="20" x2="16" y2="16"/></svg>',
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
      .doclib-vertical { writing-mode: vertical-rl; text-orientation: mixed; padding: 24px; min-height: 200px; border: 1px dashed #cbd5e1; border-radius: 8px; font-size: 16px; line-height: 2; margin: 16px 0; background: #fff; outline: none; display: flex; align-items: flex-start; justify-content: flex-start; }
      .doclib-vertical[contenteditable="true"]:focus { border-color: #3b82f6; }
      .doclib-vertical:empty::before { content: "DocLib Text"; color: #94a3b8; pointer-events: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-vertical");
    container.innerText = this.data.text;

    if (!this.readOnly) {
      container.contentEditable = "true";
      container.addEventListener("input", () => {
        this.data.text = container.innerText;
      });
    } else {
      container.style.border = "none";
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
