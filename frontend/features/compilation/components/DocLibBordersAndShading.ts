import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibBordersAndShading implements BlockTool {
  static readonly feature = {
    id: "DocLibBordersAndShading",
    title: "DocLib BordersAndShading",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="76a2043d59b30828"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,13 8,14 8,13 12,10 17,6 4,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Borders & Shading",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="76a2043d59b30828"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="20,13 8,14 8,13 12,10 17,6 4,11"/></svg>',
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
      text: data?.text || "",
      borderWidth: data?.borderWidth || "2px",
      borderStyle: data?.borderStyle || "solid",
      borderColor: data?.borderColor || "hsl(var(--brand))",
      bgColor: data?.bgColor || "hsl(var(--brand-soft))",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-bns { padding: 16px; margin: 16px 0; border-radius: 4px; font-size: 16px; line-height: 1.6; color: hsl(var(--ink)); outline: none; transition: all 0.2s; }
      .doclib-bns:empty::before { content: "DocLib Text"; color: hsl(var(--ink-faint)); pointer-events: none; }
      .doclib-bns-controls { display: flex; gap: 8px; margin-top: 12px; background: hsl(var(--surface-raised)); padding: 12px; border: 1px solid hsl(var(--border)); border-radius: 8px; flex-wrap: wrap; }
      .doclib-bns-input { padding: 6px; border: 1px solid hsl(var(--border)); border-radius: 4px; outline: none; font-size: 14px; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-bns");
    container.innerText = this.data.text;

    const applyStyles = () => {
      container.style.border = `${this.data.borderWidth} ${this.data.borderStyle} ${this.data.borderColor}`;
      container.style.backgroundColor = this.data.bgColor;
    };
    applyStyles();

    if (!this.readOnly) {
      container.contentEditable = "true";
      container.addEventListener("input", () => {
        this.data.text = container.innerText;
      });

      const controls = document.createElement("div");
      controls.classList.add("doclib-bns-controls");

      const widthInput = document.createElement("input");
      widthInput.classList.add("doclib-bns-input");
      widthInput.value = this.data.borderWidth;
      widthInput.placeholder = "DocLib Input";
      widthInput.addEventListener("input", () => {
        this.data.borderWidth = widthInput.value || "0px";
        applyStyles();
      });

      const styleSelect = document.createElement("select");
      styleSelect.classList.add("doclib-bns-input");
      ["solid", "dashed", "dotted", "double"].forEach((s) => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.text = s.charAt(0).toUpperCase() + s.slice(1);
        opt.selected = this.data.borderStyle === s;
        styleSelect.appendChild(opt);
      });
      styleSelect.addEventListener("change", () => {
        this.data.borderStyle = styleSelect.value;
        applyStyles();
      });

      const borderColorInput = document.createElement("input");
      borderColorInput.type = "color";
      borderColorInput.classList.add("doclib-bns-input");
      borderColorInput.value = this.data.borderColor;
      borderColorInput.title = "Border Color";
      borderColorInput.addEventListener("input", () => {
        this.data.borderColor = borderColorInput.value;
        applyStyles();
      });

      const bgColorInput = document.createElement("input");
      bgColorInput.type = "color";
      bgColorInput.classList.add("doclib-bns-input");
      bgColorInput.value = this.data.bgColor;
      bgColorInput.title = "Background Color";
      bgColorInput.addEventListener("input", () => {
        this.data.bgColor = bgColorInput.value;
        applyStyles();
      });

      controls.appendChild(widthInput);
      controls.appendChild(styleSelect);
      controls.appendChild(borderColorInput);
      controls.appendChild(bgColorInput);

      this.wrapper.appendChild(container);
      this.wrapper.appendChild(controls);
    } else {
      this.wrapper.appendChild(container);
    }

    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      text: this.data.text,
      borderWidth: this.data.borderWidth,
      borderStyle: this.data.borderStyle,
      borderColor: this.data.borderColor,
      bgColor: this.data.bgColor,
    };
  }
}
