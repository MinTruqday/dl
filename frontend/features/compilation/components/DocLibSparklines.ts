import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSparklines implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { values: string };

  static get toolbox() {
    return {
      title: "DocLib Sparklines",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18M7 14l5-5 4 4 5-5"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { values: data.values || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-sparklines");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.values;
    this.wrapper.dataset.placeholder = "Sparkline data";

    this.wrapper.addEventListener("input", () => {
      this.data.values = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { values: blockContent.innerHTML };
  }
}
