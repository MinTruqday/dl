import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibParagraphBorders implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { content: string };

  static get toolbox() {
    return {
      title: "DocLib Paragraph Borders",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { content: data.content || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-doc-lib-paragraph-borders");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.content;
    this.wrapper.dataset.placeholder = "Doc Lib Paragraph Borders";

    this.wrapper.addEventListener("input", (e: any) => {
      this.data.content = e.target.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      content: blockContent.innerHTML
    };
  }
}
