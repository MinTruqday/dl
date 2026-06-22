import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibLabelConfig implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Label Config",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      productNum: data?.productNum || "Avery 5160",
      content: data?.content || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-labelcfg { font-family: sans-serif; padding: 16px; border: 1px dashed #cbd5e1; border-radius: 4px; background: #fafafa; margin: 16px 0; max-width: 400px; display: flex; flex-direction: column; gap: 8px; }
      .doclib-labelcfg-head { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 8px; }
      .doclib-labelcfg-title { font-weight: bold; font-size: 14px; color: #1e293b; }
      .doclib-labelcfg-prod { font-size: 12px; padding: 4px 8px; background: #e2e8f0; border-radius: 4px; color: #475569; outline: none; }
      .doclib-labelcfg-prod:empty:before { content: "DocLib Product"; color: #94a3b8; }
      .doclib-labelcfg-content { min-height: 80px; font-family: "Times New Roman", serif; font-size: 14px; outline: none; background: #fff; border: 1px solid #cbd5e1; padding: 8px; border-radius: 4px; }
      .doclib-labelcfg-content:empty:before { content: "DocLib Label Text"; color: #94a3b8; font-style: italic; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-labelcfg");

    const head = document.createElement("div");
    head.classList.add("doclib-labelcfg-head");
    
    const title = document.createElement("div");
    title.classList.add("doclib-labelcfg-title");
    title.innerText = "Labels";
    head.appendChild(title);

    const prod = document.createElement("div");
    prod.classList.add("doclib-labelcfg-prod");
    prod.innerText = this.data.productNum;
    if (!this.readOnly) {
      prod.contentEditable = "true";
      prod.addEventListener("input", () => { this.data.productNum = prod.innerText; });
    }
    head.appendChild(prod);
    container.appendChild(head);

    const content = document.createElement("div");
    content.classList.add("doclib-labelcfg-content");
    content.innerText = this.data.content;
    if (!this.readOnly) {
      content.contentEditable = "true";
      content.addEventListener("input", () => { this.data.content = content.innerText; });
    }
    container.appendChild(content);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
