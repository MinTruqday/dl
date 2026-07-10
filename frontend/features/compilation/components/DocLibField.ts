import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibField implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string };

  static get toolbox() {
    return {
      title: "DocLib Field",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/></svg>'
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
    this.wrapper.innerHTML = this.data.code;
    this.wrapper.dataset.placeholder = "Insert field code";

    this.wrapper.addEventListener("input", () => {
      this.data.code = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { code: blockContent.innerHTML };
  }
}
