import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibThesaurus implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Thesaurus",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path><circle cx="12" cy="10" r="3"></circle><line x1="12" y1="13" x2="12" y2="17"></line></svg>',
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
      .doclib-thes { font-family: sans-serif; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; margin: 16px 0; max-width: 400px; display: flex; flex-direction: column; gap: 12px; }
      .doclib-thes-head { display: flex; align-items: center; gap: 8px; font-weight: bold; font-size: 16px; color: #1e293b; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }
      .doclib-thes-word { color: #3b82f6; outline: none; border-bottom: 1px dashed #3b82f6; }
      .doclib-thes-word:empty:before { content: "DocLib Word"; color: #94a3b8; }
      .doclib-thes-list { display: flex; flex-wrap: wrap; gap: 8px; }
      .doclib-thes-item { padding: 4px 12px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 16px; font-size: 13px; color: #475569; display: flex; align-items: center; gap: 6px; }
      .doclib-thes-text { outline: none; }
      .doclib-thes-text:empty:before { content: "DocLib Synonym"; color: #cbd5e1; }
      .doclib-thes-del { color: #ef4444; font-size: 10px; border: none; background: transparent; cursor: pointer; display: none; }
      .doclib-thes-item:hover .doclib-thes-del { display: block; }
      .doclib-thes-add { font-size: 12px; color: #3b82f6; border: 1px dashed #3b82f6; background: transparent; border-radius: 16px; padding: 4px 12px; cursor: pointer; }
      .doclib-thes-add:hover { background: #eff6ff; }
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
          del.innerText = "✕";
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
