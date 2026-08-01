import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTableOfAuthorities implements BlockTool {
  static readonly feature = {
    id: "DocLibTableOfAuthorities",
    title: "DocLib TableOfAuthorities",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4a1041aa8a7a0c9a"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,20 18,4 6,7 16,5 19,9 5,9"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Table of Authorities",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="4a1041aa8a7a0c9a"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="10,20 18,4 6,7 16,5 19,9 5,9"/></svg>',
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
      cases:
        data?.cases && data.cases.length > 0
          ? data.cases
          : [
              { name: "DocLib Case 1", page: "12" },
              { name: "DocLib Case 2", page: "45" },
            ],
      statutes:
        data?.statutes && data.statutes.length > 0
          ? data.statutes
          : [{ name: "DocLib Statute A", page: "3" }],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-toa { font-family: "Times New Roman", serif; padding: 16px; margin: 16px 0; max-width: 600px; border: 1px solid hsl(var(--border)); border-radius: 8px; background: hsl(var(--surface)); }
      .doclib-toa-head { text-align: center; font-size: 18px; font-weight: bold; text-transform: uppercase; margin-bottom: 16px; color: hsl(var(--ink)); }
      .doclib-toa-section { margin-bottom: 16px; }
      .doclib-toa-stitle { font-size: 16px; font-weight: bold; font-style: italic; color: hsl(var(--ink)); margin-bottom: 8px; border-bottom: 1px solid hsl(var(--border)); }
      .doclib-toa-row { display: flex; align-items: flex-end; margin-bottom: 4px; font-size: 14px; position: relative; }
      .doclib-toa-name { outline: none; background: transparent; }
      .doclib-toa-dots { flex: 1; border-bottom: 1px dotted hsl(var(--ink-faint)); margin: 0 8px; position: relative; top: -4px; }
      .doclib-toa-page { outline: none; background: transparent; min-width: 20px; text-align: right; }
      .doclib-toa-del { position: absolute; right: -24px; color: hsl(var(--danger)); font-size: 10px; border: none; background: transparent; cursor: pointer; display: none; }
      .doclib-toa-row:hover .doclib-toa-del { display: block; }
      .doclib-toa-add { font-family: sans-serif; font-size: 12px; color: hsl(var(--brand)); cursor: pointer; display: inline-block; padding: 4px 8px; background: hsl(var(--surface-raised)); border-radius: 4px; margin-top: 4px; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-toa");

    const head = document.createElement("div");
    head.classList.add("doclib-toa-head");
    head.innerText = "Table of Authorities";
    container.appendChild(head);

    const renderSection = (title: string, listKey: "cases" | "statutes") => {
      const section = document.createElement("div");
      section.classList.add("doclib-toa-section");

      const stitle = document.createElement("div");
      stitle.classList.add("doclib-toa-stitle");
      stitle.innerText = title;
      section.appendChild(stitle);

      this.data[listKey].forEach((item: any, i: number) => {
        const row = document.createElement("div");
        row.classList.add("doclib-toa-row");

        const name = document.createElement("div");
        name.classList.add("doclib-toa-name");
        name.innerText = item.name;

        const dots = document.createElement("div");
        dots.classList.add("doclib-toa-dots");

        const page = document.createElement("div");
        page.classList.add("doclib-toa-page");
        page.innerText = item.page;

        if (!this.readOnly) {
          name.contentEditable = "true";
          name.addEventListener("input", () => {
            this.data[listKey][i].name = name.innerText;
          });
          page.contentEditable = "true";
          page.addEventListener("input", () => {
            this.data[listKey][i].page = page.innerText;
          });

          const del = document.createElement("button");
          del.classList.add("doclib-toa-del");
          del.innerText = "x";
          del.addEventListener("click", () => {
            this.data[listKey].splice(i, 1);
            container.innerHTML = "";
            container.appendChild(head);
            container.appendChild(renderSection("Cases", "cases"));
            container.appendChild(renderSection("Statutes", "statutes"));
          });
          row.appendChild(del);
        }

        row.appendChild(name);
        row.appendChild(dots);
        row.appendChild(page);
        section.appendChild(row);
      });

      if (!this.readOnly) {
        const add = document.createElement("div");
        add.classList.add("doclib-toa-add");
        add.innerText = "+ Add Item";
        add.addEventListener("click", () => {
          this.data[listKey].push({ name: "DocLib New Item", page: "0" });
          container.innerHTML = "";
          container.appendChild(head);
          container.appendChild(renderSection("Cases", "cases"));
          container.appendChild(renderSection("Statutes", "statutes"));
        });
        section.appendChild(add);
      }

      return section;
    };

    container.appendChild(renderSection("Cases", "cases"));
    container.appendChild(renderSection("Statutes", "statutes"));

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
