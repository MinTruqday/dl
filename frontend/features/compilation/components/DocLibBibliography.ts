import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibBibliography implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Bibliography",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
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
      entries: data?.entries || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-bib {
        background: #fff;
        border-top: 2px solid #e2e8f0;
        padding-top: 24px;
        margin: 32px 0;
      }
      .doclib-bib-title {
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 16px;
      }
      .doclib-bib-list {
        padding-left: 24px;
      }
      .doclib-bib-entry {
        font-size: 14px;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 12px;
        padding-left: 24px;
        text-indent: -24px;
      }
      .doclib-bib-edit {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 16px;
        border-radius: 8px;
      }
      .doclib-bib-edit-item {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
      }
      .doclib-bib-input {
        flex: 1;
        padding: 8px;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        font-size: 13px;
        outline: none;
      }
      .doclib-bib-del {
        background: #ef4444;
        color: #fff;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        padding: 0 12px;
      }
      .doclib-bib-add {
        background: #3b82f6;
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        cursor: pointer;
        font-size: 13px;
        margin-top: 8px;
      }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-bib");

    const title = document.createElement("div");
    title.classList.add("doclib-bib-title");
    title.innerText = "Bibliography";
    container.appendChild(title);

    if (this.readOnly) {
      const list = document.createElement("div");
      list.classList.add("doclib-bib-list");
      this.data.entries.forEach((text: string) => {
        const item = document.createElement("div");
        item.classList.add("doclib-bib-entry");
        item.innerHTML = text;
        list.appendChild(item);
      });
      container.appendChild(list);
      this.wrapper.appendChild(container);
      return this.wrapper;
    }

    const edit = document.createElement("div");
    edit.classList.add("doclib-bib-edit");

    const renderEntries = () => {
      edit.innerHTML = "";
      this.data.entries.forEach((text: string, index: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-bib-edit-item");

        const input = document.createElement("input");
        input.classList.add("doclib-bib-input");
        input.value = text;
        input.placeholder = "";
        input.addEventListener("input", () => {
          this.data.entries[index] = input.value;
        });

        const del = document.createElement("button");
        del.classList.add("doclib-bib-del");
        del.innerText = "Delete";
        del.addEventListener("click", () => {
          this.data.entries.splice(index, 1);
          renderEntries();
        });

        row.appendChild(input);
        row.appendChild(del);
        edit.appendChild(row);
      });

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-bib-add");
      addBtn.innerText = "Add Citation";
      addBtn.addEventListener("click", () => {
        this.data.entries.push("");
        renderEntries();
      });
      edit.appendChild(addBtn);
    };

    renderEntries();
    container.appendChild(edit);
    this.wrapper.appendChild(container);

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      entries: this.data.entries.filter((e: string) => e.trim() !== ""),
    };
  }
}
