import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibBreakLine implements BlockTool {
  static readonly feature = {
    id: "DocLibBreakLine",
    title: "DocLib Break Line",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c3660dc53f17d7d7"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,4 17,14 16,10 15,15 14,11 5,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: any;

  static get toolbox() {
    return {
      title: "DocLib Break Line",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c3660dc53f17d7d7"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,4 17,14 16,10 15,15 14,11 5,14"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-breakline-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-breakline-styles";
      style.innerHTML = `
            .doclib-breakline { margin: 24px 0; border: none; border-top: 1px solid #e2e8f0; }
        `;
      document.head.appendChild(style);
    }

    const hr = document.createElement("hr");
    hr.classList.add("doclib-breakline");
    this.wrapper.appendChild(hr);

    return this.wrapper;
  }

  save() {
    return {};
  }
}
