import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTable implements BlockTool {
  static readonly feature = {
    id: "DocLibTable",
    title: "Bảng",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="eab225f6131a7830"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="17,12 7,12 6,13 5,18 19,8 6,6"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { content: string[][] };
  private wrapper: HTMLElement | null = null;
  private tbody: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "Bảng",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="eab225f6131a7830"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="17,12 7,12 6,13 5,18 19,8 6,6"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      content:
        data?.content && data?.content.length > 0
          ? data?.content
          : [
              ["", ""],
              ["", ""],
            ],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-table-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-table-styles";
      style.innerHTML = `
        .doclib-table-wrapper { width: 100%; margin: 16px 0; overflow-x: auto; }
        .doclib-table { width: 100%; border-collapse: collapse; border: 1px solid hsl(var(--border)); }
        .doclib-table td { border: 1px solid hsl(var(--border)); padding: 8px 12px; min-width: 100px; outline: none; }
        .doclib-table td:empty::before { content: ''; color: hsl(var(--border)); }
        .doclib-table-controls { display: flex; gap: 8px; margin-top: 8px; justify-content: flex-end; }
        .doclib-table-btn { padding: 4px 8px; font-size: 12px; background: hsl(var(--surface-raised)); border: 1px solid hsl(var(--border)); border-radius: 4px; cursor: pointer; color: hsl(var(--ink-muted)); }
        .doclib-table-btn:hover { background: hsl(var(--border)); }
      `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-table-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const table = document.createElement("table");
    table.classList.add("doclib-table");
    this.tbody = document.createElement("tbody");

    this.data?.content.forEach((rowData) => {
      const tr = document.createElement("tr");
      rowData.forEach((cellData) => {
        const td = document.createElement("td");
        td.contentEditable = "true";
        td.innerHTML = cellData;
        td.addEventListener("input", () => this.saveData());
        tr.appendChild(td);
      });
      this.tbody!.appendChild(tr);
    });

    table.appendChild(this.tbody);
    this.wrapper.appendChild(table);

    const controls = document.createElement("div");
    controls.classList.add("doclib-table-controls");

    const addRowBtn = document.createElement("button");
    addRowBtn.classList.add("doclib-table-btn");
    addRowBtn.innerText = "Thêm hàng";
    addRowBtn.addEventListener("click", () => {
      const cols = this.data?.content[0]?.length || 2;
      this.data?.content.push(Array(cols).fill(""));
      this.buildUI();
    });

    const addColBtn = document.createElement("button");
    addColBtn.classList.add("doclib-table-btn");
    addColBtn.innerText = "Thêm cột";
    addColBtn.addEventListener("click", () => {
      this.data?.content.forEach((row) => row.push(""));
      this.buildUI();
    });

    const rmRowBtn = document.createElement("button");
    rmRowBtn.classList.add("doclib-table-btn");
    rmRowBtn.innerText = "Xóa hàng";
    rmRowBtn.addEventListener("click", () => {
      if (this.data?.content.length > 1) {
        this.data?.content.pop();
        this.buildUI();
      }
    });

    const rmColBtn = document.createElement("button");
    rmColBtn.classList.add("doclib-table-btn");
    rmColBtn.innerText = "Xóa cột";
    rmColBtn.addEventListener("click", () => {
      if (this.data?.content[0]?.length > 1) {
        this.data?.content.forEach((row) => row.pop());
        this.buildUI();
      }
    });

    controls.appendChild(addRowBtn);
    controls.appendChild(addColBtn);
    controls.appendChild(rmRowBtn);
    controls.appendChild(rmColBtn);
    this.wrapper.appendChild(controls);
  }

  private saveData() {
    if (!this.tbody) return;
    const rows = Array.from(this.tbody.querySelectorAll("tr"));
    this.data.content = rows.map((tr) => {
      return Array.from(tr.querySelectorAll("td")).map((td) => td.innerHTML);
    });
  }

  save() {
    this.saveData();
    return this.data;
  }
}
