import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCaption implements BlockTool {
  static readonly feature = {
    id: "DocLibCaption",
    title: "Caption",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="db197ac4f7591372"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="19,12 7,13 13,8 6,16 15,14 5,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Caption",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="db197ac4f7591372"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="19,12 7,13 13,8 6,16 15,14 5,4"/></svg>',
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
      text.contentEditable = "true";
      text.addEventListener("input", () => {
        this.data.text = text.innerText;
      });
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
