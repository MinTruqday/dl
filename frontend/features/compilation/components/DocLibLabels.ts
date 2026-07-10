import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibLabels implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { labelType: string };

  static get toolbox() {
    return {
      title: "DocLib Labels",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { labelType: data.labelType || "Avery" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-labels");
    const input = document.createElement("input");
    input.placeholder = "Enter label type";
    input.value = this.data.labelType;
    input.addEventListener("input", (e) => {
      this.data.labelType = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      labelType: input ? input.value : "",
    };
  }
}
