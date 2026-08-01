import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibThesaurus implements BlockTool {
  static readonly feature = {
    id: "DocLibThesaurus",
    title: "DocLib Thesaurus",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7f2437888e7329ec"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="12,6 8,4 10,17 11,19 13,20 14,17"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Thesaurus",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="7f2437888e7329ec"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="12,6 8,4 10,17 11,19 13,20 14,17"/></svg>',
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
      word: data?.word || "Important",
      synonyms:
        data?.synonyms && data.synonyms.length > 0
          ? data.synonyms
          : ["DocLib Crucial", "DocLib Significant", "DocLib Vital"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-thes { font-family: sans-serif; padding: 16px; border: 1px solid hsl(var(--border)); border-radius: 8px; background: hsl(var(--surface)); margin: 16px 0; max-width: 400px; display: flex; flex-direction: column; gap: 12px; }
      .doclib-thes-head { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 16px; color: hsl(var(--ink)); border-bottom: 1px solid hsl(var(--surface-quiet)); padding-bottom: 8px; }
      .doclib-thes-word { color: hsl(var(--brand)); outline: none; border-bottom: 1px dashed hsl(var(--brand)); }
      .doclib-thes-word:empty:before { content: "DocLib Word"; color: hsl(var(--ink-faint)); }
      .doclib-thes-list { display: flex; flex-wrap: wrap; gap: 8px; }
      .doclib-thes-item { padding: 4px 12px; background: hsl(var(--surface-raised)); border: 1px solid hsl(var(--border)); border-radius: 16px; font-size: 13px; color: hsl(var(--ink-muted)); display: flex; align-items: center; gap: 6px; }
      .doclib-thes-text { outline: none; }
      .doclib-thes-text:empty:before { content: "DocLib Synonym"; color: hsl(var(--border)); }
      .doclib-thes-del { color: hsl(var(--danger)); font-size: 10px; border: none; background: transparent; cursor: pointer; display: none; }
      .doclib-thes-item:hover .doclib-thes-del { display: block; }
      .doclib-thes-add { font-size: 12px; color: hsl(var(--brand)); border: 1px dashed hsl(var(--brand)); background: transparent; border-radius: 16px; padding: 4px 12px; cursor: pointer; }
      .doclib-thes-add:hover { background: hsl(var(--brand-soft)); }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-thes");

    const head = document.createElement("div");
    head.classList.add("doclib-thes-head");
    head.innerHTML = `<span>Thesaurus:</span>`;

    const word = document.createElement("span");
    word.classList.add("doclib-thes-word");
    word.innerText = this.data.word;
    if (!this.readOnly) {
      word.contentEditable = "true";
      word.addEventListener("input", () => {
        this.data.word = word.innerText;
      });
    }
    head.appendChild(word);
    container.appendChild(head);

    const list = document.createElement("div");
    list.classList.add("doclib-thes-list");
    container.appendChild(list);

    const renderList = () => {
      list.innerHTML = "";
      this.data.synonyms.forEach((syn: string, i: number) => {
        const item = document.createElement("div");
        item.classList.add("doclib-thes-item");

        const text = document.createElement("span");
        text.classList.add("doclib-thes-text");
        text.innerText = syn;

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", () => {
            this.data.synonyms[i] = text.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-thes-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data.synonyms.splice(i, 1);
            renderList();
          });
          item.appendChild(text);
          item.appendChild(del);
        } else {
          item.appendChild(text);
        }

        list.appendChild(item);
      });

      if (!this.readOnly) {
        const add = document.createElement("button");
        add.classList.add("doclib-thes-add");
        add.innerText = "+";
        add.addEventListener("click", () => {
          this.data.synonyms.push("DocLib New");
          renderList();
        });
        list.appendChild(add);
      }
    };

    renderList();

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
