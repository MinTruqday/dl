import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMasterDocument implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Master Document",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4"></path><path d="M14 2v4a2 2 0 0 0 2 2h4"></path><rect x="2" y="11" width="10" height="7" rx="1"></rect></svg>',
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
      title: data?.title || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-master { padding: 24px; border: 2px solid #1e293b; border-radius: 8px; background: #f8fafc; margin: 16px 0; font-family: sans-serif; position: relative; }
      .doclib-master::before { content: "DocLib Master Document Container"; position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #1e293b; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; letter-spacing: 1px; }
      .doclib-master-title { font-size: 24px; font-weight: bold; color: #0f172a; text-align: center; outline: none; margin-bottom: 16px; }
      .doclib-master-title:empty:before { content: "DocLib Enter Master Title"; color: #94a3b8; }
      .doclib-master-dropzone { padding: 32px; border: 2px dashed #cbd5e1; border-radius: 4px; text-align: center; color: #64748b; font-size: 14px; background: #fff; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-master");

    const title = document.createElement("div");
    title.classList.add("doclib-master-title");
    title.innerText = this.data.title;

    if (!this.readOnly) {
      title.contentEditable = "true";
      title.addEventListener("input", () => {
        this.data.title = title.innerText;
      });
    }
    container.appendChild(title);

    const dropzone = document.createElement("div");
    dropzone.classList.add("doclib-master-dropzone");
    dropzone.innerText = "Drag and drop Subdocuments here";
    container.appendChild(dropzone);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
