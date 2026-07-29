import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTitle implements BlockTool {
  static readonly feature = {
    id: "DocLibTitle",
    title: "Title",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f25a10d84d0530b7"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="8,9 20,16 13,9 18,17 4,10 16,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };

  static get toolbox() {
    return {
      title: "Title",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f25a10d84d0530b7"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="8,9 20,16 13,9 18,17 4,10 16,19"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return false;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      text: data.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("h1");
    this.wrapper.classList.add(this.api.styles.block);
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.text;
    this.wrapper.dataset.placeholder = "DocLib Title";

    this.wrapper.style.fontSize = "2.25rem";
    this.wrapper.style.fontWeight = "700";
    this.wrapper.style.lineHeight = "1.2";
    this.wrapper.style.margin = "24px 0 16px 0";
    this.wrapper.style.outline = "none";

    this.wrapper.addEventListener("input", () => {
      this.data.text = this.wrapper!.innerHTML;
    });

    this.wrapper.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.api.blocks.insert();
        this.api.caret.setToBlock(this.api.blocks.getCurrentBlockIndex() + 1);
      }
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      text: this.wrapper ? this.wrapper.innerHTML : this.data.text,
    };
  }

  static get sanitize() {
    return {
      text: { br: true, b: true, i: true, a: true, span: true },
    };
  }
}
