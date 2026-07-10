import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibRestrictEditing implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { content: string };

  static get toolbox() {
    return {
      title: "DocLib Restrict Editing",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { content: data.content || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-restrict");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.content;
    this.wrapper.dataset.placeholder = "Restricted content";

    this.wrapper.addEventListener("input", () => {
      this.data.content = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { content: blockContent.innerHTML };
  }
}
