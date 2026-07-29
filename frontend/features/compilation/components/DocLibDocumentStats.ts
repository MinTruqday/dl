import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDocumentStats implements BlockTool {
  static readonly feature = {
    id: "DocLibDocumentStats",
    title: "DocLib Document Stats",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2747e1666d1a58ff"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,7 8,4 11,13 7,4 16,15 8,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Document Stats",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="2747e1666d1a58ff"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="9,7 8,4 11,13 7,4 16,15 8,4"/></svg>',
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
      pages: data?.pages || 1,
      words: data?.words || 0,
      characters: data?.characters || 0,
      paragraphs: data?.paragraphs || 0,
      lines: data?.lines || 0,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-stats { font-family: sans-serif; padding: 20px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; max-width: 350px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
      .doclib-stats-title { font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
      .doclib-stats-row { display: flex; justify-content: space-between; font-size: 14px; color: #475569; padding: 4px 0; }
      .doclib-stats-val { font-weight: 600; color: #0f172a; outline: none; }
      .doclib-stats-val:empty:before { content: "0"; color: #94a3b8; }
      .doclib-stats-refresh { margin-top: 16px; width: 100%; padding: 8px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; color: #3b82f6; cursor: pointer; font-weight: bold; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-stats");

    const title = document.createElement("div");
    title.classList.add("doclib-stats-title");
    title.innerText = "Word Count";
    container.appendChild(title);

    const createRow = (label: string, key: string) => {
      const row = document.createElement("div");
      row.classList.add("doclib-stats-row");
      const lbl = document.createElement("div");
      lbl.innerText = label;
      const val = document.createElement("div");
      val.classList.add("doclib-stats-val");
      val.innerText = this.data[key];
      if (!this.readOnly) {
        val.contentEditable = "true";
        val.addEventListener("input", () => {
          this.data[key] = Number(val.innerText) || 0;
        });
      }
      row.appendChild(lbl);
      row.appendChild(val);
      return row;
    };

    container.appendChild(createRow("Pages", "pages"));
    container.appendChild(createRow("Words", "words"));
    container.appendChild(createRow("Characters (no spaces)", "characters"));
    container.appendChild(createRow("Paragraphs", "paragraphs"));
    container.appendChild(createRow("Lines", "lines"));

    if (!this.readOnly) {
      const btn = document.createElement("button");
      btn.classList.add("doclib-stats-refresh");
      btn.innerText = "Simulate Refresh Stats";
      btn.addEventListener("click", () => {
        this.data.words = Math.floor(Math.random() * 500) + 100;
        this.data.characters =
          this.data.words * 5 + Math.floor(Math.random() * 100);
        this.data.paragraphs = Math.floor(this.data.words / 50) + 1;
        this.data.lines = this.data.paragraphs * 3;
        this.data.pages = Math.floor(this.data.words / 300) + 1;

        const vals = container.querySelectorAll(".doclib-stats-val");
        vals[0].innerHTML = this.data.pages;
        vals[1].innerHTML = this.data.words;
        vals[2].innerHTML = this.data.characters;
        vals[3].innerHTML = this.data.paragraphs;
        vals[4].innerHTML = this.data.lines;
      });
      container.appendChild(btn);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
