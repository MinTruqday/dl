import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDigitalSignatureLine implements BlockTool {
  static readonly feature = {
    id: "DocLibDigitalSignatureLine",
    title: "Digital Signature Line",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e29a3ffd20b6ce9f"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="9,5 16,19 19,16 6,10 7,18 7,15"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Digital Signature Line",
      icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e29a3ffd20b6ce9f"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="9,5 16,19 19,16 6,10 7,18 7,15"/></svg>`,
    };
  }

  private api: API;
  private data: BlockToolData;
  private wrapper: HTMLElement;

  constructor({ api, data }: { api: API; data: BlockToolData }) {
    this.api = api;
    this.data = data || { content: "" };
    this.wrapper = document.createElement("div");
  }

  render() {
    this.wrapper.classList.add("ce-block");
    const input = document.createElement("input");
    input.classList.add("ce-paragraph", "cdx-block");
    input.value = this.data?.content || "";
    input.placeholder = "DocLib Digital Signature Line";
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input") as HTMLInputElement;
    return {
      content: input ? input.value : "",
    };
  }
}
