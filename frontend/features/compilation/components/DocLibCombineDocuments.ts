import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibCombineDocuments implements BlockTool {
  static readonly feature = {
    id: "DocLibCombineDocuments",
    title: "DocLib CombineDocuments",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4e5c73fb414ae782"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,11 17,17 18,10 14,15 12,13 19,15"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Combine Documents",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4e5c73fb414ae782"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="14,11 17,17 18,10 14,15 12,13 19,15"/></svg>',
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
      .doclib-combine { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 24px; border: 1px solid hsl(var(--border)); border-radius: 8px; background: hsl(var(--surface-raised)); margin: 16px 0; font-family: sans-serif; }
      .doclib-combine-doc { flex: 1; min-width: 120px; text-align: center; background: hsl(var(--surface)); border: 1px solid hsl(var(--border)); border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .doclib-combine-title { font-size: 14px; font-weight: bold; color: hsl(var(--ink)); margin-bottom: 8px; outline: none; }
      .doclib-combine-title:empty:before { content: attr(data-placeholder); color: hsl(var(--ink-faint)); font-weight: normal; }
      .doclib-combine-icon { font-size: 24px; color: hsl(var(--brand)); margin-bottom: 8px; }
      .doclib-combine-arrow { font-size: 24px; color: hsl(var(--ink-faint)); font-weight: bold; }
      .doclib-combine-merged { flex: 1; min-width: 140px; text-align: center; background: hsl(var(--brand-soft)); border: 2px dashed hsl(var(--brand)); border-radius: 8px; padding: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
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
