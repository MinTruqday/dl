import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAccessibilityChecker implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { result: string };

  static get toolbox() {
    return {
      title: "DocLib Accessibility Checker",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="16" cy="4" r="1"/><path d="m18 19 1-7-6 1"/><path d="m5 8 3-3 5.5 3-2.36 3.5"/><path d="M4.24 14.5a5 5 0 0 0 6.88 6"/><path d="M13.76 17.5a5 5 0 0 0-6.88-6"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { result: data.result || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-accessibility");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.result;
    this.wrapper.dataset.placeholder = "Accessibility status";

    this.wrapper.addEventListener("input", () => {
      this.data.result = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { result: blockContent.innerHTML };
  }
}
