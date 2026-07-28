import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibHeaderBlock implements BlockTool {
  static readonly feature = {
    id: "DocLibHeaderBlock",
    title: "DocLib HeaderBlock",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="141168bc3cbd546e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="7,4 6,5 13,6 20,12 5,5 11,6"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Header Block",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="141168bc3cbd546e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="7,4 6,5 13,6 20,12 5,5 11,6"/></svg>',
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
      text: data?.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-header-block { padding: 16px 24px; border-bottom: 2px solid #cbd5e1; margin-bottom: 32px; color: #475569; font-size: 14px; font-weight: 500; font-style: italic; outline: none; display: flex; align-items: center; justify-content: space-between; position: relative; }
      .doclib-header-block::before { content: "HEADER"; position: absolute; top: -10px; left: 0; font-size: 10px; font-weight: 700; color: #94a3b8; background: #fff; padding: 0 4px; font-style: normal; }
      .doclib-header-block:empty::after { content: "DocLib Text"; color: #cbd5e1; pointer-events: none; font-style: normal; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-header-block");
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
