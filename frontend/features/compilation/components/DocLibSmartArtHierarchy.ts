import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtHierarchy implements BlockTool {
  static readonly feature = {
    id: "DocLibSmartArtHierarchy",
    title: "Smart Art Hierarchy",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3428308ba490c0c6"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,10 18,7 15,12 9,15 12,12 19,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Smart Art Hierarchy",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3428308ba490c0c6"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="5,10 18,7 15,12 9,15 12,12 19,4"/></svg>',
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
      root: data?.root || "DocLib Title",
      children:
        data?.children && data.children.length > 0
          ? data.children
          : ["DocLib Name", "DocLib Name"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-hier { display: flex; flex-direction: column; align-items: center; margin: 32px 0; font-family: sans-serif; }
      .doclib-hier-root { padding: 16px 32px; background: #2563eb; color: #fff; font-weight: bold; border-radius: 8px; position: relative; outline: none; }
      .doclib-hier-line-v { width: 2px; height: 32px; background: #94a3b8; }
      .doclib-hier-line-h { height: 2px; background: #94a3b8; width: 100%; transition: width 0.3s; }
      .doclib-hier-children-wrap { display: flex; flex-direction: column; align-items: center; width: 100%; }
      .doclib-hier-children { display: flex; justify-content: space-between; width: 100%; position: relative; }
      .doclib-hier-child-col { display: flex; flex-direction: column; align-items: center; flex: 1; }
      .doclib-hier-child-line-v { width: 2px; height: 16px; background: #94a3b8; }
      .doclib-hier-child { padding: 12px 16px; background: #f8fafc; border: 2px solid #2563eb; border-radius: 8px; color: #1e293b; font-weight: 500; outline: none; text-align: center; }
      
      .doclib-hier-edit { display: flex; gap: 8px; margin-top: 24px; background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; flex-wrap: wrap; justify-content: center; width: 100%; }
      .doclib-hier-input { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; flex: 1; min-width: 120px; }
      .doclib-hier-btn { padding: 6px 12px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      .doclib-hier-add { padding: 6px 16px; background: #10b981; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-hier");

    const rootEl = document.createElement("div");
    rootEl.classList.add("doclib-hier-root");
    rootEl.innerText = this.data.root;

    if (!this.readOnly) {
      rootEl.contentEditable = "true";
      rootEl.addEventListener("input", () => {
        this.data.root = rootEl.innerText;
      });
    }

    container.appendChild(rootEl);

    const lineV1 = document.createElement("div");
    lineV1.classList.add("doclib-hier-line-v");
    container.appendChild(lineV1);

    const childrenWrap = document.createElement("div");
    childrenWrap.classList.add("doclib-hier-children-wrap");

    const lineH = document.createElement("div");
    lineH.classList.add("doclib-hier-line-h");

    const childrenCont = document.createElement("div");
    childrenCont.classList.add("doclib-hier-children");

    childrenWrap.appendChild(lineH);
    childrenWrap.appendChild(childrenCont);
    container.appendChild(childrenWrap);

    const renderChildren = () => {
      childrenCont.innerHTML = "";
      const n = this.data.children.length;
      if (n <= 1) {
        lineH.style.width = "0px";
      } else {
        const pct = ((n - 1) / n) * 100;
        lineH.style.width = `${pct}%`;
      }

      this.data.children.forEach((childText: string, i: number) => {
        const col = document.createElement("div");
        col.classList.add("doclib-hier-child-col");

        const lineV2 = document.createElement("div");
        lineV2.classList.add("doclib-hier-child-line-v");

        const childEl = document.createElement("div");
        childEl.classList.add("doclib-hier-child");
        childEl.innerText = childText;

        if (!this.readOnly) {
          childEl.contentEditable = "true";
          childEl.addEventListener("input", () => {
            this.data.children[i] = childEl.innerText;
          });
        }

        col.appendChild(lineV2);
        col.appendChild(childEl);
        childrenCont.appendChild(col);
      });
    };
    renderChildren();

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-hier-edit");

      const renderEdit = () => {
        edit.innerHTML = "";
        this.data.children.forEach((text: string, i: number) => {
          const row = document.createElement("div");
          row.style.display = "flex";
          row.style.gap = "4px";

          const input = document.createElement("input");
          input.classList.add("doclib-hier-input");
          input.value = text;
          input.placeholder = "DocLib Name";
          input.addEventListener("input", () => {
            this.data.children[i] = input.value;
            renderChildren();
          });

          const del = document.createElement("button");
          del.classList.add("doclib-hier-btn");
          del.innerText = "X";
          del.addEventListener("click", () => {
            this.data.children.splice(i, 1);
            renderChildren();
            renderEdit();
          });

          row.appendChild(input);
          row.appendChild(del);
          edit.appendChild(row);
        });

        if (this.data.children.length < 5) {
          const add = document.createElement("button");
          add.classList.add("doclib-hier-add");
          add.innerText = "+";
          add.addEventListener("click", () => {
            this.data.children.push("DocLib Name");
            renderChildren();
            renderEdit();
          });
          edit.appendChild(add);
        }
      };
      renderEdit();
      container.appendChild(edit);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      root: this.data.root,
      children: this.data.children,
    };
  }
}
