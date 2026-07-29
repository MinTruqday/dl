import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormListBox implements BlockTool {
  static readonly feature = {
    id: "DocLibFormListBox",
    title: "Form List Box",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6838bac9185c1916"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="6,9 20,18 11,11 12,9 11,17 8,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "Form List Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6838bac9185c1916"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="6,9 20,18 11,11 12,9 11,17 8,11"/></svg>',
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
      label: data?.label || "",
      options:
        data?.options && data.options.length > 0
          ? data.options
          : ["DocLib Item 1", "DocLib Item 2", "DocLib Item 3"],
      selected: data?.selected || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-listbox { font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin: 16px 0; max-width: 400px; }
      .doclib-lb-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-lb-label:empty:before { content: "DocLib List Box Title"; color: #94a3b8; font-weight: normal; }
      .doclib-lb-box { border: 1px solid #cbd5e1; border-radius: 4px; background: #fff; max-height: 200px; overflow-y: auto; padding: 4px; }
      .doclib-lb-item { display: flex; align-items: center; padding: 6px 8px; border-radius: 4px; cursor: pointer; user-select: none; position: relative; }
      .doclib-lb-item:hover { background: #f1f5f9; }
      .doclib-lb-item.selected { background: #eff6ff; color: #2563eb; font-weight: bold; }
      .doclib-lb-text { flex: 1; outline: none; font-size: 14px; }
      .doclib-lb-text:empty:before { content: "DocLib Item"; color: #94a3b8; font-weight: normal; }
      .doclib-lb-del { font-size: 10px; color: #ef4444; background: none; border: none; cursor: pointer; display: none; }
      .doclib-lb-item:hover .doclib-lb-del { display: block; }
      .doclib-lb-add { padding: 8px; font-size: 12px; font-weight: bold; color: #3b82f6; cursor: pointer; text-align: center; border-radius: 4px; }
      .doclib-lb-add:hover { background: #eff6ff; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-listbox");

    const label = document.createElement("div");
    label.classList.add("doclib-lb-label");
    label.innerText = this.data.label;
    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
    }
    container.appendChild(label);

    const box = document.createElement("div");
    box.classList.add("doclib-lb-box");
    container.appendChild(box);

    const renderList = () => {
      box.innerHTML = "";
      this.data.options.forEach((opt: string, i: number) => {
        const item = document.createElement("div");
        item.classList.add("doclib-lb-item");
        if (this.data.selected.includes(i)) item.classList.add("selected");

        item.addEventListener("click", () => {
          if (this.data.selected.includes(i)) {
            this.data.selected = this.data.selected.filter(
              (idx: number) => idx !== i,
            );
          } else {
            this.data.selected.push(i);
          }
          renderList();
        });

        const text = document.createElement("div");
        text.classList.add("doclib-lb-text");
        text.innerText = opt;

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", (e) => {
            e.stopPropagation();
            this.data.options[i] = text.innerText;
          });
          text.addEventListener("click", (e) => e.stopPropagation());

          const del = document.createElement("button");
          del.classList.add("doclib-lb-del");
          del.innerText = "x";
          del.addEventListener("click", (e) => {
            e.stopPropagation();
            this.data.options.splice(i, 1);
            this.data.selected = this.data.selected
              .filter((idx: number) => idx !== i)
              .map((idx: number) => (idx > i ? idx - 1 : idx));
            renderList();
          });
          item.appendChild(text);
          item.appendChild(del);
        } else {
          item.appendChild(text);
        }

        box.appendChild(item);
      });

      if (!this.readOnly) {
        const add = document.createElement("div");
        add.classList.add("doclib-lb-add");
        add.innerText = "+ Add Item";
        add.addEventListener("click", () => {
          this.data.options.push("");
          renderList();
        });
        box.appendChild(add);
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
