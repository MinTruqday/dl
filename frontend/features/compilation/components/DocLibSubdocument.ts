import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSubdocument implements BlockTool {
  static readonly feature = {
    id: "DocLibSubdocument",
    title: "DocLib Subdocument",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="16d29829b7363666"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,10 20,11 17,7 7,4 6,8 12,5"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Subdocument",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="16d29829b7363666"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,10 20,11 17,7 7,4 6,8 12,5"/></svg>',
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
      filename: data?.filename || "",
      status: data?.status || "Linked",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-subdoc { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid #94a3b8; border-radius: 4px; background: #fff; margin: 8px 0; font-family: sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
      .doclib-subdoc-info { display: flex; align-items: center; gap: 12px; flex: 1; }
      .doclib-subdoc-icon { color: #3b82f6; width: 24px; height: 24px; }
      .doclib-subdoc-name { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; flex: 1; }
      .doclib-subdoc-name:empty:before { content: "DocLib Subdocument Link"; color: #94a3b8; font-weight: normal; }
      .doclib-subdoc-status { font-size: 11px; padding: 4px 8px; border-radius: 12px; font-weight: bold; text-transform: uppercase; }
      .doclib-subdoc-status.linked { background: #dcfce7; color: #16a34a; }
      .doclib-subdoc-status.locked { background: #fee2e2; color: #dc2626; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-subdoc");

    const info = document.createElement("div");
    info.classList.add("doclib-subdoc-info");

    info.innerHTML += `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="16d29829b7363666"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,10 20,11 17,7 7,4 6,8 12,5"/></svg>`;

    const name = document.createElement("div");
    name.classList.add("doclib-subdoc-name");
    name.innerText = this.data.filename;

    if (!this.readOnly) {
      name.contentEditable = "true";
      name.addEventListener("input", () => {
        this.data.filename = name.innerText;
      });
    }
    info.appendChild(name);
    container.appendChild(info);

    const status = document.createElement("div");
    status.className = `doclib-subdoc-status ${this.data.status === "Linked" ? "linked" : "locked"}`;
    status.innerText = this.data.status;

    if (!this.readOnly) {
      status.style.cursor = "pointer";
      status.addEventListener("click", () => {
        this.data.status = this.data.status === "Linked" ? "Locked" : "Linked";
        status.className = `doclib-subdoc-status ${this.data.status === "Linked" ? "linked" : "locked"}`;
        status.innerText = this.data.status;
      });
    }
    container.appendChild(status);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
