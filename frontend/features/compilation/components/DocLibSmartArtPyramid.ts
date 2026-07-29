import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtPyramid implements BlockTool {
  static readonly feature = {
    id: "DocLibSmartArtPyramid",
    title: "Smart Art Pyramid",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="713cafb171db5eb5"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="15,13 9,11 15,19 13,15 13,14 4,14"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Smart Art Pyramid",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="713cafb171db5eb5"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="15,13 9,11 15,19 13,15 13,14 4,14"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      top: data?.top || "DocLib Top",
      middle: data?.middle || "DocLib Middle",
      bottom: data?.bottom || "DocLib Bottom",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-pyramid { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; margin: 16px 0; max-width: 400px; height: 300px; font-family: sans-serif; position: relative; margin-left: auto; margin-right: auto; }
      .doclib-pyr-level { display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; color: #fff; text-align: center; outline: none; transition: 0.3s; }
      .doclib-pyr-level:empty:before { content: attr(data-placeholder); color: rgba(255,255,255,0.7); }
      .doclib-pyr-top { width: 100px; height: 100px; background: #ef4444; clip-path: polygon(50% 0%, 0% 100%, 100% 100%); margin-bottom: -1px; display: flex; align-items: flex-end; padding-bottom: 12px; z-index: 3; }
      .doclib-pyr-mid { width: 220px; height: 80px; background: #f59e0b; clip-path: polygon(25% 0%, 75% 0%, 100% 100%, 0% 100%); margin-bottom: -1px; z-index: 2; }
      .doclib-pyr-bot { width: 340px; height: 80px; background: #10b981; clip-path: polygon(18% 0%, 82% 0%, 100% 100%, 0% 100%); z-index: 1; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-pyramid");

    const levels = [
      { key: "top", cls: "doclib-pyr-top", placeholder: "DocLib Top" },
      { key: "middle", cls: "doclib-pyr-mid", placeholder: "DocLib Middle" },
      { key: "bottom", cls: "doclib-pyr-bot", placeholder: "DocLib Bottom" },
    ];

    levels.forEach((lvl) => {
      const el = document.createElement("div");
      el.classList.add("doclib-pyr-level", lvl.cls);
      el.dataset.placeholder = lvl.placeholder;

      const span = document.createElement("span");
      span.innerText = this.data[lvl.key];
      if (!this.readOnly) {
        span.contentEditable = "true";
        span.addEventListener("input", () => {
          this.data[lvl.key] = span.innerText;
        });
      }
      el.appendChild(span);
      container.appendChild(el);
    });

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
