import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCaption implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Caption",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      label: data?.label || "Figure",
      number: data?.number || "1",
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-caption { font-family: "Times New Roman", serif; font-size: 14px; color: #475569; text-align: center; margin: 8px 0 16px 0; font-style: italic; }
      .doclib-caption-label { font-weight: bold; color: #1e293b; outline: none; }
      .doclib-caption-text { outline: none; }
      .doclib-caption-text:empty:before { content: "DocLib Enter caption text"; color: #94a3b8; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-caption");

    const label = document.createElement("span");
    label.classList.add("doclib-caption-label");
    label.innerText = `${this.data.label} ${this.data.number}: `;
    
    const text = document.createElement("span");
    text.classList.add("doclib-caption-text");
    text.innerText = this.data.text;

    if (!this.readOnly) {
      // In a real scenario, you'd have a config menu for label/number. For now, editable.
      text.contentEditable = "true";
      text.addEventListener("input", () => { this.data.text = text.innerText; });
    }

    container.appendChild(label);
    container.appendChild(text);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
