import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSparklines implements BlockTool {
  static readonly feature = {
    id: "DocLibSparklines",
    title: "Sparklines",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c654522acbf49ddf"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="15,20 18,12 20,10 8,6 4,11 16,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { values: string };

  static get toolbox() {
    return {
      title: "Sparklines",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c654522acbf49ddf"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="15,20 18,12 20,10 8,6 4,11 16,4"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { values: data.values || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-sparklines");
    const input = document.createElement("input");
    input.type = "text";
    input.value = this.data.values;
    input.placeholder = "12, 18, 9, 24";
    input.addEventListener("input", () => {
      this.data.values = input.value;
    });
    this.wrapper.appendChild(input);

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return { values: input?.value.trim() || "" };
  }
}
