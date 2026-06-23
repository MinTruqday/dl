import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibBreadcrumb implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Breadcrumb",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      items: data?.items && data.items.length > 0 ? data.items : ["Home", "Category", "Current Page"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-bc { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-family: sans-serif; font-size: 14px; color: #64748b; padding: 12px; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; }
      .doclib-bc-item { display: flex; align-items: center; gap: 8px; }
      .doclib-bc-text { outline: none; cursor: pointer; }
      .doclib-bc-text:hover { color: #3b82f6; text-decoration: underline; }
      .doclib-bc-text:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-bc-item:last-child .doclib-bc-text { font-weight: 600; color: #0f172a; text-decoration: none; cursor: text; }
      .doclib-bc-sep { font-size: 12px; color: #94a3b8; user-select: none; }
      .doclib-bc-item:last-child .doclib-bc-sep { display: none; }
      .doclib-bc-del { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 10px; margin-left: 4px; display: none; }
      .doclib-bc-item:hover .doclib-bc-del { display: inline-block; }
      .doclib-bc-add { margin-left: 8px; padding: 2px 8px; font-size: 12px; border: 1px dashed #cbd5e1; border-radius: 4px; background: #fff; cursor: pointer; color: #64748b; }
      .doclib-bc-add:hover { background: #f1f5f9; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-bc");
    this.wrapper.appendChild(container);

    const renderUI = () => {
      container.innerHTML = "";
      this.data.items.forEach((item: string, i: number) => {
        const itemEl = document.createElement("div");
        itemEl.classList.add("doclib-bc-item");

        const text = document.createElement("div");
        text.classList.add("doclib-bc-text");
        text.innerText = item;
        text.dataset.placeholder = "DocLib Path";

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", () => { this.data.items[i] = text.innerText; });

          const del = document.createElement("button");
          del.classList.add("doclib-bc-del");
          del.innerText = "✕";
          del.addEventListener("click", () => {
            this.data.items.splice(i, 1);
            renderUI();
          });
          
          itemEl.appendChild(text);
          itemEl.appendChild(del);
        } else {
          itemEl.appendChild(text);
        }

        const sep = document.createElement("span");
        sep.classList.add("doclib-bc-sep");
        sep.innerText = "/";
        itemEl.appendChild(sep);

        container.appendChild(itemEl);
      });

      if (!this.readOnly) {
        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-bc-add");
        addBtn.innerText = "+";
        addBtn.addEventListener("click", () => {
          this.data.items.push("");
          renderUI();
        });
        container.appendChild(addBtn);
      }
    };

    renderUI();
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
