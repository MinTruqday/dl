import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibIndex implements BlockTool {
  static readonly feature = {
    id: "DocLibIndex",
    title: "DocLib Index",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8737d55798eab3c7"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="20,8 13,6 20,17 13,16 4,15 8,19"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Index",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="8737d55798eab3c7"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="20,8 13,6 20,17 13,16 4,15 8,19"/></svg>',
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
      .doclib-index { margin: 24px 0; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background: #fff; }
      .doclib-index-title { font-size: 18px; font-weight: 700; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 16px; }
      .doclib-index-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
      .doclib-index-item { display: flex; justify-content: space-between; font-size: 14px; border-bottom: 1px dotted #e2e8f0; padding-bottom: 4px; }
      .doclib-index-term { font-weight: 500; color: #1e293b; }
      .doclib-index-page { color: #64748b; }
      .doclib-index-edit { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px dashed #cbd5e1; }
      .doclib-index-row { display: flex; gap: 8px; }
      .doclib-index-input { flex: 1; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
      .doclib-index-page-input { width: 80px; padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
      .doclib-index-btn { padding: 8px 16px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      .doclib-index-add { padding: 8px 16px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; align-self: flex-start; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-index");

    const title = document.createElement("div");
    title.classList.add("doclib-index-title");
    title.innerText = "Index";
    container.appendChild(title);

    const grid = document.createElement("div");
    grid.classList.add("doclib-index-grid");
    container.appendChild(grid);

    const renderGrid = () => {
      grid.innerHTML = "";
      const sorted = [...this.data.entries].sort((a, b) =>
        a.term.localeCompare(b.term),
      );
      sorted.forEach((e: any) => {
        const item = document.createElement("div");
        item.classList.add("doclib-index-item");

        const term = document.createElement("span");
        term.classList.add("doclib-index-term");
        term.innerText = e.term;

        const page = document.createElement("span");
        page.classList.add("doclib-index-page");
        page.innerText = e.page;

        item.appendChild(term);
        item.appendChild(page);
        grid.appendChild(item);
      });
    };

    renderGrid();

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-index-edit");

      const renderEdit = () => {
        edit.innerHTML = "";
        this.data.entries.forEach((e: any, i: number) => {
          const row = document.createElement("div");
          row.classList.add("doclib-index-row");

          const inputTerm = document.createElement("input");
          inputTerm.classList.add("doclib-index-input");
          inputTerm.placeholder = "DocLib Input";
          inputTerm.value = e.term;
          inputTerm.addEventListener("input", () => {
            this.data.entries[i].term = inputTerm.value;
            renderGrid();
          });

          const inputPage = document.createElement("input");
          inputPage.classList.add("doclib-index-page-input");
          inputPage.placeholder = "DocLib Input";
          inputPage.value = e.page;
          inputPage.addEventListener("input", () => {
            this.data.entries[i].page = inputPage.value;
            renderGrid();
          });

          const del = document.createElement("button");
          del.classList.add("doclib-index-btn");
          del.innerText = "X";
          del.addEventListener("click", () => {
            this.data.entries.splice(i, 1);
            renderGrid();
            renderEdit();
          });

          row.appendChild(inputTerm);
          row.appendChild(inputPage);
          row.appendChild(del);
          edit.appendChild(row);
        });

        const add = document.createElement("button");
        add.classList.add("doclib-index-add");
        add.innerText = "+";
        add.addEventListener("click", () => {
          this.data.entries.push({ term: "", page: "" });
          renderGrid();
          renderEdit();
        });
        edit.appendChild(add);
      };

      renderEdit();
      container.appendChild(edit);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      entries: this.data.entries.filter((e: any) => e.term.trim() !== ""),
    };
  }
}
