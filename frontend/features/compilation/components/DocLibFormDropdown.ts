import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormDropdown implements BlockTool {
  static readonly feature = {
    id: "DocLibFormDropdown",
    title: "DocLib FormDropdown",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a5630cc3179ce423"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="16,18 16,12 10,7 11,5 14,17 19,14"/></svg>',
    origin: "doclib-native",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Form Dropdown",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a5630cc3179ce423"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="16,18 16,12 10,7 11,5 14,17 19,14"/></svg>',
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
      label: data?.label || "DocLib Button",
      options:
        data?.options && data.options.length > 0
          ? data.options
          : ["DocLib Text", "DocLib Text"],
      selected: data?.selected || 0,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-form-dd { display: flex; align-items: center; gap: 12px; margin: 16px 0; padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px; background: #fff; }
      .doclib-form-dd-label { font-size: 15px; font-weight: 600; color: #1e293b; outline: none; flex: 1; }
      .doclib-form-dd-label:empty::before { content: "DocLib Title"; color: #94a3b8; pointer-events: none; }
      .doclib-form-dd-select { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; background: #f8fafc; font-size: 14px; min-width: 150px; cursor: pointer; }
      .doclib-form-dd-edit { margin-top: 8px; padding: 12px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; }
      .doclib-form-dd-row { display: flex; gap: 8px; }
      .doclib-form-dd-input { flex: 1; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
      .doclib-form-dd-btn { padding: 6px 12px; background: #ef4444; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      .doclib-form-dd-add { padding: 6px 16px; background: #3b82f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; align-self: flex-start; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-form-dd");

    const label = document.createElement("div");
    label.classList.add("doclib-form-dd-label");
    label.innerText = this.data.label;

    if (!this.readOnly) {
      label.contentEditable = "true";
      label.addEventListener("input", () => {
        this.data.label = label.innerText;
      });
    }

    const select = document.createElement("select");
    select.classList.add("doclib-form-dd-select");

    const renderSelect = () => {
      select.innerHTML = "";
      this.data.options.forEach((optStr: string, idx: number) => {
        const o = document.createElement("option");
        o.value = String(idx);
        o.text = optStr;
        o.selected = this.data.selected === idx;
        select.appendChild(o);
      });
    };
    renderSelect();

    select.addEventListener("change", () => {
      this.data.selected = parseInt(select.value, 10);
    });

    container.appendChild(label);
    container.appendChild(select);
    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-form-dd-edit");

      const renderEdit = () => {
        edit.innerHTML = "";
        this.data.options.forEach((optStr: string, i: number) => {
          const row = document.createElement("div");
          row.classList.add("doclib-form-dd-row");

          const input = document.createElement("input");
          input.classList.add("doclib-form-dd-input");
          input.value = optStr;
          input.placeholder = "DocLib Input";
          input.addEventListener("input", () => {
            this.data.options[i] = input.value;
            renderSelect();
          });

          const del = document.createElement("button");
          del.classList.add("doclib-form-dd-btn");
          del.innerText = "X";
          del.addEventListener("click", () => {
            this.data.options.splice(i, 1);
            if (this.data.selected >= this.data.options.length)
              this.data.selected = Math.max(0, this.data.options.length - 1);
            renderSelect();
            renderEdit();
          });

          row.appendChild(input);
          row.appendChild(del);
          edit.appendChild(row);
        });

        const add = document.createElement("button");
        add.classList.add("doclib-form-dd-add");
        add.innerText = "+";
        add.addEventListener("click", () => {
          this.data.options.push("DocLib Text");
          renderSelect();
          renderEdit();
        });
        edit.appendChild(add);
      };

      renderEdit();
      this.wrapper.appendChild(edit);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      label: this.data.label,
      options: this.data.options.filter((o: string) => o.trim() !== ""),
      selected: this.data.selected,
    };
  }
}
