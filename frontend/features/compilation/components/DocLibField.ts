import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibField implements BlockTool {
  static readonly feature = {
    id: "DocLibField",
    title: "DocLib Field",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e08d46bf9cc55e08"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="7,9 6,8 7,14 13,12 8,11 6,18"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string };

  static get toolbox() {
    return {
      title: "DocLib Field",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e08d46bf9cc55e08"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="7,9 6,8 7,14 13,12 8,11 6,18"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { code: data.code || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-field");
    this.wrapper.contentEditable = "true";
    this.wrapper.textContent = this.data.code;
    this.wrapper.dataset.placeholder = "Insert field code";

    this.wrapper.addEventListener("input", () => {
      this.data.code = this.wrapper!.textContent || "";
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { code: blockContent.textContent || "" };
  }
}
