import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTranslation implements BlockTool {
  static readonly feature = {
    id: "DocLibTranslation",
    title: "DocLib Translation",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a541e82be1fd08c1"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="16,18 15,13 8,19 12,10 19,19 9,7"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Translation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a541e82be1fd08c1"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="16,18 15,13 8,19 12,10 19,19 9,7"/></svg>',
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
      original: data?.original || "",
      translated: data?.translated || "",
      langOrig: data?.langOrig || "English",
      langTrans: data?.langTrans || "Vietnamese",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-trans { display: flex; flex-direction: column; gap: 16px; padding: 16px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; margin: 16px 0; font-family: sans-serif; }
      .doclib-trans-row { display: flex; gap: 16px; }
      .doclib-trans-col { flex: 1; display: flex; flex-direction: column; gap: 8px; }
      .doclib-trans-lang { font-size: 12px; font-weight: bold; color: #64748b; text-transform: uppercase; outline: none; }
      .doclib-trans-lang:empty:before { content: "DocLib Lang"; color: #cbd5e1; }
      .doclib-trans-text { background: #fff; border: 1px solid #e2e8f0; border-radius: 4px; padding: 12px; min-height: 80px; font-size: 14px; outline: none; line-height: 1.5; color: #1e293b; }
      .doclib-trans-text:empty:before { content: attr(data-placeholder); color: #94a3b8; font-style: italic; }
      .doclib-trans-arrow { display: flex; align-items: center; justify-content: center; font-size: 24px; color: #94a3b8; padding-top: 24px; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-trans");

    const row = document.createElement("div");
    row.classList.add("doclib-trans-row");

    const col1 = document.createElement("div");
    col1.classList.add("doclib-trans-col");

    const lang1 = document.createElement("div");
    lang1.classList.add("doclib-trans-lang");
    lang1.innerText = this.data.langOrig;

    const text1 = document.createElement("div");
    text1.classList.add("doclib-trans-text");
    text1.innerText = this.data.original;
    text1.dataset.placeholder = "DocLib Original Text";

    if (!this.readOnly) {
      lang1.contentEditable = "true";
      lang1.addEventListener("input", () => {
        this.data.langOrig = lang1.innerText;
      });
      text1.contentEditable = "true";
      text1.addEventListener("input", () => {
        this.data.original = text1.innerText;
      });
    }

    col1.appendChild(lang1);
    col1.appendChild(text1);

    const arrow = document.createElement("div");
    arrow.classList.add("doclib-trans-arrow");
    arrow.innerText = "->";

    const col2 = document.createElement("div");
    col2.classList.add("doclib-trans-col");

    const lang2 = document.createElement("div");
    lang2.classList.add("doclib-trans-lang");
    lang2.innerText = this.data.langTrans;

    const text2 = document.createElement("div");
    text2.classList.add("doclib-trans-text");
    text2.innerText = this.data.translated;
    text2.dataset.placeholder = "DocLib Translated Text";

    if (!this.readOnly) {
      lang2.contentEditable = "true";
      lang2.addEventListener("input", () => {
        this.data.langTrans = lang2.innerText;
      });
      text2.contentEditable = "true";
      text2.addEventListener("input", () => {
        this.data.translated = text2.innerText;
      });
    }

    col2.appendChild(lang2);
    col2.appendChild(text2);

    row.appendChild(col1);
    row.appendChild(arrow);
    row.appendChild(col2);

    container.appendChild(row);
    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
