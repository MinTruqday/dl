import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPageBorder implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Page Border",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><rect x="7" y="7" width="10" height="10"/></svg>',
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
      style: data?.style || "solid",
      color: data?.color || "#0f172a",
      width: data?.width || "4px",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-page-border-container { position: relative; margin: 32px 0; min-height: 400px; padding: 32px; display: flex; align-items: center; justify-content: center; background: #fff; }
      .doclib-page-border-inner { position: absolute; top: 16px; left: 16px; right: 16px; bottom: 16px; pointer-events: none; }
      .doclib-page-border-text { font-size: 24px; font-weight: 700; color: #334155; outline: none; text-align: center; z-index: 10; width: 100%; }
      .doclib-page-border-text:empty::before { content: "DocLib Title"; color: #cbd5e1; pointer-events: none; }
      .doclib-page-border-controls { display: flex; gap: 8px; margin-top: 16px; background: #f8fafc; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; }
      .doclib-page-border-input { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-page-border-container");

    const borderInner = document.createElement("div");
    borderInner.classList.add("doclib-page-border-inner");

    const applyBorder = () => {
      borderInner.style.border = `${this.data.width} ${this.data.style} ${this.data.color}`;
    };
    applyBorder();

    const textEl = document.createElement("div");
    textEl.classList.add("doclib-page-border-text");
    textEl.innerText = this.data.text || "";

    if (!this.readOnly) {
      textEl.contentEditable = "true";
      textEl.addEventListener("input", () => {
        this.data.text = textEl.innerText;
      });
    }

    container.appendChild(borderInner);
    container.appendChild(textEl);
    this.wrapper.appendChild(container);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-page-border-controls");

      const styleSelect = document.createElement("select");
      styleSelect.classList.add("doclib-page-border-input");
      ["solid", "dashed", "dotted", "double", "groove", "ridge"].forEach(
        (s) => {
          const opt = document.createElement("option");
          opt.value = s;
          opt.text = s.charAt(0).toUpperCase() + s.slice(1);
          opt.selected = this.data.style === s;
          styleSelect.appendChild(opt);
        },
      );
      styleSelect.addEventListener("change", () => {
        this.data.style = styleSelect.value;
        applyBorder();
      });

      const widthInput = document.createElement("input");
      widthInput.classList.add("doclib-page-border-input");
      widthInput.value = this.data.width;
      widthInput.placeholder = "DocLib Input";
      widthInput.addEventListener("input", () => {
        this.data.width = widthInput.value || "1px";
        applyBorder();
      });

      const colorInput = document.createElement("input");
      colorInput.type = "color";
      colorInput.classList.add("doclib-page-border-input");
      colorInput.value = this.data.color;
      colorInput.addEventListener("input", () => {
        this.data.color = colorInput.value;
        applyBorder();
      });

      controls.appendChild(styleSelect);
      controls.appendChild(widthInput);
      controls.appendChild(colorInput);
      this.wrapper.appendChild(controls);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      style: this.data.style,
      color: this.data.color,
      width: this.data.width,
      text: this.data.text,
    };
  }
}
