import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCoverPage implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Cover Page",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d=\"M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z\"/><polyline points=\"14 2 14 8 20 8\"/><path d=\"M8 13h8\"/><path d=\"M8 17h8\"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      title: data?.title || "",
      subtitle: data?.subtitle || "",
      author: data?.author || "",
      date: data?.date || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-cover { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 800px; padding: 48px; border: 1px solid #e2e8f0; background: #fff; margin: 32px 0; page-break-after: always; position: relative; }
      .doclib-cover::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 16px; background: #2563eb; }
      .doclib-cover-title { font-size: 48px; font-weight: 800; text-align: center; color: #0f172a; margin-bottom: 24px; outline: none; width: 100%; }
      .doclib-cover-subtitle { font-size: 24px; font-weight: 400; text-align: center; color: #475569; margin-bottom: 64px; outline: none; width: 100%; }
      .doclib-cover-author { font-size: 18px; font-weight: 500; text-align: center; color: #334155; margin-bottom: 8px; outline: none; width: 100%; }
      .doclib-cover-date { font-size: 16px; text-align: center; color: #64748b; outline: none; width: 100%; }
      
      .doclib-cover-input:empty::before { color: #cbd5e1; pointer-events: none; }
      .doclib-cover-title:empty::before { content: "DocLib Title"; }
      .doclib-cover-subtitle:empty::before { content: "DocLib Input"; }
      .doclib-cover-author:empty::before { content: "DocLib Name"; }
      .doclib-cover-date:empty::before { content: "DocLib Input"; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-cover");

    const titleEl = document.createElement("div");
    titleEl.classList.add("doclib-cover-title", "doclib-cover-input");
    titleEl.innerText = this.data.title;

    const subtitleEl = document.createElement("div");
    subtitleEl.classList.add("doclib-cover-subtitle", "doclib-cover-input");
    subtitleEl.innerText = this.data.subtitle;

    const authorEl = document.createElement("div");
    authorEl.classList.add("doclib-cover-author", "doclib-cover-input");
    authorEl.innerText = this.data.author;

    const dateEl = document.createElement("div");
    dateEl.classList.add("doclib-cover-date", "doclib-cover-input");
    dateEl.innerText = this.data.date;

    if (!this.readOnly) {
      titleEl.contentEditable = "true";
      subtitleEl.contentEditable = "true";
      authorEl.contentEditable = "true";
      dateEl.contentEditable = "true";
      
      titleEl.addEventListener("input", () => { this.data.title = titleEl.innerText; });
      subtitleEl.addEventListener("input", () => { this.data.subtitle = subtitleEl.innerText; });
      authorEl.addEventListener("input", () => { this.data.author = authorEl.innerText; });
      dateEl.addEventListener("input", () => { this.data.date = dateEl.innerText; });
    }

    container.appendChild(titleEl);
    container.appendChild(subtitleEl);
    container.appendChild(authorEl);
    container.appendChild(dateEl);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      title: this.data.title,
      subtitle: this.data.subtitle,
      author: this.data.author,
      date: this.data.date,
    };
  }
}
