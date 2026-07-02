import { BlockTool, API, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPageNumber implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Page Number",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><text x="12" y="14" font-size="8">#</text></svg>',
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
      position: data?.position || "bottom-right",
      format: data?.format || "1, 2, 3",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-pagenum { border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; margin: 16px 0; background: #f8fafc; font-family: monospace; display: flex; justify-content: space-between; align-items: center; }
      .doclib-pagenum-preview { font-weight: bold; color: #475569; font-size: 16px; }
      .doclib-pagenum-controls { display: flex; gap: 8px; }
      .doclib-pagenum-select { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; background: #fff; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-pagenum");

    const preview = document.createElement("div");
    preview.classList.add("doclib-pagenum-preview");

    const updatePreview = () => {
      let sample = "1";
      if (this.data.format === "i, ii, iii") sample = "i";
      else if (this.data.format === "A, B, C") sample = "A";
      else if (this.data.format === "Page X of Y") sample = "Page 1 of 10";

      const pos = this.data.position.replace("-", " ").toUpperCase();
      preview.innerText = `[${pos}] - Format: ${sample}`;
    };
    updatePreview();

    container.appendChild(preview);

    if (!this.readOnly) {
      const controls = document.createElement("div");
      controls.classList.add("doclib-pagenum-controls");

      const posSelect = document.createElement("select");
      posSelect.classList.add("doclib-pagenum-select");
      [
        "bottom-right",
        "bottom-center",
        "bottom-left",
        "top-right",
        "top-center",
        "top-left",
      ].forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p;
        opt.text = p;
        opt.selected = this.data.position === p;
        posSelect.appendChild(opt);
      });
      posSelect.addEventListener("change", () => {
        this.data.position = posSelect.value;
        updatePreview();
      });

      const fmtSelect = document.createElement("select");
      fmtSelect.classList.add("doclib-pagenum-select");
      ["1, 2, 3", "i, ii, iii", "A, B, C", "Page X of Y"].forEach((f) => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.text = f;
        opt.selected = this.data.format === f;
        fmtSelect.appendChild(opt);
      });
      fmtSelect.addEventListener("change", () => {
        this.data.format = fmtSelect.value;
        updatePreview();
      });

      controls.appendChild(posSelect);
      controls.appendChild(fmtSelect);
      container.appendChild(controls);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return {
      position: this.data.position,
      format: this.data.format,
    };
  }
}
