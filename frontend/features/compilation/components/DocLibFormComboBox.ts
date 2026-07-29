import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormComboBox implements BlockTool {
  static readonly feature = {
    id: "DocLibFormComboBox",
    title: "DocLib Form Combo Box",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="850922ec8ab006e5"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="18,13 4,19 6,10 10,12 8,14 16,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form Combo Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="850922ec8ab006e5"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="18,13 4,19 6,10 10,12 8,14 16,4"/></svg>',
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
          : ["DocLib Option A", "DocLib Option B"],
      value: data?.value || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-combo { font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin: 16px 0; max-width: 400px; }
      .doclib-combo-label { font-size: 14px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-combo-label:empty:before { content: "DocLib Label"; color: #94a3b8; font-weight: normal; }
      .doclib-combo-wrap { position: relative; display: flex; align-items: center; }
      .doclib-combo-input { flex: 1; padding: 8px 32px 8px 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; outline: none; }
      .doclib-combo-input:focus { border-color: #3b82f6; }
      .doclib-combo-toggle { position: absolute; right: 0; top: 0; bottom: 0; width: 32px; background: #f1f5f9; border-left: 1px solid #cbd5e1; border-radius: 0 4px 4px 0; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #475569; }
      .doclib-combo-list { display: none; position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #cbd5e1; border-radius: 4px; margin-top: 4px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); z-index: 10; max-height: 150px; overflow-y: auto; }
      .doclib-combo-list.open { display: block; }
      .doclib-combo-item { padding: 8px 12px; font-size: 14px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
      .doclib-combo-item:hover { background: #f1f5f9; }
      .doclib-combo-item-text { outline: none; flex: 1; }
      .doclib-combo-item-text:empty:before { content: "DocLib Opt"; color: #94a3b8; }
      .doclib-combo-del { color: #ef4444; font-size: 10px; cursor: pointer; display: none; background: none; border: none; }
      .doclib-combo-item:hover .doclib-combo-del { display: block; }
      .doclib-combo-add { padding: 8px; text-align: center; color: #3b82f6; font-size: 12px; cursor: pointer; border-top: 1px solid #f1f5f9; font-weight: bold; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-combo");

    const labelEl = document.createElement("div");
    labelEl.classList.add("doclib-combo-label");
    labelEl.innerText = this.data.label;
    if (!this.readOnly) {
      labelEl.contentEditable = "true";
      labelEl.addEventListener("input", () => {
        this.data.label = labelEl.innerText;
      });
    }
    container.appendChild(labelEl);

    const wrap = document.createElement("div");
    wrap.classList.add("doclib-combo-wrap");

    const input = document.createElement("input");
    input.classList.add("doclib-combo-input");
    input.placeholder = "DocLib Select or Type";
    input.value = this.data.value;
    input.addEventListener("input", () => {
      this.data.value = input.value;
    });
    if (this.readOnly) input.disabled = true;

    const toggle = document.createElement("div");
    toggle.classList.add("doclib-combo-toggle");
    toggle.innerHTML = "v";

    const list = document.createElement("div");
    list.classList.add("doclib-combo-list");

    const renderList = () => {
      list.innerHTML = "";
      this.data.options.forEach((opt: string, i: number) => {
        const item = document.createElement("div");
        item.classList.add("doclib-combo-item");

        const text = document.createElement("div");
        text.classList.add("doclib-combo-item-text");
        text.innerText = opt;

        if (!this.readOnly) {
          text.contentEditable = "true";
          text.addEventListener("input", (e) => {
            e.stopPropagation();
            this.data.options[i] = text.innerText;
          });
          text.addEventListener("click", (e) => e.stopPropagation());

          const del = document.createElement("button");
          del.classList.add("doclib-combo-del");
          del.innerText = "x";
          del.addEventListener("click", (e) => {
            e.stopPropagation();
            this.data.options.splice(i, 1);
            renderList();
          });
          item.appendChild(text);
          item.appendChild(del);
        } else {
          item.appendChild(text);
        }

        item.addEventListener("click", () => {
          input.value = this.data.options[i];
          this.data.value = input.value;
          list.classList.remove("open");
        });

        list.appendChild(item);
      });

      if (!this.readOnly) {
        const add = document.createElement("div");
        add.classList.add("doclib-combo-add");
        add.innerText = "+ Add Option";
        add.addEventListener("click", (e) => {
          e.stopPropagation();
          this.data.options.push("");
          renderList();
        });
        list.appendChild(add);
      }
    };

    renderList();

    if (!this.readOnly) {
      toggle.addEventListener("click", () => {
        list.classList.toggle("open");
      });
      document.addEventListener("click", (e) => {
        if (!wrap.contains(e.target as Node)) list.classList.remove("open");
      });
    }

    wrap.appendChild(input);
    wrap.appendChild(toggle);
    wrap.appendChild(list);
    container.appendChild(wrap);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
