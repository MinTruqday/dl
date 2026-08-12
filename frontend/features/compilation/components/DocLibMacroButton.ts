import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibMacroButton implements BlockTool {
  static readonly feature = {
    id: "DocLibMacroButton",
    title: "DocLib MacroButton",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c51a03c21bc817d5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="14,13 7,11 14,17 10,13 19,8 8,4"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Macro Button",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="c51a03c21bc817d5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="14,13 7,11 14,17 10,13 19,8 8,4"/></svg>',
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
      label: data?.label || "Nút DocLib",
      macroId: data?.macroId || "macro_1",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-macro { margin: 24px 0; display: flex; flex-direction: column; align-items: center; gap: 16px; }
      .doclib-macro-btn { padding: 12px 32px; background: hsl(var(--ink)); color: hsl(var(--surface)); border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; text-transform: uppercase; letter-spacing: 0.05em; transition: background 0.2s; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
      .doclib-macro-btn:hover { background: hsl(var(--ink)); }
      .doclib-macro-btn:active { transform: translateY(1px); }
      
      .doclib-macro-edit { display: flex; gap: 8px; background: hsl(var(--surface-raised)); padding: 12px; border: 1px dashed hsl(var(--border)); border-radius: 8px; }
      .doclib-macro-input { padding: 8px; border: 1px solid hsl(var(--border)); border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-macro");

    const btn = document.createElement("button");
    btn.classList.add("doclib-macro-btn");
    btn.innerText = this.data.label;
    btn.addEventListener("click", () => {
      const event = new CustomEvent("doclib:macro", {
        bubbles: true,
        detail: { macroId: this.data.macroId },
      });
      btn.dispatchEvent(event);
    });

    container.appendChild(btn);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-macro-edit");

      const labelInput = document.createElement("input");
      labelInput.classList.add("doclib-macro-input");
      labelInput.placeholder = "Tên nút";
      labelInput.value = this.data.label;
      labelInput.addEventListener("input", () => {
        this.data.label = labelInput.value || "Nút DocLib";
        btn.innerText = this.data.label;
      });

      const idInput = document.createElement("input");
      idInput.classList.add("doclib-macro-input");
      idInput.placeholder = "Mã macro";
      idInput.value = this.data.macroId;
      idInput.addEventListener("input", () => {
        this.data.macroId = idInput.value;
      });

      edit.appendChild(labelInput);
      edit.appendChild(idInput);
      container.appendChild(edit);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      label: this.data.label,
      macroId: this.data.macroId,
    };
  }
}
