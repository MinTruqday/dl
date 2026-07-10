import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTabStops implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { stops: string };

  static get toolbox() {
    return {
      title: "DocLib Tab Stops",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16M4 6h16M4 18h16"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { stops: data.stops || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-tab-stops");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.stops;
    this.wrapper.dataset.placeholder = "Set tab stops";

    this.wrapper.addEventListener("input", () => {
      this.data.stops = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { stops: blockContent.innerHTML };
  }
}
