import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtMatrix implements BlockTool {
  static readonly feature = {
    id: "DocLibSmartArtMatrix",
    title: "Smart Art Matrix",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="271fcbdf2c03de1f"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,18 20,6 14,7 5,18 4,10 20,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Smart Art Matrix",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="271fcbdf2c03de1f"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,18 20,6 14,7 5,18 4,10 20,4"/></svg>',
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
      tl: data?.tl || "DocLib Q1",
      tr: data?.tr || "DocLib Q2",
      bl: data?.bl || "DocLib Q3",
      br: data?.br || "DocLib Q4",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-matrix { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; max-width: 400px; margin: 16px auto; font-family: sans-serif; position: relative; }
      .doclib-matrix::before { content: ""; position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: #fff; transform: translateY(-50%); z-index: 1; }
      .doclib-matrix::after { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; width: 4px; background: #fff; transform: translateX(-50%); z-index: 1; }
      .doclib-matrix-cell { aspect-ratio: 1/1; display: flex; align-items: center; justify-content: center; text-align: center; padding: 16px; font-weight: bold; font-size: 18px; color: #fff; outline: none; }
      .doclib-matrix-cell:empty:before { content: "DocLib Cell"; color: rgba(255,255,255,0.7); font-weight: normal; }
      .doclib-matrix-tl { background: #3b82f6; border-radius: 16px 0 0 0; }
      .doclib-matrix-tr { background: #10b981; border-radius: 0 16px 0 0; }
      .doclib-matrix-bl { background: #f59e0b; border-radius: 0 0 0 16px; }
      .doclib-matrix-br { background: #ef4444; border-radius: 0 0 16px 0; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-matrix");

    const cells = [
      { key: "tl", cls: "doclib-matrix-tl" },
      { key: "tr", cls: "doclib-matrix-tr" },
      { key: "bl", cls: "doclib-matrix-bl" },
      { key: "br", cls: "doclib-matrix-br" },
    ];

    cells.forEach((c) => {
      const el = document.createElement("div");
      el.classList.add("doclib-matrix-cell", c.cls);
      el.innerText = this.data[c.key];
      if (!this.readOnly) {
        el.contentEditable = "true";
        el.addEventListener("input", () => {
          this.data[c.key] = el.innerText;
        });
      }
      container.appendChild(el);
    });

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
