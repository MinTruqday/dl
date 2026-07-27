import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCombineDocuments implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Combine Documents",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>',
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
      doc1: data?.doc1 || "",
      doc2: data?.doc2 || "",
      mergedTitle: data?.mergedTitle || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-combine { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 24px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; margin: 16px 0; font-family: sans-serif; }
      .doclib-combine-doc { flex: 1; min-width: 120px; text-align: center; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .doclib-combine-title { font-size: 14px; font-weight: bold; color: #0f172a; margin-bottom: 8px; outline: none; }
      .doclib-combine-title:empty:before { content: attr(data-placeholder); color: #94a3b8; font-weight: normal; }
      .doclib-combine-icon { font-size: 24px; color: #3b82f6; margin-bottom: 8px; }
      .doclib-combine-arrow { font-size: 24px; color: #94a3b8; font-weight: bold; }
      .doclib-combine-merged { flex: 1; min-width: 140px; text-align: center; background: #eff6ff; border: 2px dashed #3b82f6; border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-combine");

    const createDoc = (key: string, icon: string, ph: string) => {
      const doc = document.createElement("div");
      doc.classList.add("doclib-combine-doc");
      doc.innerHTML = `<div class="doclib-combine-icon">${icon}</div>`;

      const title = document.createElement("div");
      title.classList.add("doclib-combine-title");
      title.innerText = this.data[key];
      title.dataset.placeholder = ph;

      if (!this.readOnly) {
        title.contentEditable = "true";
        title.addEventListener("input", () => {
          this.data[key] = title.innerText;
        });
      }
      doc.appendChild(title);
      return doc;
    };

    container.appendChild(createDoc("doc1", "DOC", "DocLib Doc 1"));

    const plus = document.createElement("div");
    plus.classList.add("doclib-combine-arrow");
    plus.innerText = "+";
    container.appendChild(plus);

    container.appendChild(createDoc("doc2", "TEXT", "DocLib Doc 2"));

    const arrow = document.createElement("div");
    arrow.classList.add("doclib-combine-arrow");
    arrow.innerText = "->";
    container.appendChild(arrow);

    const merged = document.createElement("div");
    merged.classList.add("doclib-combine-merged");
    merged.innerHTML = `<div class="doclib-combine-icon">MERGED</div>`;
    const mTitle = document.createElement("div");
    mTitle.classList.add("doclib-combine-title");
    mTitle.innerText = this.data.mergedTitle;
    mTitle.dataset.placeholder = "DocLib Merged Doc";
    if (!this.readOnly) {
      mTitle.contentEditable = "true";
      mTitle.addEventListener("input", () => {
        this.data.mergedTitle = mTitle.innerText;
      });
    }
    merged.appendChild(mTitle);
    container.appendChild(merged);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
